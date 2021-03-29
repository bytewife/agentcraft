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
# print(sim.state.prosperities)
for center in sim.state.nodes:
    pass
# a = get_line([0,1], [4,9])
# print(a)
# print(sim.state.node_pointers[0][0])
# sim.state.roads.append((10, 10))
sim.state.create_road((8,20), (15,2), src.my_utils.Type.MAJOR_ROAD.name)
sim.state.get_closest_point(sim.state.nodes[sim.state.node_pointers[(0,8)]], [], sim.state.roads, src.my_utils.Type.MAJOR_ROAD.name, False)
sim.state.create_road((0,8), (13,13), src.my_utils.Type.MAJOR_ROAD.name)

sim.step()
# print(a)
# print(file_name+" complete")
