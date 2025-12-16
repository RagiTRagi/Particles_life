import numpy as np

letter_index = {'Blau': 0, 'Rot': 1, 'Gelb': 2, 'Grün': 3}

def init_particles(n, width, height):
    # Zufällige Positionen
    pos = np.random.rand(n, 2) * np.array([width, height])
    
    # Zufällige Start-Geschwindigkeiten (optional, hier 0)
    vel = np.zeros((n, 2))
    
    # Zufällige Typen (A, B, C)
    type_keys = list(letter_index.keys())
    types = np.random.choice(type_keys, n)
    
    return pos, vel, types
