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
    types = list(types)  
    colors = []

    for t in types:
        i = t % len(TYPE_COLORS) 
        colors.append(TYPE_COLORS[i])

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
        self._draw_snapshot(snap)
        self.timer = app.Timer(interval=1/120, connect=self.on_timer, start=True)

        self.freeze()

    def _draw_snapshot(self, snap):
        pos = np.asarray(snap["pos"], dtype=np.float32)
        types = np.asarray(snap["types"], dtype=int)

        colors = types_to_colors(types)

        self.markers.set_data(
            pos=pos,
            face_color=colors,
            size=3.0,
        )


    def on_timer(self, event):
        snap = self.game.step(self.dt)
        self._draw_snapshot(snap)


if __name__ == "__main__":

    game = Game(
        n=30000,
        world_width=100.0,
        world_height=100.0,
        r_max=5.0,
    )

    canvas = ParticleCanvas(game, world_width=game.w, world_height=game.h)
    canvas.show()

    app.run()