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

    return {
        "pos": sorted_pos,       # Die sortierten Daten
        "vel": sorted_vel,
        "types": sorted_types,
        "starts": cell_starts,   # Das Inhaltsverzeichnis
        "counts": cell_counts,   # Wie viele Partikel pro Zelle
        "cols": cols,
        "rows": rows
    }

def update_particles(pos, vel, types, world_width, world_height, r_max, dt, friction):
    
    # Grid berechnen
    grid = quadrantisieren(pos, vel, types, world_width, world_height, r_max)

    # Kräfte berechnen
    forces = calculate_forces(grid)

    # Neue Velocity berechnen
    grid['vel'] += forces * dt
    grid['vel'] *= friction

    # Position updaten
    grid['pos'] += grid['vel'] * dt

    # Ausgabe von Position, Geschwindigkeit und Typ
    return grid['pos'], grid['vel'], grid['types']