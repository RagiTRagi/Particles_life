import numpy as np
import numpy.testing as npt

import p_life.game as game

def test_regroup_particles_in_cells_to_assign_cells():

    """
    Tests the basic logic of the grid partitioning function.
    
    Verifies that regroup_particles_in_cells correctly:
    1. Calculates the right grid dimensions (cols and rows)
    2. Sorts particles by their cell assignment
    3. Correctly populates cell_starts and cell_counts arrays
    
    Uses a simple test case with 4 particles placed in 2 cells of a 2x2 grid.
    """

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

    sorted_pos, _, _, cell_starts, cell_counts, cols, rows = game.regroup_particles_in_cells(
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

def test_regroup_particles_in_cells_out_of_bounds():

    """
    Tests the robustness of regroup_particles_in_cells with out-of-bounds positions.
    
    Verifies that the function correctly handles particles positioned outside
    the world boundaries (negative coordinates or beyond world dimensions) by
    using np.clip to constrain them to valid grid cells.
    
    The test ensures the function doesn't crash and that all particles are
    accounted for in the cell counts despite invalid initial positions.
    """

    pos = np.array([[-1.0, -1.0], [20.0, 20.0]])
    
    _, _, _, _, cell_counts, _, _ = game.regroup_particles_in_cells(
        pos, np.zeros((2,2)), np.array([0,1]), 10, 10, 5
    )

    assert cell_counts.sum() == 2

def test_calculate_forces_repulsion():

    """
    Tests that calculate_forces correctly applies repulsion between close particles.
    
    Places two particles very close together (0.1 units apart) and verifies
    that they experience repulsive forces pushing them apart along the x-axis.
    """

    sorted_pos = np.array([[0.5, 0.5], [0.6, 0.5]], dtype=np.float32)
    sorted_types = np.array([0, 0], dtype=int)
    cell_starts = np.array([0, 0, 0, 0], dtype=int)
    cell_counts = np.array([2, 0, 0, 0], dtype=int)
    matrix = np.zeros((4, 4), dtype=np.float32)
    matrix[0, 0] = 1.0

    forces = game.calculate_forces(
        sorted_pos, 
        sorted_types, 
        cell_starts, 
        cell_counts, 
        cols=2, 
        rows=2,
        interaction_matrix=matrix, 
        r_max=5.0, 
        world_width=10.0, 
        world_height=10.0
    )

    assert forces[0, 0] < 0
    assert forces[1, 0] > 0
    assert forces[0, 1] == 0 
    assert forces[1, 1] == 0

def test_game_set_force():

    """
    Tests the set_force method of the Game class.
    
    Verifies that calling set_force correctly updates a specific entry
    in the interaction matrix with the provided force value.
    """

    g = game.Game(n=1, world_width=10.0, world_height=10.0, r_max=5.0)
        
    g.set_force(0, 1, 3.5)
    
    assert g.matrix[0, 1] == np.float32(3.5)
    

def test_game_step_applies_friction():

    """
    Tests that the Game.step method correctly applies friction to velocity.
    
    Sets up a particle with an initial velocity and friction coefficient,
    then verifies that after one step the velocity has been reduced by
    the friction factor and the position updated accordingly.
    """

    g = game.Game(n=1, world_width=100.0, world_height=100.0, r_max=5.0)
    g.pos[:] = np.array([[50.0, 50.0]], dtype=np.float32)
    g.vel[:] = np.array([[1.0, 0.0]], dtype=np.float32)
    g.noise_strength = 0.0
    g.friction = 0.9 
    g.matrix[:] = 0.0  
    out = g.step(dt=1.0)
    
    npt.assert_allclose(out["pos"][0, 0], 50.9, rtol=1e-5, atol=1e-5)

def test_game_init_particles():

    """
    Tests the init_particles method of the Game class.
    
    Verifies that:
    1. Correct number of particles are created
    2. Positions are within world boundaries
    3. Velocities are initialized to zero
    4. Types are valid integers in range [0, 4)
    """

    g = game.Game(n=100, world_width=50.0, world_height=30.0, r_max=5.0)
    
    assert len(g.pos) == 100
    assert len(g.vel) == 100
    assert len(g.types) == 100
    assert np.all(g.pos[:, 0] >= 0) and np.all(g.pos[:, 0] <= 50.0)
    assert np.all(g.pos[:, 1] >= 0) and np.all(g.pos[:, 1] <= 30.0)
    assert np.all(g.types >= 0) and np.all(g.types < 4)
    npt.assert_allclose(g.vel, np.zeros_like(g.vel))

def test_calculate_forces_no_neighbors():

    """
    Tests that particles beyond interaction radius exert no forces.
    
    Places two particles 5 units apart with r_max=1.0, ensuring they
    are in different cells and beyond interaction range. Verifies that
    no forces are calculated between them.
    """

    pos = np.array([[0.0, 0.0], [5.0, 0.0]], dtype=np.float32)
    vel = np.zeros((2, 2), dtype=np.float32)
    types = np.array([0, 0], dtype=int)

    sorted_pos, _, sorted_types, cell_starts, cell_counts, cols, rows = game.regroup_particles_in_cells(
        pos, vel, types, world_width=10.0, world_height=10.0, r_max=1.0
    )

    forces = game.calculate_forces(
        sorted_pos, 
        sorted_types, 
        cell_starts, 
        cell_counts, cols, 
        rows,
        np.zeros((4, 4), 
        dtype=np.float32), 
        r_max=1.0,
        world_width=10.0, 
        world_height=10.0
    )

    npt.assert_allclose(forces, np.zeros_like(forces), rtol=1e-6, atol=1e-6)

def test_calculate_forces_two_particles():

    """
    Tests force calculation between two particles at medium distance.
    
    Places two particles 1.0 units apart and verifies that the calculated
    force matches the expected value based on the Lennard-Jones-inspired
    potential formula used in the simulation.
    """

    pos = np.array([[1.0, 1.0], [2.0, 1.0]], dtype=np.float32)
    vel = np.zeros((2, 2), dtype=np.float32)
    types = np.array([0, 0], dtype=int)
    matrix = np.zeros((4, 4), dtype=np.float32)
    matrix[0, 0] = 1.0

    sorted_pos, _, sorted_types, cell_starts, cell_counts, cols, rows = game.regroup_particles_in_cells(
        pos, vel, types, world_width=10.0, world_height=10.0, r_max=2.0
    )

    forces = game.calculate_forces(
        sorted_pos, 
        sorted_types, 
        cell_starts, 
        cell_counts, 
        cols, 
        rows,
        matrix, 
        r_max=2.0, 
        world_width=10.0, 
        world_height=10.0
    )

    order = np.lexsort((sorted_pos[:, 1], sorted_pos[:, 0]))
    forces = forces[order]

    pct = (0.5 - 0.3) / (1.0 - 0.3)
    shape = 1.0 - abs(2.0 * pct - 1.0)
    force_factor = np.float32(shape)
    expected = np.array([[force_factor, 0.0], [-force_factor, 0.0]], dtype=np.float32)

    npt.assert_allclose(forces, expected, rtol=1e-6, atol=1e-6)

def test_update_particles_no_forces_no_noise(monkeypatch):

    """
    Tests update_particles with no forces and no noise (pure velocity integration).
    
    Mocks the calculate_forces function to return zero forces, then verifies
    that particles move purely according to their initial velocities with
    friction=1.0 (no friction) and noise_strength=0.0 (no noise).
    """
    
    pos = np.array([[1.0, 1.0], [2.0, 2.0]], dtype=np.float32)
    vel = np.array([[0.5, -0.5], [1.0, 0.0]], dtype=np.float32)
    types = np.array([0, 1], dtype=int)

    def fake_forces(
        sorted_pos, 
        sorted_types, 
        cell_starts, 
        cell_counts, 
        cols, 
        rows,
        matrix, 
        r_max, 
        world_width, 
        world_height
    ):
        return np.zeros_like(sorted_pos, dtype=np.float32)

    monkeypatch.setattr(game, "calculate_forces", fake_forces)

    new_pos, new_vel, _ = game.update_particles(
        pos,
        vel,
        types,
        world_width=10.0,
        world_height=10.0,
        r_max=5.0,
        dt=1.0,
        friction=1.0,
        noise_strength=0.0,
        matrix=np.zeros((4, 4), dtype=np.float32),
    )
    
    order = np.lexsort((new_pos[:, 1], new_pos[:, 0]))
    new_pos = new_pos[order]
    new_vel = new_vel[order]

    expected_pos = pos + vel
    expected_order = np.lexsort((expected_pos[:, 1], expected_pos[:, 0]))
    expected_pos = expected_pos[expected_order]
    expected_vel = vel[expected_order]

    npt.assert_allclose(new_pos, expected_pos)
    npt.assert_allclose(new_vel, expected_vel)

def test_game_step_wraps():

    """
    Tests that Game.step correctly wraps particles in torus-world.
    
    Places a particle near the world boundary and gives it velocity that
    would move it beyond the boundary. Verifies that after one step, the
    particle position wraps around to the opposite side of the world.
    """
    
    g = game.Game(n=1, world_width=3.0, world_height=3.0, r_max=5.0)
    g.pos[:] = np.array([[2.9, 2.9]], dtype=np.float32)
    g.vel[:] = np.array([[0.5, 0.5]], dtype=np.float32)
    g.noise_strength = 0.0
    g.friction = 1.0
    g.matrix[:] = 0.0  

    out = g.step(dt=1.0)

    npt.assert_allclose(
        out["pos"][0], 
        np.array([0.4, 0.4],
        dtype=np.float32), 
        rtol=1e-6, 
        atol=1e-6
    )
