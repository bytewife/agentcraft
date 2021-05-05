import src.states
import src.scheme_utils
import src.manipulation
import src.simulation
import http_framework.worldLoader
import http_framework.interfaceUtils
import src.my_utils
import src.agent
import src.states
import numpy as np
from src.linedrawing import get_line
from enum import Enum

# jungle
# x1 = 4000
# z1 = 4000
# x2 = 3900
# z2 = 4100

x1 = 5100
z1 = 5100
x2 = 5000
z2 = 5200

area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
file_name = ""
clean_agents = "kill @e[type=minecraft:armor_stand,x={},y=64,z={},distance=..100]".format(str((x2+x1)/2), str((z2+z1)/2))
http_framework.interfaceUtils.runCommand(clean_agents)

frame_duration = 0.0
sim = src.simulation.Simulation(area, rendering_step_duration=frame_duration, is_rendering_each_step=False)

print("road_segs is ")
print(sim.state.road_segs)
timesteps = 300
sim.run_with_render(300)

## ROADS
# for r in sim.state.roads:
#     if r in sim.state.construction:
#         # sim.state.construction.discard(r)
#         pass
#     x = r.center[0]
#     z = r.center[1]
#     y = sim.state.rel_ground_hm[x][z] + 1
#     sim.state.set_block(x,y,z,"minecraft:redstone_block")

## CONSTRUCTION
# for b in sim.state.construction:
#     x = b.center[0]
#     z = b.center[1]
#     y = sim.state.rel_ground_hm[x][z] + 1
#     sim.state.set_block(x,y,z,"minecraft:gold_block")
    # if src.my_utils.TYPE.WATER.name in b.get_type():
    #     pass

#HEIGHTMAP
# for x in range(len(sim.state.blocks_arr)):
#     for z in range(len(sim.state.blocks_arr[0][0])):
#         # y = sim.state.static_ground_hm[x][z]
#         # sim.state.set_block(x, y, z, "minecraft:oak_sign")
#         y = sim.state.rel_ground_hm[x][z]
#         sim.state.set_block(x, y, z, "minecraft:oak_sign")

sim.state.step(1)

# pprint(sim.state.rel_ground_hm)
# print(sim.state.static_ground_hm)
# print(sim.state.sectors)
print(src.agent.Agent.shared_resources)
print("done")
# sim.is_rendering_each_step = True
# sim.step(is_rendering=True)
