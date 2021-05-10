import src.states
import src.scheme_utils
import src.manipulation
import http_framework.worldLoader
import src.my_utils
import src.simulation

x1 = -3
z1 = 47
x2 = -8
z2 = 52
area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)

sim = src.simulation.Simulation(area)

hm_base = sim.state.heightmaps["MOTION_BLOCKING_NO_LEAVES"].copy()
hm_abs = sim.state.abs_ground_hm.copy()
hm_rel = sim.state.rel_ground_hm.copy()
hm_abs = sim.state.abs_ground_hm.copy()
print(hm_base)
for x in range(len(hm_base)):
    for z in range(len(hm_base[0])):
        sim.state.update_heightmaps()
print("base original:")
print(hm_base)
print("base updated:")
print(sim.state.heightmaps["MOTION_BLOCKING_NO_LEAVES"])

print("abs original:")
print(hm_abs)
print("abs updated:")
print(sim.state.abs_ground_hm)

print("rel original:")
print(hm_rel)
print("rel updated:")
print(sim.state.rel_ground_hm)

print("############### CHANGING BLOCK ###################")

x = 0
z = 4
print ("befores:")
print(sim.state.heightmaps["MOTION_BLOCKING_NO_LEAVES"][x][z])
print(sim.state.abs_ground_hm[x][z])
print(sim.state.rel_ground_hm[x][z])
src.states.set_state_block(sim.state, x, 1, z, "minecraft:air")
sim.state.step()
print ("afters (should be 1 lower.:")
print(sim.state.heightmaps["MOTION_BLOCKING_NO_LEAVES"][x][z])
print(sim.state.abs_ground_hm[x][z])
print(sim.state.rel_ground_hm[x][z])
src.states.set_state_block(sim.state, x, 1, z, "minecraft:diorite")
sim.state.step()
# update sectors

# store in file

# put it back
