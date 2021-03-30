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

x1 = -10
z1 = 65
x2 = -54
z2 = 114
area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
file_name = ""
# a = np.full((8, 8), 1.0)
# a *= 0.8
# print(np.where(a > 0.45))
# print(a)
sim = src.simulation.Simulation(area, rendering_step_duration=0.2)
ag = src.agent.Agent(sim.state, 0, 2, sim.state.rel_ground_hm, "Prof")
sim.add_agent(ag)
ag.set_motive(ag.Motive.LOGGING)
# for node in sim.state.nodes[(13,13)].range:
#     y = sim.state.rel_ground_hm[node.center[0]][ node.center[1]] - 1
#     sim.state.set_block(node.center[0], y,node.center[1], "minecraft:white_wool")
# #

# for center in sim.state.nodes:
#     pass

sim.step(60)


node = sim.state.nodes[sim.state.node_pointers[23][5]]
print(sim.state.prosperity[node.center[0]][node.center[1]])  # eq 60
