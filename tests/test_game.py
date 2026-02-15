import numpy as np
import numpy.testing as npt

import p_life.game as game

def test_quadrantisieren():
    pos = np.array([
        [1.0, 1.0], 
        [6.0, 1.0], 
        [1.1, 1.1], 
        [6.1, 1.1]
    ])
    velocities = np.zeros((4, 2))
    types = np.array([0, 1, 2, 3])
    world_width = 10.0
    world_height = 10.0
    r_max = 5.0

    sorted_pos, sorted_vel, sorted_types, cell_starts, cell_counts, cols, rows = game.quadrantisieren(
        pos, velocities, types, world_width, world_height, r_max
    )

    assert cols == 2
    assert rows == 2
    
    assert len(sorted_pos) == 4
    
    assert cell_starts[0] == 0
    assert cell_counts[0] == 2
    
    assert cell_starts[1] == 2
    assert cell_counts[1] == 2
    
    assert cell_counts[2] == 0
    assert cell_counts[3] == 0

def test_quadrantisieren_out_of_bounds():
    pos = np.array([[-1.0, -1.0], [20.0, 20.0]])
    
    sorted_pos, sorted_vel, sorted_types, cell_starts, cell_counts, cols, rows = game.quadrantisieren(
        pos, np.zeros((2,2)), np.array([0,1]), 10, 10, 5
    )

    assert cell_counts.sum() == 2

def test_calculate_forces_repulsion():
    sorted_pos = np.array([[0.5, 0.5], [0.6, 0.5]], dtype=np.float32)
    sorted_types = np.array([0, 0], dtype=int)
    
    cell_starts = np.array([0, 0, 0, 0], dtype=int)
    cell_counts = np.array([2, 0, 0, 0], dtype=int)
    
    matrix = np.zeros((4, 4), dtype=np.float32)
    matrix[0, 0] = 1.0

    forces = game.calculate_forces(
        sorted_pos, sorted_types, cell_starts, cell_counts, cols=2, rows=2,
        interaction_matrix=matrix, r_max=5.0, world_width=10.0, world_height=10.0
    )

    assert forces[0, 0] < 0
    assert forces[1, 0] > 0
    assert forces[0, 1] == 0 
    assert forces[1, 1] == 0

def test_game_set_force():
    g = game.Game(n=1, world_width=10.0, world_height=10.0, r_max=5.0)
    
    original_val = g.matrix[0, 1]
    
    g.set_force(0, 1, 3.5)
    
    assert g.matrix[0, 1] == np.float32(3.5)
    
    assert g.matrix[0, 0] != g.matrix[0, 1]

def test_game_step_with_friction():
    g = game.Game(n=1, world_width=100.0, world_height=100.0, r_max=5.0)
    g.pos[:] = np.array([[50.0, 50.0]], dtype=np.float32)
    g.vel[:] = np.array([[1.0, 0.0]], dtype=np.float32)
    g.noise_strength = 0.0
    g.friction = 0.9 
    g.matrix[:] = 0.0  
    out = g.step(dt=1.0)
    
    npt.assert_allclose(out["pos"][0, 0], 50.9, rtol=1e-5, atol=1e-5)

def test_game_init_particles():
    g = game.Game(n=100, world_width=50.0, world_height=30.0, r_max=5.0)
    
    assert len(g.pos) == 100
    assert len(g.vel) == 100
    assert len(g.types) == 100
    
    assert np.all(g.pos[:, 0] >= 0) and np.all(g.pos[:, 0] <= 50.0)
    assert np.all(g.pos[:, 1] >= 0) and np.all(g.pos[:, 1] <= 30.0)
    
    assert np.all(g.types >= 0) and np.all(g.types < 4)
    
    npt.assert_allclose(g.vel, np.zeros_like(g.vel))

