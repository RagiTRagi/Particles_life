import numpy as np
from vispy import app, scene
from game import Game

TYPE_COLORS = np.array([
    [1.0, 0.2, 0.2, 1.0],  # rot
    [0.2, 1.0, 0.2, 1.0],  # grün
    [0.2, 0.2, 1.0, 1.0],  # blau
    [1.0, 1.0, 0.2, 1.0],  # gelb
], dtype=np.float32)

def types_to_colors(types):

    """
        Initializes particle positions, velocities, and types.
        
        Particles are randomly distributed across the world with zero initial velocity.
        Each particle is randomly assigned one of four types (0-3).
        
        Args:
            n (int): Number of particles to create
            width (float): Width of the world for position initialization
            height (float): Height of the world for position initialization
        
        Returns:
            tuple: Contains (positions, velocities, types) where:
                - positions: np.ndarray of shape (n, 2) with random x, y coordinates
                - velocities: np.ndarray of shape (n, 2), initialized to zeros
                - types: np.ndarray of shape (n,) with random integers 0-3
        """
    
    types = list(types)  
    colors = []

    for t in types:
        i = t % len(TYPE_COLORS) 
        colors.append(TYPE_COLORS[i])

    return np.array(colors, dtype=np.float32)

class ParticleCanvas(scene.SceneCanvas):

    """
    Vispy-based visualization canvas for the Particle Life simulation.
    
    Class creates an interactive window that displays the particle simulation
    in real-time. It uses Vispy's SceneCanvas for hardware-accelerated rendering
    and provides pan/zoom camera controls for navigation.
    
    Attributes:
        game (Game): The Game instance being visualized
        dt (float): Time step passed to the simulation at each frame
        view (ViewBox): Vispy view container for the scene
        markers (Markers): Vispy visual object for rendering particles as points
        timer (Timer): Vispy timer that triggers updates at a fixed framerate
    """

    def __init__(self, game, world_width, world_height):

        """
        Initializes the visualization canvas.
        
        Sets up the window, camera, particle markers, and update timer. The camera
        is configured to show the entire world space with pan and zoom controls.
        
        Args:
            game (Game): The Game instance to visualize
            world_width (float): Width of the simulation world (for camera range)
            world_height (float): Height of the simulation world (for camera range)
        """

        super().__init__(keys='interactive', bgcolor='black', size=(900, 700))
        self.unfreeze()

        self.game = game
        self.dt = 0.01

        self.view = self.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=1)
        self.view.camera.set_range(x=(0, world_width), y=(0, world_height))

        self.markers = scene.Markers(parent=self.view.scene)
        snap = self.game.step(0.0)
        self._draw_snapshot(snap)
        self.timer = app.Timer(interval=1/120, connect=self.on_timer, start=True)

        self.freeze()

    def _draw_snapshot(self, snap):

        """
        Updates the visual representation with current particle states.
        
        Takes a simulation snapshot (positions and types) and updates the
        marker visual to reflect the current state of all particles.
        
        Args:
            snap (dict): Simulation snapshot containing:
                - "pos": Particle positions as np.ndarray, shape (N, 2)
                - "types": Particle types as np.ndarray, shape (N,)
        """

        pos = np.asarray(snap["pos"], dtype=np.float32)
        types = np.asarray(snap["types"], dtype=int)

        colors = types_to_colors(types)

        self.markers.set_data(
            pos=pos,
            face_color=colors,
            size=3.0,
        )


    def on_timer(self, event):

        """
        Timer callback that advances and renders the simulation.
        
        This method is called repeatedly by the Vispy timer (120 times per second).
        Each call advances the simulation by one time step and updates the display.
        
        Args:
            event: Vispy timer event (not used but required by callback signature)
        """
        
        snap = self.game.step(self.dt)
        self._draw_snapshot(snap)


if __name__ == "__main__":

    game = Game(
        n=10000,
        world_width=100.0,
        world_height=100.0,
        r_max=5.0,
    )

    canvas = ParticleCanvas(game, world_width=game.w, world_height=game.h)
    canvas.show()

    app.run()