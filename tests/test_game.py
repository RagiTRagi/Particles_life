import numpy as np
from Particles_life.game import quadrantisieren

def test_quadrantisieren_logic():
    pos = np.array([
        [1.0, 1.0], # Zelle 0
        [6.0, 1.0], # Zelle 1
        [1.1, 1.1], # Zelle 0
        [6.1, 1.1]  # Zelle 1
    ])
    velocities = np.zeros((4, 2))
    types = np.array([0, 1, 2, 3])
    world_width = 10.0
    world_height = 10.0
    r_max = 5.0

    # Ausführung
    sorted_pos, sorted_vel, sorted_types, cell_starts, cell_counts, cols, rows = quadrantisieren(
        pos, velocities, types, world_width, world_height, r_max
    )

    # 1. Teste die Grid-Dimensionen
    assert cols == 2
    assert rows == 2
    
    # 2. Teste die Sortierung
    assert len(sorted_pos) == 4
    
    # 3. Teste cell_starts und cell_counts
    assert cell_starts[0] == 0
    assert cell_counts[0] == 2
    
    # Zelle 1 (unten rechts): Startet bei 2, hat 2 Partikel
    assert cell_starts[1] == 2
    assert cell_counts[1] == 2
    
    # Zelle 2 & 3 (obere Reihe): Leer
    assert cell_counts[2] == 0
    assert cell_counts[3] == 0

def test_quadrantisieren_out_of_bounds():
    # Testet den np.clip Schutz gegen Werte außerhalb der Welt
    pos = np.array([[-1.0, -1.0], [20.0, 20.0]])
    
    # Hier prüfen wir nur, ob es ohne Absturz durchläuft (wegen np.clip)
    _, _, _, _, cell_counts, _, _ = quadrantisieren(
        pos, np.zeros((2,2)), np.array([0,1]), 10, 10, 5
    )
    # Beide sollten in Zelle 0 bzw. der letzten Zelle landen, nicht außerhalb des Index
    assert cell_counts.sum() == 2