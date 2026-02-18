from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Qt

try:
    from .game import Game
    from .frontend_vispy import ParticleCanvas
except ImportError:
    from game import Game
    from frontend_vispy import ParticleCanvas


app = QtWidgets.QApplication([])
window = QtWidgets.QWidget()
window.resize(100, 100)
window.setWindowTitle("particles life")

main_layout = QtWidgets.QHBoxLayout(window)
scale = 50.0
controls = QtWidgets.QWidget()
layout = QtWidgets.QGridLayout(controls)
main_layout.addWidget(controls, stretch=0)

game = Game(
    n=10000,
    world_width=100.0,
    world_height=100.0,
    r_max=5.0,
)
canvas = ParticleCanvas(game, world_width=game.w, world_height=game.h)
main_layout.addWidget(canvas.native, stretch=1)


particle_list = ["🔵", "🟡", "🟢", "🔴"]

particle_force_matrix = []
for i in particle_list:
    row = []
    for j in particle_list:
        row.append(f"{i[0].upper()} -> {j[0].upper()}")
    particle_force_matrix.append(row)

for row in range(len(particle_force_matrix)):
    for col in range(len(particle_force_matrix[row])):
        particle_force_matrix[row][col] = [particle_force_matrix[row][col], 0]

for r in range(4):
    for c in range(4):
        particle_force_matrix[r][c][1] = int(round(float(game.matrix[r, c]) * scale))


def value_to_color(value):

    if value < 0:

        t = (value + 50) / 50
        r = int(100 + t * 155)
        g = int(100 + t * 155)
        b = int(100 + t * 155)
    
    elif value == 0:
        r = 255
        g = 255
        b = 255
    
    else:

        t = value / 50
        r = 255
        g = int(255 - t * 255)
        b = 255

    return f"rgb({r},{g},{b})"


button_matrix = []

current_button = (0, 0)

for row in range(len(particle_force_matrix)):
    buttons = []
    for col in range(len(particle_force_matrix[row])):
        button = QtWidgets.QPushButton(particle_force_matrix[row][col][0])
        button.clicked.connect(lambda _, r=row, c=col: particle_button_clicked(r, c))
        button.setStyleSheet(f"background-color: {value_to_color(particle_force_matrix[row][col][1])}")
        layout.addWidget(button, row, col)
        buttons.append(button)
    button_matrix.append(buttons)


def particle_button_clicked(row, col):
    print(f"Button at row {row}, column {col} clicked.")
    global current_button
    current_button = (row, col)
    slider.setValue(int(particle_force_matrix[row][col][1]))

def particle_force_change(value):
    if current_button is not None:
        row, col = current_button

        particle_force_matrix[row][col][1] = int(value)

        print(f"Force between {particle_force_matrix[row][col][0]} changed to {value}")
        button_matrix[row][col].setStyleSheet(f"background-color: {value_to_color(value)}")

        force = float(value) / scale

        if hasattr(game, "set_force"):
            game.set_force(row, col, force)
        
slider = QtWidgets.QSlider()
slider.setOrientation(Qt.Orientation.Horizontal)
slider.setFixedHeight(24)
slider.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
slider.setRange(-50, 50)
slider.valueChanged.connect(particle_force_change)

num_rows = len(particle_force_matrix)
num_cols = len(particle_force_matrix[0])
layout.addWidget(slider, num_rows, 0, 1, num_cols)

friction_box = QtWidgets.QDoubleSpinBox()
friction_box.setRange(0.80, 0.999)
friction_box.setSingleStep(0.001)
friction_box.setDecimals(3)
friction_box.setValue(float(game.friction))
friction_box.valueChanged.connect(lambda v: setattr(game, "friction", float(v)))
layout.addWidget(QtWidgets.QLabel("friction"), num_rows+1, 0)
layout.addWidget(friction_box, num_rows+1, 1, 1, num_cols-1)

noise_box = QtWidgets.QDoubleSpinBox()
noise_box.setRange(0.0, 1.0)
noise_box.setSingleStep(0.01)
noise_box.setDecimals(3)
noise_box.setValue(float(game.noise_strength))
noise_box.valueChanged.connect(lambda v: setattr(game, "noise_strength", float(v)))
layout.addWidget(QtWidgets.QLabel("noise"),  num_rows+2, 0)
layout.addWidget(noise_box, num_rows+2, 1, 1, num_cols-1)


pause_btn = QtWidgets.QPushButton("Pause")
layout.addWidget(pause_btn, num_rows+4, 0, 1, num_cols)

running = {"on": True}
def toggle():
    if running["on"]:
        timer.stop()
        pause_btn.setText("Resume")
        running["on"] = False
    else:
        timer.start(int(1000 / 60))
        pause_btn.setText("Pause")
        running["on"] = True

pause_btn.clicked.connect(toggle)

restart_btn = QtWidgets.QPushButton("Reset")

def restart():
    if hasattr(game, "reset_particles"):
        game.reset_particles()

restart_btn.clicked.connect(restart)
layout.addWidget(restart_btn, num_rows+3, 0, 1, num_cols)

particle_button_clicked(0, 0)

timer = QtCore.QTimer()
timer.timeout.connect(canvas.step_and_draw) 
timer.start(int(1000 / 60))

window.showMaximized()
app.exec()