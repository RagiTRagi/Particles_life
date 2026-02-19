"""
Tests for the p_life GUI and VisPy frontend.

This part contains pytest-based tests that validate:
- GUI matrix structure, labels, and value synchronization with the game model
- UI interactions (slider/spinboxes/buttons) updating the state
- Color mapping for particle types
- Basic stepping/drawing behavior of the VisPy particle canvas

"""

import numpy as np
from PySide6 import QtCore

import p_life.gui as gui
import p_life.game as game
from p_life.frontend_vispy import types_to_colors, ParticleCanvas

# GUI Tests


def test_matrix_size():
    """Testing if partifle force matrix is a 4x4 grid."""
    assert len(gui.particle_force_matrix) == 4
    assert len(gui.particle_force_matrix[0]) == 4


def test_matrix_clabels():
    """Verify that each matrix cell has the expected label."""
    expected_labels = [
        ["🔵 -> 🔵", "🔵 -> 🟡", "🔵 -> 🟢", "🔵 -> 🔴"],
        ["🟡 -> 🔵", "🟡 -> 🟡", "🟡 -> 🟢", "🟡 -> 🔴"],
        ["🟢 -> 🔵", "🟢 -> 🟡", "🟢 -> 🟢", "🟢 -> 🔴"],
        ["🔴 -> 🔵", "🔴 -> 🟡", "🔴 -> 🟢", "🔴 -> 🔴"],
    ]
    for r in range(len(gui.particle_force_matrix)):
        for c in range(len(gui.particle_force_matrix[r])):
            assert gui.particle_force_matrix[r][c][0] == expected_labels[r][c]


def test_matrix_initial_values():
    """Check that GUI matrix values match the initial game matrix values."""
    for r, row in enumerate(gui.particle_force_matrix):
        for c, cell in enumerate(row):
            expected = int(round(float(gui.game.matrix[r, c]) * gui.SCALE))
            assert cell[1] == expected


def test_particle_force_change():
    """Verify that particle_force_change updates the currently selected matrix cell."""
    gui.current_button = (1, 2)
    gui.particle_force_change(50)
    assert gui.particle_force_matrix[1][2][1] == 50
    gui.particle_force_change(-50)
    assert gui.particle_force_matrix[1][2][1] == -50


def test_particle_button_clicked():
    """Ensure clicking a particle button stores the selected cell coordinates."""
    gui.particle_button_clicked(2, 3)
    assert gui.current_button == (2, 3)


def test_slider_value_changes_particle_force(qtbot):
    """Ensure slider movement updates the selected particle force value."""
    gui.current_button = (0, 0)
    qtbot.addWidget(gui.slider)
    gui.slider.setValue(50)
    assert gui.particle_force_matrix[0][0][1] == 50


def test_friction_box_updates_game(qtbot):
    """Ensure friction spinbox updates the game friction parameter."""
    qtbot.addWidget(gui.friction_box)
    gui.friction_box.setValue(0.9)
    assert gui.game.friction == 0.9


def test_particle_force_change_updates_game_matrix():
    """Ensure changing a force updates the game matrix."""
    gui.current_button = (1, 2)
    gui.particle_force_change(50)
    assert gui.game.matrix[1, 2] == 50.0 / gui.SCALE


def test_noise_box_updates_game(qtbot):
    """Ensure noise spinbox updates the game noise strength parameter."""
    qtbot.addWidget(gui.noise_box)
    gui.noise_box.setValue(0.42)
    assert gui.game.noise_strength == 0.42


def test_pause_button_toggle(qtbot):
    """Ensure pause button toggles the running state and label text."""
    qtbot.addWidget(gui.pause_btn)

    assert gui.running is True
    assert gui.pause_btn.text() == "Pause"

    qtbot.mouseClick(gui.pause_btn, QtCore.Qt.LeftButton)
    assert gui.running is False
    assert gui.pause_btn.text() == "Resume"

    qtbot.mouseClick(gui.pause_btn, QtCore.Qt.LeftButton)
    assert gui.running is True
    assert gui.pause_btn.text() == "Pause"


# Frontend Vispy Tests


def test_types_to_colors_basic():
    """Ensure type-to-color mapping returns unique RGBA float32 colors."""
    colors = types_to_colors([0, 1, 2, 3])
    assert colors.shape == (4, 4)
    assert colors.dtype == np.float32
    assert len({tuple(row) for row in colors}) == 4


def test_types_to_colors_wraparound():
    """Ensure type-to-color mapping wraps around after the base palette size."""
    c0 = types_to_colors([0])[0]
    c4 = types_to_colors([4])[0]  
    np.testing.assert_array_equal(c4, c0)


def test_particle_canvas_step_and_draw():
    """Ensure ParticleCanvas initialization and step_and_draw run without raising exceptions."""
    g = game.Game(n=100, world_width=50.0, world_height=50.0, r_max=10.0)
    canvas = ParticleCanvas(g, world_width=g.w, world_height=g.h, dt=1/60)

    assert canvas.game is g
    assert canvas.dt == 1 / 60

    canvas.step_and_draw()