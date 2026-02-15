from p_life.gui import value_to_color, particle_force_matrix, particle_force_change

def test_value_to_color():
    # Teste negative Werte
    assert value_to_color(-100) == "rgb(0,100,0)"
    
    # Teste Null
    assert value_to_color(0) == "rgb(50,50,255)"

    # Teste positive Werte
    assert value_to_color(100) == "rgb(100,0,0)"

def test_matrix_size():
    assert len(particle_force_matrix) == 4
    assert len(particle_force_matrix[0]) == 4

def test_matrix_clabels():
    expected_labels = [
        ["R x R", "R x Y", "R x G", "R x B"],
        ["Y x R", "Y x Y", "Y x G", "Y x B"],
        ["G x R", "G x Y", "G x G", "G x B"],
        ["B x R", "B x Y", "B x G", "B x B"]
    ]
    for row in range(len(particle_force_matrix)):
        for col in range(len(particle_force_matrix[row])):
            assert particle_force_matrix[row][col][0] == expected_labels[row][col]

def test_matrix_initial_values():
    for row in particle_force_matrix:
        for cell in row:
            assert cell[1] == 0

def test_particle_force_change():
    import p_life.gui as gui
    gui.current_button = (1, 2)
    gui.particle_force_change(50)
    assert gui.particle_force_matrix[1][2][1] == 0.5
    gui.particle_force_change(-50)
    assert gui.particle_force_matrix[1][2][1] == -0.5