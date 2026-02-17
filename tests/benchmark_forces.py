from p_life.game import Game, update_particles1, update_particles2
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

# Benchmark 1
start = time.perf_counter()
for _ in range(n):
    pos1, vel1, types1 = update_particles1(pos1, vel1, types1, game.w, game.h, game.r_max, 0.01, game.friction, game.noise_strength, game.matrix)
print(pos1.shape)
end = time.perf_counter()

print("Numba + broadcasting:", end - start)

# Benchmark 2
start = time.perf_counter()
for _ in range(n):
    pos2, vel2, types2 = update_particles2(pos2, vel2, types2, game.w, game.h, game.r_max, 0.01, game.friction, game.noise_strength, game.matrix)
print(pos2.shape)
end = time.perf_counter()

print("Numba solely:", end - start)



