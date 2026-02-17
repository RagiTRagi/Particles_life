import numpy as np
from numba import njit, prange

def quadrantisieren(pos, velocities, types, world_width, world_height, r_max):

    cols = int(world_width / r_max)  # Anzahl der Spalten berechnen
    rows = int(world_height / r_max) # Anzahl der Reihen berechnen

    cols = max(1, cols) # Fallback damit es mindestens eine Spalte gibt
    rows = max(1, rows) # Fallback damit es mindestens eine Reihe gibt

    grid_x = (pos[:, 0] / r_max).astype(int) # Umgerechnete X Positon
    grid_y = (pos[:, 1] / r_max).astype(int) # Umgerechnete Y Position

    # Sicherheitshalber Indices auf [0, max] begrenzen
    grid_x = np.clip(grid_x, 0, cols - 1)
    grid_y = np.clip(grid_y, 0, rows - 1)

    cell_ids = grid_x + (grid_y * cols) # 2D Zellen ID in 1D Zellen ID 

    sort_indices = np.argsort(cell_ids) # Sortieren Reihenfolge der 1D Werte berrechnen

    # Sortieren nach der bestimmten Reihenfolge
    sorted_pos = pos[sort_indices] 
    sorted_vel = velocities[sort_indices]
    sorted_types = types[sort_indices]
    sorted_cell_ids = cell_ids[sort_indices]

    total_cells = cols * rows # Max Zellen berechnen

    # Leere Arrays für Inhaltsverzeichnis
    cell_starts = np.zeros(total_cells, dtype=int)
    cell_counts = np.zeros(total_cells, dtype=int)

    # Ermitteln in welchen Zellen welche sind und speichern von wo bis wo die ID geht 
    unique_ids, unique_starts, unique_counts = np.unique(
        sorted_cell_ids, return_index=True, return_counts=True
    )

    # Leere Arrays mit den gefundenen Werten füllen
    cell_starts[unique_ids] = unique_starts
    cell_counts[unique_ids] = unique_counts

    return sorted_pos, sorted_vel, sorted_types, cell_starts, cell_counts, cols, rows

def update_particles(pos, vel, types, world_width, world_height, r_max, dt, friction, noise_strength, matrix):
    
    # Grid berechnen
    sorted_pos, sorted_vel, sorted_types, cell_starts, cell_counts, cols, rows = quadrantisieren(pos, vel, types, world_width, world_height, r_max)

    # Kräfte berechnen
    forces = calculate_forces(sorted_pos, sorted_types, cell_starts, cell_counts, cols, rows, matrix, r_max, world_width, world_height)

    noise = np.random.normal(0.0, noise_strength, size=sorted_vel.shape)

    # Neue Velocity berechnen
    sorted_vel += forces * dt
    sorted_vel += noise
    sorted_vel *= friction

    # Position updaten
    sorted_pos += sorted_vel * dt

    # Ausgabe von Position, Geschwindigkeit und Typ
    return sorted_pos, sorted_vel, sorted_types
@njit
def wrap_coordinate(value, max_value):
    """
    Torus-world: If val goes beyond max_val,
    it wraps around to the beginning.
    """
    return value % max_value

