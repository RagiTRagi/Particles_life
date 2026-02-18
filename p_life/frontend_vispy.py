import numpy as np
from vispy import scene
from collections import deque

colour_type = np.array([
    [0.2, 0.2, 1.0, 1.0],  # blue
    [1.0, 1.0, 0.2, 1.0],  # yellow
    [0.2, 1.0, 0.2, 1.0],  # green
    [1.0, 0.2, 0.2, 1.0],  # red
], dtype=np.float32)

colour_type[:, :3] *= 0.8

def types_to_colors(types):
    types = np.asarray(types, dtype=np.int32)
    return colour_type[types % len(colour_type)]

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

        super().__init__(keys='interactive', bgcolor='black', size=(100, 100))
        self.unfreeze()

        self.game = game
        self.dt = 0.01

        self.view = self.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=None)
        self.view.camera.interactive = False
        self.view.camera.rect = (0, 0, world_width, world_height)

        self.history = deque(maxlen=6)
        self.blur = scene.Markers(parent=self.view.scene)
        self.blur.visible = False

        self.markers = scene.Markers(parent=self.view.scene)

        self.blur.order = 0
        self.markers.order = 1

        self.blur.set_gl_state(
            blend=True,
            depth_test=False,
            blend_func=('SRC_ALPHA', 'one_minus_src_alpha')  
        )
        self.markers.set_gl_state(blend=False, depth_test=False)

        snap = self.game.step(0.0)
        self.draw_snapshot(snap)
        self.freeze()

    def draw_snapshot(self, snap):

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
        raw_types = np.asarray(snap["types"])
        types = raw_types.astype(np.int32, copy=False)

        colors = types_to_colors(types)

        self.history.append(pos.copy())
        k = len(self.history)
        n = len(pos)

        if k < 2:
            self.blur.visible = False
        else:
            self.blur.visible = True

            blur_pos = np.vstack(list(self.history)).astype(np.float32, copy=False)

            blur_col = np.tile(colors, (k, 1)).astype(np.float32, copy=False)

            alphas = np.linspace(0.01, 0.05, k, dtype=np.float32)
            for i, a in enumerate(alphas):
                blur_col[i*n:(i+1)*n, 3] = a

            self.blur.set_data(pos=blur_pos, face_color=blur_col, size=7.0, symbol="disc")

        self.markers.set_data(pos=pos, face_color=colors, size=4.0, symbol="disc", edge_width=0.0)

    def step_and_draw(self):
        snap = self.game.step(self.dt)
        self.draw_snapshot(snap)
        self.update()
