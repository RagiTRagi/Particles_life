from p_life.game import Game, update_particles
from p_life_old_version.game import update_particles_old
import time

game = Game(
        n=20,
        world_width=100.0,
        world_height=100.0,
        r_max=5.0,
    )
pos, vel, types = game.init_particles(15000, 100.0, 100.0)

# Equal starting data
pos1, vel1, types1 = pos.copy(), vel.copy(), types.copy()
pos2, vel2, types2 = pos.copy(), vel.copy(), types.copy()


n = 250

# Benchmark numba version
start = time.perf_counter()
for _ in range(n):
    pos1, vel1, types1 = update_particles(pos1, vel1, types1, game.w, game.h, game.r_max, 0.01, game.friction, game.noise_strength, game.matrix)

end = time.perf_counter()

print("Numba version:", end - start)

# Benchmark hybrid version
start = time.perf_counter()
for _ in range(n):
    pos2, vel2, types2 = update_particles_old(pos2, vel2, types2, game.w, game.h, game.r_max, 0.01, game.friction, game.noise_strength, game.matrix)

end = time.perf_counter()

print("Hybrid version:", end - start)



