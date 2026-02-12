import numpy as np

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
    forces = calculate_forces(sorted_pos, sorted_types, cell_starts, cell_counts, cols, rows, matrix, r_max)

    # Neue Velocity berechnen
    sorted_vel += forces * dt
    sorted_vel += noise
    sorted_vel *= friction

    # Position updaten
    sorted_pos += sorted_vel * dt

    # Ausgabe von Position, Geschwindigkeit und Typ
    return sorted_pos, sorted_vel, sorted_types
# für die Matrix Conversion

letter_index = {"blau":0, "gelb":1, "grün":2, "rot":3} # 0 = rot, 1 = grün, 2 = gelb, 3 = blau
sorted_colors = ["blau", "gelb", "gruen", "rot"]

def calculate_forces(sorted_pos, sorted_types, cell_starts, cell_counts, cols, rows, interaction_matrix, r_max):

    # Grids filtern, die mind. 1 Partikel beinhalten & Initialisierung von array, welches die Gesamtkräfte jedes Partikels beinhaltet
    filled_grids = np.where(cell_counts > 0)[0]
    total_forces = np.zeros_like(sorted_pos, dtype=float)
    #print(sorted_types[:10])
    sorted_types = np.searchsorted(sorted_colors, sorted_types)
    # Iteration durch jedes befüllte target cell_grid und Berechnung der Nachbarn(oben/unten/links/rechts)
    # partikel in einem grid haben alle die selben nachbargrids und somit die selben partikel
    for cell_id in filled_grids:
        n_ids = [cell_id]
        x = cell_id % cols
        y = cell_id // cols

        # if evtl. mit masken ersetzen
        if x < cols - 1:
            right_n = cell_id + 1         
            n_ids.append(right_n)
        if x > 0:
            left_n = cell_id - 1
            n_ids.append(left_n)
        if x > 0 and y > 0:
            left_upper_diagonal_n = cell_id - (cols + 1)
            n_ids.append(left_upper_diagonal_n)
        if x > 0 and y < rows - 1:
            left_lower_diagonal_n = cell_id + (cols - 1)
            n_ids.append(left_lower_diagonal_n)
        if x < cols - 1 and y > 0:
            right_upper_diagonal_n = cell_id - (cols - 1)
            n_ids.append(right_upper_diagonal_n)
        if x < cols - 1 and y < rows - 1:
            right_lower_diagonal_n = cell_id + (cols + 1)
            n_ids.append(right_lower_diagonal_n)
        if y > 0:
            upper_n = cell_id - cols
            n_ids.append(upper_n)
        if y < rows - 1:
            lower_n = cell_id + cols
            n_ids.append(lower_n)
        n_ids = np.array(n_ids)
        # Indizes der Partikel im target Grid 
        s0 = cell_starts[cell_id]
        c0 = cell_counts[cell_id]
        target_particles = np.array(range(s0, s0+c0))
        # print(target_particles.shape)
        # Iteration über jedes Partikel in dem target grid
        
        #broadcasted_noise = np.broadcast_to(noise_param, (len(target_particles), 2))
        #gesamtkraft = broadcasted_noise.copy()  #[None,:] #additive Zufallsbewegung, wie bei Brown'sche Molekularbewegungen -> noise muss demnach ein Vektor sein
        gesamtkraft = 0 #noise_param[target_particles].copy()
        #position_i = np.array(sorted_pos[target_particles])
        #ptype_i = np.array(sorted_types[target_particles])
        #print(ptype_i.shape)
        #velocity_i = sorted_vel[target_idx]
        #print("Gesamtkraft:", gesamtkraft.shape)
            
            
        # Iteration über jedes Nachbar-Grid
            
        # Indizes der Partikel des Nachbar-Grids
        s = cell_starts[n_ids]
        c = cell_counts[n_ids]
        source = np.concatenate([np.arange(start, start + count) for start, count in zip(s, c)])[:, None]

        source_particles = np.broadcast_to(source, (len(source), len(target_particles)))
        #print("source_particles before mask:", source_particles.shape)
        #print(source_particles)
        #print(ptype_i)
        #print(source_particles.size)
        #print(target_particles.size)
        #print(mask1) 
        #mask1 = ~np.all(np.isclose(source_particles, target_particles), axis=1)
        #np.any(source_particles != target_particles, axis=1)
        #print("Maske:", mask1)
        #print(mask1.shape)

        
        if source_particles.shape[0] == 0:
            total_forces[target_particles] = gesamtkraft
            continue
        position_j = sorted_pos[source_particles]
        ptype_j = sorted_types[source_particles]
        position_i = sorted_pos[target_particles]
        ptype_i = sorted_types[target_particles]
        #print("Target_particle_types:",ptype_i.shape)
        #print("source particle types:", ptype_j.shape)
        #print("target_particle Types:",ptype_i)
        #interaction_pairs = np.stack((np.ones_like(ptype_j)*ptype_i, ptype_j), axis=1)
        #print(interaction_pairs.shape)
        interaction_vals = interaction_matrix[ptype_i[None,:], ptype_j]
        #print("interaction matrix shape:",interaction_matrix.shape)
        #print(sorted_types[:10])
        #interaction_vals = interaction_matrix[ptype_i, ptype_j]
        #print("interaction values:", interaction_vals.shape)
        richtungs_vector = position_j - position_i
        #print("RV 1:",richtungs_vector.shape)
        distance = np.sqrt(richtungs_vector[:,:,0]**2 + richtungs_vector[:,:,1]**2)
        #print("Distance Vektor:", distance)
        #print("Distance 1:", distance.shape)
        mask2 = (distance > 0) & (distance <= r_max)
        #print(mask2, mask2.shape)
        #print(mask2)
        safe_distance = np.where(mask2, distance, 1.0)
        #print("Distance 2:", distance_.shape)
        richtungs_vector_ = richtungs_vector * mask2[:, :, None]
        #print("RV 2:", richtungs_vector_.shape)
        #print(position_j.shape, position_i.shape, richtungs_vector.shape)
        n_vectors = richtungs_vector_/safe_distance[:,:,None] # Richtungsvektor bei Distanz sowieso 0  
        #print("NV:", n_vectors)
        #print("NV", n_vectors.shape)
        #print("(1 - distance_/r_max):", (1 - distance_/r_max))

        w = (1 - safe_distance/r_max) * interaction_vals*mask2
        #print("W = ",w.shape)
        anziehung_abstoßungskraft = n_vectors * w[:,:,None]
        #print(anziehung_abstoßungskraft.shape)
        gesamtkraft += anziehung_abstoßungskraft.sum(axis=0)
        #print(gesamtkraft.shape)
        total_forces[target_particles] = gesamtkraft
    return total_forces

class Game:
    def __init__(self, n=2000, world_width=100.0, world_height=100.0, r_max=5.0):
        self.w = world_width
        self.h = world_height
        self.r_max = r_max

        self.pos, self.vel, self.types = self.init_particles(n, self.w, self.h)

        self.friction = 0.98
        self.noise_strength = 1.0

        self.matrix = np.array([
            [ 100.2, -0.8,  0.6, -0.2],  # blau
            [ 0.6,  100.2, -0.8, -0.2],  # gelb
            [-0.8,  0.6,  100.2, -0.2],  # grün
            [-0.2, -0.2, -0.2,  100.4],  # rot
        ], dtype=float)

    def step(self, dt=0.01):
        noise = np.random.normal(0.0, self.noise_strength, size=(self.pos.shape[0], 2))
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


        type_keys = list(letter_index.keys())
        types = np.random.choice(type_keys, n)

        return pos, vel, types
