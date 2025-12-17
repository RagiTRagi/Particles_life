import numpy as np
import numba

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

def update_particles(pos, vel, types, world_width, world_height, r_max, dt, friction, noise, matrix):
    
    # Grid berechnen
    sorted_pos, sorted_vel, sorted_types, cell_starts, cell_counts, cols, rows = quadrantisieren(pos, vel, types, world_width, world_height, r_max)

    # Kräfte berechnen
    forces = calculate_forces(sorted_pos, sorted_vel, sorted_types, cell_starts, cell_counts, cols, rows, matrix, noise, r_max)

    # Neue Velocity berechnen
    sorted_vel += forces * dt
    sorted_vel *= friction

    # Position updaten
    sorted_pos += sorted_vel * dt

    # Ausgabe von Position, Geschwindigkeit und Typ
    return sorted_pos, sorted_vel, sorted_types
# für die Matrix Conversion
letter_index = {"rot":0, "grün":1, "blau":2, "gelb":3}

def calculate_forces(sorted_pos, sorted_vel, sorted_types, cell_starts, cell_counts, cols, rows, interaction_matrix, noise_param, r_max):

    # Grids filtern, die mind. 1 Partikel beinhalten & Initialisierung von array, welches die Gesamtkräfte jedes Partikels beinhaltet
    filled_grids = np.where(cell_counts > 0)[0]
    total_forces = np.zeros_like(sorted_pos, dtype=float)
    
    # Iteration durch jedes befüllte target cell_grid und Berechnung der Nachbarn(oben/unten/links/rechts)
    for cell_id in filled_grids:
        n_ids = [cell_id]
        x = cell_id % cols
        y = cell_id // cols

        if x < cols - 1:
            right_n = cell_id + 1
            n_ids.append(right_n)
        if x > 0:
            left_n = cell_id - 1
            n_ids.append(left_n)
        if y > 0:
            upper_n = cell_id - cols
            n_ids.append(upper_n)
        if y < rows - 1:
            lower_n = cell_id + cols
            n_ids.append(lower_n)
        
        # Indexe der Partikel im target Grid 
        s0 = cell_starts[cell_id]
        c0 = cell_counts[cell_id]
        target_particles = range(s0, s0+c0)
        
        # Iteration über jedes Partikel in dem target grid
        for target_idx in target_particles:

            gesamtkraft = noise_param # additive Zufallsbewegung, wie bei Brown'sche Molekularbewegungen -> noise muss demnach ein Vektor sein
            position_i = sorted_pos[target_idx]
            ptype_i = sorted_types[target_idx]
            #velocity_i = sorted_vel[target_idx]

            # Iteration über jedes Nachbar-Grid
            for n_id in n_ids:
                # Indexe der Partikel des Nachbar-Grids
                s = cell_starts[n_id]
                c = cell_counts[n_id]
                source_particles = range(s, s+c)

                # Iteration über Partikel des Nachbar-Grids
                for source_idx in source_particles:
                    if target_idx == source_idx:
                        continue

                    position_j = sorted_pos[source_idx]
                    ptype_j = sorted_types[source_idx]
                    #velocity_j = sorted_vel[source_idx]

                    # Interaktionswert der jeweiligen Interaktion
                    interaction_matrix_val = interaction_matrix[ptype_i, ptype_j] # wenn interaktionsmatrix wie folgt definiert ist: (Traget-Partikel, Nachbarn-/Einfluss-Partikel)

                    # Berechnung des Abstands zwischen den Partikeln
                    richtungs_vector = position_j - position_i
                    distance = np.sqrt(richtungs_vector[0]**2 + richtungs_vector[1]**2)
                    if distance == 0:
                        continue
                    n_vector = richtungs_vector/distance

                    # Überprüfung, ob Partikel sich in der maximalen Einflussreichweite befinden
                    if distance <= r_max:
                        anziehung_abstoßungskraft = (1 - distance/r_max) * interaction_matrix_val * n_vector # Berechnung der Anziehungs- /Abstoßungskraft 
                        gesamtkraft += anziehung_abstoßungskraft
                        
            total_forces[target_idx] = gesamtkraft
    return total_forces

class Game:
    def __init__(self, n=2000, world_width=100.0, world_height=100.0, r_max=5.0):
        self.w = world_width
        self.h = world_height
        self.r_max = r_max

        self.pos, self.vel, self.types = self.init_particles(n, self.w, self.h)

        self.friction = 0.99
        self.noise_strength = 0.2

        self.matrix = np.array([
            [0.0,  5.0, -3.0,  2.0],
            [-2.0, 0.0,  4.0, -1.0],
            [3.0, -4.0,  0.0,  0.5],
            [1.0, -2.0,  2.0,  0.0],
        ], dtype=float)

    def step(self, dt=0.01):
        noise = np.random.normal(0.0, self.noise_strength, size=2)

        self.pos, self.vel, self.types = update_particles(
            self.pos,
            self.vel,
            self.types,
            self.w,
            self.h,
            self.r_max,
            dt,
            self.friction,
            noise,
            self.matrix,
        )

        self.pos[:, 0] = np.mod(self.pos[:, 0], self.w)
        self.pos[:, 1] = np.mod(self.pos[:, 1], self.h)

        return {
            "pos": self.pos,
            "types": self.types,
        }

    def init_particles(self, n, width, height):
        pos = np.random.rand(n, 2) * np.array([width, height], dtype=np.float32)
        vel = np.zeros((n, 2), dtype=np.float32)
        types = np.random.randint(0, 4, size=n, dtype=np.int64)  # direkt als ints
        return pos, vel, types
