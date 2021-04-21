import src.states
import src.scheme_utils
import src.manipulation
import src.simulation
import http_framework.worldLoader
import http_framework.interfaceUtils
import src.my_utils
import src.agent
import src.states
from pprint import pprint
import numpy as np

from src.linedrawing import get_line
from enum import Enum

# x1 = 77
# z1 = 46
# x2 = 152
# z2 = 144
# x1 = 15
# z1 = -42
# x2 = 62
# z2 = -99

# x1 = 0
# z1 = 0
# x2 = 62
# z2 = 65

# x1 = 2000
# z1 = 2000
# x2 = 2250
# z2 = 2250

x1 = 1500
z1 = 1500
x2 = 1600
z2 = 1600
# x2 = 1024
# z2 = 1024
# x2 = 11150
# z2 = 11150

# x1 = 10000
# z1 = 10000
# # x2 = -1058
# # z2 = -1024
# x2 = 10250
# z2 = 10250

area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
file_name = ""
# a = np.full((8, 8), 1.0)
# a *= 0.8
# print(np.where(a > 0.45))
# print(a)
clean_agents = "kill @e[type=minecraft:armor_stand,x={},y=64,z={},distance=..100]".format(str((x2+x1)/2), str((z2+z1)/2))
http_framework.interfaceUtils.runCommand(clean_agents)

# sim = src.simulation.Simulation(area, rendering_step_duration=0.0)
sim = src.simulation.Simulation(area, rendering_step_duration=0.05, is_rendering_each_step=False)
while sim.start() == False:
    sim.state.reset_for_restart()
# for x in range(len(sim.state.blocks)):
#     for z in range(len(sim.state.blocks[0][0])):
#         y = sim.state.static_ground_hm[x][z]
#         src.states.set_state_block(sim.state, x, y, z, "minecraft:oak_sign")
    # sim = src.simulation.Simulation(area, precomp_world_slice=sim.world_slice)#, precomp_legal_actions=sim.state.legal_actions, precomp_types=sim.state.types, precomp_sectors=sim.state.sectors, precamp_pathfinder=sim.state.pathfinder, rendering_step_duration=0.0, is_rendering_each_step=False)#, precomp_nodes=sim.state.nodes, precomp_node_pointers=sim.state.node_pointers)
    # sim = src.simulation.Simulation(area, rendering_step_duration=0.0, is_rendering_each_step=False)
    # sim = src.simulation.Simulation(area, rendering_step_duration=0.0,
    #                             is_rendering_each_step=False)
# sim.step(1)

## CONSTRUCTION
# for b in sim.state.construction:
#     x = b.center[0]
#     z = b.center[1]
#     y = sim.state.rel_ground_hm[x][z] + 1
#     # sim.state.set_block(x,y,z,"minecraft:gold_block")
#     if src.my_utils.TYPE.WATER.name in b.get_type():
#         pass
        # print("water found!")

print("road_segs is ")
print(sim.state.road_segs)
sim.step(300, is_rendering=True)
for built in sim.state.built:
    # src.states.set_state_block(sim.state, built.center[0], sim.state.rel_ground_hm[built.center[0]][built.center[1]]+11, built.center[1], 'minecraft:red_wool')
    pass
for xz,y in sim.state.built_heightmap.items():
    x, z = xz
    # src.states.set_state_block(sim.state,x,y+1,z, 'minecraft:diorite')
for x in range(sim.state.len_x):
    for z in range(sim.state.len_z):
        pass
        # src.states.set_state_block(sim.state,x,sim.state.rel_ground_hm[x][z],z, 'minecraft:pumpkin')


## ROADS
for r in sim.state.roads:
    if r in sim.state.construction:
        # sim.state.construction.discard(r)
        pass
    x = r.center[0]
    z = r.center[1]
    y = sim.state.rel_ground_hm[x][z] + 1
    sim.state.set_block(x,y,z,"minecraft:redstone_block")
sim.step(1, is_rendering=True)
# pprint(sim.state.rel_ground_hm)
# print(sim.state.static_ground_hm)
# print(sim.state.sectors)
print(src.agent.Agent.shared_resources)
print("semibends is "+str(sim.state.semibends))
print("bends is "+str(sim.state.bends))
print("bendcoint is "+str(sim.state.bendcount))
# sim.is_rendering_each_step = True
# sim.step(is_rendering=True)
