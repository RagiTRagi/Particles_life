"""
VisPy for Particle Life frontend.

Renders particles as discs with a motion-afterimage

"""

from collections import deque

import numpy as np
from vispy import scene

# RGBA colors for particle types 0..3 (blue, yellow, green, red).

COLOR_TYPE = np.array(         
    [
        [0.2, 0.2, 1.0, 1.0],  # blue
        [1.0, 1.0, 0.2, 1.0],  # yellow
        [0.2, 1.0, 0.2, 1.0],  # green
        [1.0, 0.2, 0.2, 1.0],  # red
    ],
    dtype=np.float32,
)

COLOR_TYPE[:, :3] *= 0.8  # Darken RGB (keep alpha)


def types_to_colors(types: np.ndarray) -> np.ndarray:
    """
    Map particle type indices to RGBA colors.

    Parameters
    ----------
    types:
        Array-like of integer type indices (e.g. 0..3).

    Returns
    -------
    np.ndarray
        (n, 4) float32 array of RGBA colors.
    """
    types = np.asarray(types, dtype=np.int32)
    return COLOR_TYPE[types % len(COLOR_TYPE)]


class ParticleCanvas(scene.SceneCanvas):
    """
    VisPy canvas that draws particles from a Game snapshot.

    The Game object provides:
        step(dt) -> {"pos": (n, 2) array, "types": (n,) array}
    """
    def __init__(
        self,
        game,
        world_width: float,
        world_height: float,
        canvas_size: tuple[int, int] = (750, 500),
        dt: float = 1/60,
        shadow_len: int = 6,
    ) -> None:
        """
        Initialize a render canvas for particle snapshots.

        Parameters
        ----------
        game:
            Backend simulation object with a .step(dt) method.
        world_width/world_height:
            Size of the simulated world
        canvas_size:
            Canvas size in pixels (width, height).
        dt:
            Simulation timestep used by step_and_draw().
        shadow_len:
            Number of previous frames used for the motion shadow.
        """
        super().__init__(keys="interactive", bgcolor="black", size=canvas_size)
        self.unfreeze()  # set attributes on a frozen VisPy object

        self.game = game
        self.dt = float(dt)

        # ----- Scene + camera -----
        self.view = self.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=None)
        self.view.camera.interactive = False  # disable mouse zoom/pan
        self.view.camera.rect = (0, 0, world_width, world_height)

        # ----- Motion shadow storage -----
        # Array of a few previous positions for the afterimage creation.
        self.history: deque[np.ndarray] = deque(maxlen=int(shadow_len))
        
        # ----- Visuals -----
        # Shadow layer (draw first).
        self.blur = scene.Markers(parent=self.view.scene)
        self.blur.visible = False
        self.blur.order = 0

        # Main particles layer (draw on top).
        self.markers = scene.Markers(parent=self.view.scene)
        self.markers.order = 1

        # Additive blending for shadow and opaque main markers. 
        self.blur.set_gl_state(
            blend=True,
            depth_test=False,
            blend_func=("src_alpha", "one")
        )
        self.markers.set_gl_state(blend=False, depth_test=False)

        # Draw an initial frame. 
        snap = self.game.step(0.0)
        self.draw_snapshot(snap)

        self.freeze()  # prevents accidental attribute creation later

    def draw_snapshot(self, snap: dict) -> None:
        """
        Render a single snapshot from the simulation.

        Expected snap format:
            {"pos": (n, 2) array-like, "types": (n,) array-like ints}
        """
        # Current particle positions (float32 for the GPU).
        pos = np.asarray(snap["pos"], dtype=np.float32)

        # Current particle types (backend provides int 0..3).
        types = np.asarray(snap["types"], dtype=np.int32)

        # Per-particle RGBA colors.
        colors = types_to_colors(types)

        # ----- Build / update motion shadow -----
        self.history.append(pos.copy())
        k = len(self.history)
        n = len(pos)

        if k < 2: 
            # not enough history for a shadow
            self.blur.visible = False
        else:
            self.blur.visible = True

            # Combine all saved position frames (oldest -> newest) into one big array: (k*n, 2)
            blur_pos = np.vstack(self.history).astype(np.float32, copy=False)

            # Duplicate the current colors per-particle for each stored frame: (k*n, 4)
            blur_col = np.tile(colors, (k, 1)).astype(np.float32, copy=False)

            # Apply an alpha gradient so older frames for more transparency
            alphas = np.linspace(0.02, 0.12, k, dtype=np.float32)
            for i, a in enumerate(alphas):
                blur_col[i * n:(i + 1) * n, 3] = a

            # Slightly larger afterimage layer to create a soft motion shadow
            self.blur.set_data(
                pos=blur_pos,
                face_color=blur_col,
                size=10.0,
                symbol="disc",
            )

        # Draw the current particle positions on top 
        self.markers.set_data(
            pos=pos,
            face_color=colors,
            size=7.0,
            symbol="disc",
            edge_width=0.0,
        )

    def step_and_draw(self) -> None:
        """Step the simulation forward by dt, then render the new state.

        Intended to be called repeatedly to animate the system.
        """
        snap = self.game.step(self.dt)
        self.draw_snapshot(snap)
        self.update()
