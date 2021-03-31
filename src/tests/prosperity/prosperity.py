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

# x1 = 77
# z1 = 46
# x2 = 152
# z2 = 144
x1 = -10
z1 = 64
x2 = -73
z2 = 134

area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
file_name = ""
# a = np.full((8, 8), 1.0)
# a *= 0.8
# print(np.where(a > 0.45))
# print(a)
clean_agents = "kill @e[type=minecraft:armor_stand,x={},y=64,z={},distance=..100]".format(str((x2+x1)/2), str((z2+z1)/2))
http_framework.interfaceUtils.runCommand(clean_agents)

sim = src.simulation.Simulation(area, rendering_step_duration=0.0)
# ag = src.agent.Agent(sim.state, 50, 27, sim.state.rel_ground_hm, "Prof")
# sim.add_agent(ag)
# ag.set_motive(ag.Motive.LOGGING)
# for node in sim.state.nodes[(13,13)].range:
#     y = sim.state.rel_ground_hm[node.center[0]][ node.center[1]] - 1
#     sim.state.set_block(node.center[0], y,node.center[1], "minecraft:white_wool")
# #

# for center in sim.state.nodes:
#     pass

sim.step(1)
# print("lots")
# print(sim.state.lots)
# print("built")
# print(sim.state.construction)
# show building spots

for r in sim.state.roads:
    if r in sim.state.construction:
        sim.state.construction.discard(r)
    x = r.center[0]
    z = r.center[1]
    y = sim.state.rel_ground_hm[x][z] + 1
    sim.state.set_block(x,y,z,"minecraft:redstone_block")


for b in sim.state.construction:
    x = b.center[0]
    z = b.center[1]
    y = sim.state.rel_ground_hm[x][z] + 1
    sim.state.set_block(x,y,z,"minecraft:gold_block")
print("road_segs")
print(sim.state.road_segs)
sim.step(1)
