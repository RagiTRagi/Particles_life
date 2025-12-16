import numpy as np

# für die Matrix Conversion
letter_index = {"A":0, "B":1, "C":2}

def calculate_forces(grid, interaction_matrix, noise_param, r_max):

    cols = grid['cols']
    rows = grid['rows']
    cell_starts = grid['starts']
    cell_counts = grid['counts']
    sorted_pos = grid['pos']
    sorted_types = grid['types']

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
                    interaction_matrix_val = interaction_matrix[letter_index.get(ptype_i), letter_index.get(ptype_j)] # wenn interaktionsmatrix wie folgt definiert ist: (Traget-Partikel, Nachbarn-/Einfluss-Partikel)

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