@njit(parallel=True, fastmath=True, cache=True)
def calculate_forces(sorted_pos, sorted_types, 
    cell_starts, cell_counts, 
    cols, rows, 
    interaction_matrix, r_max, 
    world_width, world_height
):
    """
    Calculates the forces on each particle based on its neighbors in the grid.
    Uses "Cell List" approach for efficient neighbor search.
    """

    total_forces = np.zeros((len(sorted_pos), 2), dtype=np.float32) # Array for the total forces in X and Y direction
    total_cells = cols * rows

    inv_r_max = np.float32(1.0 / r_max)

    beta = np.float32(0.3)
    inv_beta = np.float32(1.0 / beta)
    inv_one_minus_beta = np.float32(1.0 / (1.0 - beta))
    
    repulsion_strength = np.float32(2.0)#                          
    # Tresholf for near interaction
    repulsion_threshold = np.float32(0.3)

    w_width = np.float32(world_width)
    w_height = np.float32(world_height)
    half_w = w_width * 0.5
    half_h = w_height * 0.5
    r_max_sq = r_max * r_max

    # Parallel computing
    # prange for parallel calculation of forces in each cell
    for cell_id in prange(total_cells):

        # Check if the cell has particles
        count_in_my_cell = cell_counts[cell_id]
        if count_in_my_cell == 0:
            continue

        start_i = cell_starts[cell_id]
        
        # Calculate cell coordinates of the grid
        cell_x = cell_id % cols
        cell_y = cell_id // cols

        # Loop through neighboring cells
        for dy in range(-1, 2):
            for dx in range(-1, 2): 
                
                # Coordinates of the neighboring cell with wrap-around for torus-world
                neighbor_x = wrap_coordinate(cell_x + dx, cols)
                neighbor_y = wrap_coordinate(cell_y + dy, rows)
                neighbor_id = neighbor_x + neighbor_y * cols

                # Check if the neighboring cell has particles
                count_in_neighbor_cell = cell_counts[neighbor_id]
                if count_in_neighbor_cell == 0:
                    continue

                start_index_neighbor = cell_starts[neighbor_id]

                # Calculate interactions between particles in cell_id (a) and neighbor_id (b)
                # Every particle in cell_id (a) ...
                for i_local in range(count_in_my_cell):
                    idx_a = start_i + i_local
                    pos_a = sorted_pos[idx_a]
                    type_a = sorted_types[idx_a]
                    
                    # Local force accumulator for particle a
                    force_x_acc = np.float32(0.0)
                    force_y_acc = np.float32(0.0)
                    
                    # ... interacts with every particle in neighbor_id (b)
                    for j_local in range(count_in_neighbor_cell):
                        idx_b = start_index_neighbor + j_local
                        
                        # Skip self-interaction
                        if idx_a == idx_b:
                            continue
                            
                        pos_b = sorted_pos[idx_b]
                        type_b = sorted_types[idx_b]
                        
                        # Vector from a to b
                        rel_x = pos_b[0] - pos_a[0]
                        rel_y = pos_b[1] - pos_a[1]
                        
                        # For torus-world: Shortest distance considering wrap-around
                        if rel_x > half_w: 
                            rel_x -= w_width
                        elif rel_x < -half_w: 
                            rel_x += w_width
                        if rel_y > half_h: 
                            rel_y -= w_height
                        elif rel_y < -half_h: 
                            rel_y += w_height
                        
                        dist_sq = rel_x*rel_x + rel_y*rel_y
                        
                        # Only consider neighbors within r_max
                        if dist_sq > 0 and dist_sq < r_max_sq:
                            dist = np.sqrt(dist_sq)
                            normalized_dist = dist * inv_r_max
                            
                            # Physiks Forula by Lennard-Jones potential inspired:
                            force_factor = np.float32(0.0)

                            if normalized_dist < repulsion_threshold:
                                # To close: Strong repulsion (to prevent overlap)
                                # Prevents particle to clump (idea from pauli principle)
                                force_factor = (normalized_dist * inv_beta - 1.0) * repulsion_strength
                                
                            else:
                                # FAR RANGE: Matrix Interaction
                                # We scale the range [repulsion_threshold ... 1.0] to [0 ... 1]
                                # to apply the matrix force
                                matrix_val = interaction_matrix[type_a, type_b]
                                
                                # Scale the matrix interaction by how close we are to the repulsion threshold
                                pct = (normalized_dist - repulsion_threshold) * inv_one_minus_beta
                                
                                # "Bump" in the curve for close interactions, 
                                # so that the matrix has more influence when particles are closer (but not too close)
                                shape = (1.0 - abs(2.0 * pct - 1.0))
                                force_factor = matrix_val * shape

                            # Addition of the force contribution from particle b to particle a
                            force_x_acc += (rel_x / dist) * force_factor
                            force_y_acc += (rel_y / dist) * force_factor

                    # Sum up all Forces of A
                    total_forces[idx_a, 0] += force_x_acc
                    total_forces[idx_a, 1] += force_y_acc

    return total_forces
class Game:
    def __init__(self, n=2000, world_width=50.0, world_height=50.0, r_max=10.0):
        self.w = world_width
        self.h = world_height
        self.r_max = r_max
        self.pos, self.vel, self.types = self.init_particles(n, self.w, self.h)
        self.friction = 0.95 # Etwas weniger Reibung für mehr Bewegung
        self.noise_strength = 0.1 # Kleineres Rauschen

        # Angepasste Matrix (Normale Werte)
        self.matrix = np.array([
            [ 0, 0,  0, 0],  # blau
            [ 0, 0,  0, 0],  # gelb
            [ 0, 0,  0, 0],  # grün
            [ 0, 0,  0, 0],  # rot
        ], dtype=np.float32)

    def step(self, dt=0.01): # dt kleiner für Stabilität
        self.pos, self.vel, self.types = update_particles(
            self.pos, self.vel, self.types, self.w, self.h, self.r_max, dt, 
            self.friction, self.noise_strength, self.matrix
        )
        
        # Wrap Around (Torus-Welt)
        self.pos[:, 0] = np.mod(self.pos[:, 0], self.w)
        self.pos[:, 1] = np.mod(self.pos[:, 1], self.h)
        
        return {"pos": self.pos, "types": self.types}

    def init_particles(self, n, width, height):
        pos = np.random.rand(n, 2).astype(np.float32) * np.array([width, height], dtype=np.float32)
        vel = np.zeros((n, 2), dtype=np.float32)
        types = np.random.randint(0, 4, size=n, dtype=int)

        return pos, vel, types

    def set_force(self, row: int, col: int, force: float) -> None:
        self.matrix[row, col] = np.float32(force)