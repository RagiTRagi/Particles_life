from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QSlider, QGridLayout, QSizePolicy
from PySide6.QtCore import Qt


app = QApplication([])
window = QWidget()
window.resize(1000, 500)
window.setWindowTitle("particles life")
layout = QGridLayout()



particle_list = ["red", "yellow", "green", "blue"]

particle_force_matrix = []
for i in particle_list:
    row = []
    for j in particle_list:
        row.append(f"{i[0].upper()} x {j[0].upper()}")
    particle_force_matrix.append(row)

for row in range(len(particle_force_matrix)):
    for col in range(len(particle_force_matrix[row])):
        particle_force_matrix[row][col] = [particle_force_matrix[row][col], 0]


def value_to_color(value):

    """
    Converts a force value to an RGB color string for button styling.
    
    Maps force values from the range [-100, 100] to a color gradient:
    - Negative values: Green gradient (darker = more negative)
    - Zero: Blue
    - Positive values: Red gradient (darker = more positive)
    
    This provides visual feedback for the interaction matrix values.
    
    Args:
        value (int or float): Force value in range [-100, 100]
    
    Returns:
        str: RGB color string in format "rgb(r,g,b)" for use in Qt stylesheets
    """

    if value < 0:

        t = (value + 100) / 100
        r = 0
        g = int(100 + t * 155)
        b = 0
    
    elif value == 0:
        r = 50
        g = 50
        b = 255
    
    else:
        
        t = value / 100
        
        r = int(255 - t * 155)
        g = 0
        b = 0

    return f"rgb({r},{g},{b})"


button_matrix = []

for row in range(len(particle_force_matrix)):
    buttons = []
    for col in range(len(particle_force_matrix[row])):
        button = QPushButton(particle_force_matrix[row][col][0])
        button.clicked.connect(lambda _, r=row, c=col: particle_button_clicked(r, c))
        button.setStyleSheet(f"background-color: {value_to_color(particle_force_matrix[row][col][1])}")
        layout.addWidget(button, row, col)
        buttons.append(button)
    button_matrix.append(buttons)



current_button = 0, 0
def particle_button_clicked(row, col):

    """
    Handles button clicks in the interaction matrix grid.
    
    When a user clicks a button representing an interaction between two particle
    types, this function:
    1. Updates the global current_button to track which interaction is selected
    2. Updates the slider to show the current force value for that interaction
    
    Args:
        row (int): Row index of the clicked button (first particle type)
        col (int): Column index of the clicked button (second particle type)
    """

    print(f"Button at row {row}, column {col} clicked.")
    global current_button
    current_button = row, col
    slider.setValue(particle_force_matrix[row][col][1])

slider = QSlider()
slider.setOrientation(Qt.Orientation.Horizontal)
slider.setFixedHeight(24)
slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
slider.setRange(-100, 100)
slider.valueChanged.connect(lambda value: particle_force_change(value))
num_rows = len(particle_force_matrix)
num_cols = len(particle_force_matrix[0])
layout.addWidget(slider, num_rows, 0, 1, num_cols)

def particle_force_change(value):

    """
    Handles slider value changes to update interaction forces.
    
    When the user moves the slider, this function:
    1. Updates the force value in the particle_force_matrix for the currently
       selected button
    2. Updates the button's background color to reflect the new force value
    3. Prints the change to the console
    
    The force values are normalized to the range [-1.0, 1.0] by dividing by 100.
    
    Args:
        value (int): New slider value in range [-100, 100]
    """
    
    if current_button is not None:

        row, col = current_button
        particle_force_matrix[row][col][1] = value / 100
        print(f"Force between {particle_force_matrix[row][col][0]} changed to {value}")
        button_matrix[row][col].setStyleSheet(f"background-color: {value_to_color(value)}")
        
window.setLayout(layout)
window.show()
app.exec()