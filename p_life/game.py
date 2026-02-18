import numpy as np
from numba import njit, prange

def quadrantisieren(pos, velocities, types, world_width, world_height, r_max):

    """
    Divides the world into a grid of cells for efficient neighbor search.
    
    This function partitions the simulation space into a regular grid where each cell
    has dimensions approximately r_max x r_max. Particles are then sorted by their
    cell assignment, which enables fast lookup of nearby particles during force
    calculations.
    
    Arguments:
        pos (np.ndarray): Particle positions, shape (N, 2) with [x, y] coordinates
        velocities (np.ndarray): Particle velocities, shape (N, 2)
        types (np.ndarray): Particle type indices, shape (N,)
        world_width (float): Width of the simulation world
        world_height (float): Height of the simulation world
        r_max (float): Maximum interaction radius (defines cell size)
    
    Returns:
        tuple: Contains the following elements:
            - sorted_pos (np.ndarray): Positions sorted by cell ID
            - sorted_vel (np.ndarray): Velocities sorted by cell ID
            - sorted_types (np.ndarray): Types sorted by cell ID
            - cell_starts (np.ndarray): Start index of each cell in sorted arrays
            - cell_counts (np.ndarray): Number of particles in each cell
            - cols (int): Number of grid columns
            - rows (int): Number of grid rows
    """

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

    """
    Performs one simulation step by updating particle positions and velocities.
    
    This is the main simulation loop function. It partitions the world into a grid,
    calculates forces between nearby particles, applies friction and noise, and
    updates velocities and positions accordingly.
    
    Arguments:
        pos (np.ndarray): Current particle positions, shape (N, 2)
        vel (np.ndarray): Current particle velocities, shape (N, 2)
        types (np.ndarray): Particle type indices, shape (N,)
        world_width (float): Width of the simulation world
        world_height (float): Height of the simulation world
        r_max (float): Maximum interaction radius
        dt (float): Time step for numerical integration
        friction (float): Friction coefficient (0-1), reduces velocity each step
        noise_strength (float): Standard deviation of random noise added to velocity
        matrix (np.ndarray): Interaction matrix defining forces between particle types
    
    Returns:
        tuple: Updated (positions, velocities, types) after one simulation step
    """
    
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

    Arguments: 
        value (float): Coordinate value to wrap
        max_value (float): Maximum boundary value

    Returns: 
        float: Wrapped coordinate value in range [0, max_value)
    """
    return value % max_value

@njit(parallel=True, fastmath=True)
def calculate_forces(sorted_pos, sorted_types, 
    cell_starts, cell_counts, 
    cols, rows, 
    interaction_matrix, r_max, 
    world_width, world_height
):
    
    """
    Calculates the forces on each particle based on its neighbors in the grid.
    Uses "Cell List" approach for efficient neighbor search.
    
    Args:
        sorted_pos (np.ndarray): Particle positions sorted by cell ID, shape (N, 2)
        sorted_types (np.ndarray): Particle types sorted by cell ID, shape (N,)
        cell_starts (np.ndarray): Start index of each cell in sorted arrays
        cell_counts (np.ndarray): Number of particles in each cell
        cols (int): Number of grid columns
        rows (int): Number of grid rows
        interaction_matrix (np.ndarray): Matrix defining forces between particle types
        r_max (float): Maximum interaction radius
        world_width (float): Width of the simulation world
        world_height (float): Height of the simulation world
    
    Returns:
        np.ndarray: Array of force vectors, shape (N, 2), with [fx, fy] for each particle
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

    """
    Main simulation class for the Particle Life system.
    
    Manages the particle simulation, including initialization of particles,
    their positions, velocities, types, and the interaction matrix that defines
    how different particle types attract or repel each other.
    
    Attributes:
        w (float): World width
        h (float): World height
        r_max (float): Maximum interaction radius between particles
        pos (np.ndarray): Current particle positions, shape (N, 2)
        vel (np.ndarray): Current particle velocities, shape (N, 2)
        types (np.ndarray): Particle type indices, shape (N,)
        friction (float): Friction coefficient applied to velocities each step
        noise_strength (float): Standard deviation of random noise added each step
        matrix (np.ndarray): 4x4 interaction matrix defining forces between particle types
    """

    def __init__(self, n=2000, world_width=100.0, world_height=100.0, r_max=5.0):

        """
        Initializes a new Particle Life simulation.
        
        Args:
            n (int): Number of particles to create. Default is 2000.
            world_width (float): Width of the simulation world. Default is 100.0.
            world_height (float): Height of the simulation world. Default is 100.0.
            r_max (float): Maximum interaction radius. Particles beyond this distance
                          don't interact. Default is 5.0.
        """

        self.w = world_width
        self.h = world_height
        self.r_max = r_max
        self.pos, self.vel, self.types = self.init_particles(n, self.w, self.h)
        self.friction = 0.95 # Etwas weniger Reibung für mehr Bewegung
        self.noise_strength = 0.1 # Kleineres Rauschen

        # Angepasste Matrix (Normale Werte)
        self.matrix = np.array([
            [ 2, -0.8,  0.6, -0.2],  # blau
            [ 0.6,  2, -0.8, -0.2],  # gelb
            [-0.8,  0.6,  2, -0.2],  # grün
            [-0.2, -0.2, -0.2,  2],  # rot
        ], dtype=np.float32)

    def step(self, dt=0.01): # dt kleiner für Stabilität

        """
        Advances the simulation by one time step.
        
        Updates particle positions and velocities based on inter-particle forces,
        friction, and random noise. Also applies torus-world wrapping so particles
        that move beyond world boundaries reappear on the opposite side.
        
        Args:
            dt (float): Time step size for numerical integration. Default is 0.01.
                       Smaller values increase stability but require more computation.
        
        Returns:
            dict: Snapshot of current simulation state with keys:
                - "pos": Current particle positions (np.ndarray)
                - "types": Current particle types (np.ndarray)
        """

        self.pos, self.vel, self.types = update_particles(
            self.pos, self.vel, self.types, self.w, self.h, self.r_max, dt, 
            self.friction, self.noise_strength, self.matrix
        )
        
        # Wrap Around (Torus-Welt)
        self.pos[:, 0] = np.mod(self.pos[:, 0], self.w)
        self.pos[:, 1] = np.mod(self.pos[:, 1], self.h)
        
        return {"pos": self.pos, "types": self.types}

    def init_particles(self, n, width, height):

        """
        Initializes particle positions, velocities, and types.
        
        Particles are randomly distributed across the world with zero initial velocity.
        Each particle is randomly assigned one of four types (0-3).
        
        Args:
            n (int): Number of particles to create
            width (float): Width of the world for position initialization
            height (float): Height of the world for position initialization
        
        Returns:
            tuple: Contains (positions, velocities, types) where:
                - positions: np.ndarray of shape (n, 2) with random x, y coordinates
                - velocities: np.ndarray of shape (n, 2), initialized to zeros
                - types: np.ndarray of shape (n,) with random integers 0-3
        """

        pos = np.random.rand(n, 2) * np.array([width, height], dtype=np.float32)
        vel = np.zeros((n, 2), dtype=np.float32)
        types = np.random.randint(0, 4, size=n, dtype=int)

        return pos, vel, types