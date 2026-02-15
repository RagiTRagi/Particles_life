import numpy as np
from game import Game
from vispy import scene

colour_type = np.array([
    [0.2, 0.2, 1.0, 1.0],  # blau (0)
    [1.0, 1.0, 0.2, 1.0],  # gelb (1)
    [0.2, 1.0, 0.2, 1.0],  # grün (2)
    [1.0, 0.2, 0.2, 1.0],  # rot  (3)
], dtype=np.float32)

type_map = {"a": 0, "b": 1, "c": 2, "d": 3}


def types_to_colors(types):
    types = list(types)  
    colors = []

    for t in types:
        i = t % len(colour_type) 
        colors.append(colour_type[i])

    return np.array(colors, dtype=np.float32)

class ParticleCanvas(scene.SceneCanvas):
    def __init__(self, game, world_width, world_height):
        super().__init__(keys='interactive', bgcolor='black', size=(900, 700))
        self.unfreeze()

        self.game = game
        self.dt = 0.01

        self.view = self.central_widget.add_view()
        self.view.camera = scene.PanZoomCamera(aspect=1)
        self.view.camera.set_range(x=(0, world_width), y=(0, world_height))

        self.markers = scene.Markers(parent=self.view.scene)
        snap = self.game.step(0.0)
        self.draw_snapshot(snap)
        self.freeze()

    def draw_snapshot(self, snap):
        pos = np.asarray(snap["pos"], dtype=np.float32)
        raw_types = np.asarray(snap["types"])

        if raw_types.dtype.kind in "iu":
            types = raw_types.astype(np.int32)
        else:
            def norm(t):
                if isinstance(t, (bytes, np.bytes_)): # byte -> string
                    t = t.decode("utf-8", errors="ignore")
                return str(t).strip().lower()

            types = np.array([type_map[norm(t)] for t in raw_types], dtype=np.int32)

        colors = types_to_colors(types)
        self.markers.set_data(pos=pos, face_color=colors, size=3.0)

    def step_and_draw(self):
            snap = self.game.step(self.dt)
            self.draw_snapshot(snap)
            self.update()



