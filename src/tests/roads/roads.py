import src.states
import src.scheme_utils
import src.manipulation
import src.simulation
import http_framework.worldLoader
import http_framework.interfaceUtils
import src.my_utils
import src.agent
import src.states
from src.linedrawing import get_line
from enum import Enum

x1 = -10
z1 = 35
x2 = -31
z2 = 62
area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
file_name = ""
sim = src.simulation.Simulation(area)
# print(sim.state.prosperities)
sim.state.prosperities[0][0] = 1
print(sim.state.prosperities)
for center in sim.state.nodes:
    pass
a = get_line([0,1], [4,9])
for b in a:
    src.states.set_state_block(sim.state, b[0], 1, b[1], "minecraft:oak_log")
sim.step()
print(a)
# print(file_name+" complete")