def test_calculate_forces_no_neighbors():
    pos = np.array([[0.0, 0.0], [5.0, 0.0]], dtype=np.float32)
    vel = np.zeros((2, 2), dtype=np.float32)
    types = np.array([0, 0], dtype=int)

    sorted_pos, sorted_vel, sorted_types, cell_starts, cell_counts, cols, rows = game.quadrantisieren(
        pos, vel, types, world_width=10.0, world_height=10.0, r_max=1.0
    )

    forces = game.calculate_forces(
        sorted_pos, sorted_types, cell_starts, cell_counts, cols, rows,
        np.zeros((4, 4), dtype=np.float32), r_max=1.0,
        world_width=10.0, world_height=10.0
    )

    npt.assert_allclose(forces, np.zeros_like(forces), rtol=1e-6, atol=1e-6)

def test_calculate_forces_two_particles():
    pos = np.array([[1.0, 1.0], [2.0, 1.0]], dtype=np.float32)
    vel = np.zeros((2, 2), dtype=np.float32)
    types = np.array([0, 0], dtype=int)

    matrix = np.zeros((4, 4), dtype=np.float32)
    matrix[0, 0] = 1.0

    sorted_pos, sorted_vel, sorted_types, cell_starts, cell_counts, cols, rows = game.quadrantisieren(
        pos, vel, types, world_width=10.0, world_height=10.0, r_max=2.0
    )

    forces = game.calculate_forces(
        sorted_pos, sorted_types, cell_starts, cell_counts, cols, rows,
        matrix, r_max=2.0, world_width=10.0, world_height=10.0
    )

    order = np.lexsort((sorted_pos[:, 1], sorted_pos[:, 0]))
    forces = forces[order]

    pct = (0.5 - 0.3) / (1.0 - 0.3)
    shape = 1.0 - abs(2.0 * pct - 1.0)
    force_factor = np.float32(shape)

    expected = np.array([[force_factor, 0.0], [-force_factor, 0.0]], dtype=np.float32)
    npt.assert_allclose(forces, expected, rtol=1e-6, atol=1e-6)

def test_update_particles_no_forces_no_noise():
    pos = np.array([[1.0, 1.0], [2.0, 2.0]], dtype=np.float32)
    vel = np.array([[0.5, -0.5], [1.0, 0.0]], dtype=np.float32)
    types = np.array([0, 1], dtype=int)

    def fake_forces(sorted_pos, sorted_types, cell_starts, cell_counts, cols, rows,
                    matrix, r_max, world_width, world_height):
        return np.zeros_like(sorted_pos, dtype=np.float32)

    game.calculate_forces = fake_forces

    new_pos, new_vel, new_types = game.update_particles(
        pos, vel, types,
        world_width=10.0, world_height=10.0, r_max=5.0,
        dt=1.0, friction=1.0, noise_strength=0.0,
        matrix=np.zeros((4, 4), dtype=np.float32)
    )

    idx = np.lexsort((new_pos[:, 1], new_pos[:, 0]))
    new_pos = new_pos[idx]
    new_vel = new_vel[idx]

    expected_pos = pos + vel
    idx_exp = np.lexsort((expected_pos[:, 1], expected_pos[:, 0]))
    expected_pos = expected_pos[idx_exp]
    expected_vel = vel[idx_exp]

    npt.assert_allclose(new_pos, expected_pos)
    npt.assert_allclose(new_vel, expected_vel)

def test_game_step_wraps():
    g = game.Game(n=1, world_width=3.0, world_height=3.0, r_max=5.0)
    g.pos[:] = np.array([[2.9, 2.9]], dtype=np.float32)
    g.vel[:] = np.array([[0.5, 0.5]], dtype=np.float32)
    g.noise_strength = 0.0
    g.friction = 1.0
    g.matrix[:] = 0.0  

    out = g.step(dt=1.0)
    npt.assert_allclose(out["pos"][0], np.array([0.4, 0.4], dtype=np.float32), rtol=1e-6, atol=1e-6)
