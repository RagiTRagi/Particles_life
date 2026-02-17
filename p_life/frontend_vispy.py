import numpy as np
from vispy import scene

colour_type = np.array([
    [0.2, 0.2, 1.0, 1.0],  # blue
    [1.0, 1.0, 0.2, 1.0],  # yellow
    [0.2, 1.0, 0.2, 1.0],  # green
    [1.0, 0.2, 0.2, 1.0],  # red
], dtype=np.float32)

def types_to_colors(types):
    types = list(types)  
    colors = []

    for t in types:
        i = t % len(colour_type) 
        colors.append(colour_type [i])

    return np.array(colors, dtype=np.float32)

class ParticleCanvas(scene.SceneCanvas):
    def __init__(self, game, world_width, world_height):
        super().__init__(keys='interactive', bgcolor='black', size=(900, 700))
        self.unfreeze()

        self.game = game
        self.dt = 1/60

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
            raise TypeError("types must be integer IDs")

        colors = types_to_colors(types)
        self.markers.set_data(pos=pos, face_color=colors, size=3.0)

    def step_and_draw(self):
        snap = self.game.step(self.dt)
        self.draw_snapshot(snap)
        self.update()
