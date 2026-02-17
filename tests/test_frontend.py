import p_life.gui as gui
import p_life.game as game
import numpy as np
from PySide6 import QtCore
from p_life.frontend_vispy import types_to_colors, ParticleCanvas, colour_type


# GUI Tests


def test_value_to_color():
    assert gui.value_to_color(-100) == "rgb(0,100,0)"
    assert gui.value_to_color(0) == "rgb(50,50,255)"
    assert gui.value_to_color(100) == "rgb(100,0,0)"


def test_matrix_size():
    assert len(gui.particle_force_matrix) == 4
    assert len(gui.particle_force_matrix[0]) == 4


def test_matrix_clabels():
    expected_labels = [
        ["B x B", "B x Y", "B x G", "B x R"],
        ["Y x B", "Y x Y", "Y x G", "Y x R"],
        ["G x B", "G x Y", "G x G", "G x R"],
        ["R x B", "R x Y", "R x G", "R x R"],
    ]
    for r in range(len(gui.particle_force_matrix)):
        for c in range(len(gui.particle_force_matrix[r])):
            assert gui.particle_force_matrix[r][c][0] == expected_labels[r][c]


def test_matrix_initial_values():
    for r, row in enumerate(gui.particle_force_matrix):
        for c, cell in enumerate(row):
            expected = int(round(float(gui.game.matrix[r, c]) * gui.scale))
            assert cell[1] == expected


def test_particle_force_change():
    gui.current_button = (1, 2)
    gui.particle_force_change(50)
    assert gui.particle_force_matrix[1][2][1] == 50
    gui.particle_force_change(-50)
    assert gui.particle_force_matrix[1][2][1] == -50


def test_particle_button_clicked():
    gui.particle_button_clicked(2, 3)
    assert gui.current_button == (2, 3)


def test_slider_range(qtbot):
    qtbot.addWidget(gui.slider)
    assert gui.slider.minimum() == -100
    assert gui.slider.maximum() == 100


def test_slider_value_changes_particle_force(qtbot):
    gui.current_button = (0, 0)
    qtbot.addWidget(gui.slider)
    gui.slider.setValue(50)
    assert gui.particle_force_matrix[0][0][1] == 50


def test_friction_box_updates_game(qtbot):
    qtbot.addWidget(gui.friction_box)
    gui.friction_box.setValue(0.9)
    assert gui.game.friction == 0.9


def test_particle_force_change_updates_game_matrix():
    gui.current_button = (1, 2)
    gui.particle_force_change(50)
    assert gui.game.matrix[1, 2] == 50.0 / gui.scale


def test_noise_box_updates_game(qtbot):
    qtbot.addWidget(gui.noise_box)
    gui.noise_box.setValue(0.42)
    assert gui.game.noise_strength == 0.42


def test_rmax_box_updates_game(qtbot):
    qtbot.addWidget(gui.rmax_box)
    gui.rmax_box.setValue(7.5)
    assert gui.game.r_max == 7.5


def test_pause_button_toggle(qtbot):
    qtbot.addWidget(gui.pause_btn)

    assert gui.running["on"] is True
    assert gui.pause_btn.text() == "Pause"

    qtbot.mouseClick(gui.pause_btn, QtCore.Qt.LeftButton)
    assert gui.running["on"] is False
    assert gui.pause_btn.text() == "Resume"

    qtbot.mouseClick(gui.pause_btn, QtCore.Qt.LeftButton)
    assert gui.running["on"] is True
    assert gui.pause_btn.text() == "Pause"


# Frontend Vispy Tests


def test_types_to_colors_basic():
    colors = types_to_colors([0, 1, 2, 3])
    assert colors.shape == (4, 4)
    np.testing.assert_array_equal(colors[0], colour_type[0])
    np.testing.assert_array_equal(colors[1], colour_type[1])
    np.testing.assert_array_equal(colors[2], colour_type[2])
    np.testing.assert_array_equal(colors[3], colour_type[3])


def test_types_to_colors_wraparound():
    colors = types_to_colors([4])
    assert colors.shape == (1, 4)
    np.testing.assert_array_equal(colors[0], colour_type[0])


def test_particle_canvas_step_and_draw():
    g = game.Game(n=100, world_width=50.0, world_height=50.0, r_max=10.0)
    canvas = ParticleCanvas(g, world_width=g.w, world_height=g.h)

    assert canvas.game is g
    assert canvas.dt == 1 / 60

    canvas.step_and_draw()