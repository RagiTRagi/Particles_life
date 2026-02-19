# Particle Life:

A Python software application that simulates a **dynamic particle system** in which thousands of particles interact based on predefined rules. The **simulation** includes different particle types with unique properties and interaction patterns, demonstrating emergent behavior and visual complexity. 

# Documentation for users

## Requirements

 - Python 3.9+
 - Anaconda (recommended)


## Installation and running the Simulation via Anaconda Prompt

### 1. Installation 
```
git clone https://github.com/RagiTRagi/Particles_life.git
cd Particles_life
```
### 2. Creating an Environment
```
conda create --name particle_life python=3.12 -y
conda activate particle_life
```
### 3. Install dependencies 
```
pip install -r requirements.txt
```
### 4. Starting the Simulation
```
python main.py
```
This installs and starts the particle simulation UI.

## Controls 

- Click a matrix button to select a particle interaction
- Use the slider to adjust the selected interaction strength.
- Adjust friction and noise with the spin boxes
- Use Pause/Resume to stop and continue the simulation
- To Reset the positions of the particles, use the Reset Button

## Troubleshooting guide

- If the UI does not open, verfiy you meet the requirements above
- Make sure to run the command from the project root
- Clear all local files stored at Particles_life\p_life\__pycache__ 

# Documentation for developers

## Project Architecture 

<img width="1461" height="931" alt="particles_life2 drawio" src="https://github.com/user-attachments/assets/496cb1ec-3967-403b-a569-8330d9cc669a" />

## Core Components

### 1. Game Logic ([p_life/game.py](p_life/game.py))

**`Game` class** - Manages the particle simulation:
- Stores particle positions, velocities, and types (4 types: blue, yellow, green, red)
- 4×4 interaction matrix defines attraction/repulsion between particle types
- Physics parameters: friction, noise, world size

**Force Calculation** - Optimized with Numba for performance:
- Uses grid-based spatial partitioning for efficient collision detection
- Two force zones:
  - **Close range** (< 30%): Strong repulsion to prevent overlap
  - **Far range** (> 30%): Matrix-based attraction/repulsion
- Torus world: particles wrap around at edges

**Performance**: Numba JIT compilation with parallel execution for increased performance

### 2. Visualization ([p_life/frontend_vispy.py](p_life/frontend_vispy.py))

**`ParticleCanvas` class** - Renders particles with OpenGL:
- Color-coded particle types
- Motion blur effect using position history
- GPU-accelerated rendering via VisPy

### 3. User Interface ([p_life/gui.py](p_life/gui.py))

**Control Panel** (PySide6/Qt):
- 4×4 matrix of buttons for particle interactions
- Slider to adjust selected interaction strength (-50 to +50)
- Friction and noise controls
- Pause/Resume button
- Reset Button

**Real-time Updates**: Changes to interaction matrix immediately affect the simulation

## Key Technologies

- **NumPy** - Fast array operations
- **Numba** - JIT compilation and parallelization
- **VisPy** - GPU-accelerated OpenGL visualization
- **PySide6** - Qt6 user interface

# Tasks:

Developing a project - *Biology-inspired algorithms - emergent behavior* - for the <br> HSD Course: *Data Science und KI Infrastrukturen, Wintersemester 2025-2026* <br> Supervised by Prof. Dr. Florian Huber


