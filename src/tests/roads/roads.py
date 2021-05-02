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
x2 = -33
z2 = 64
area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
file_name = ""
sim = src.simulation.Simulation(area)

# print(sim.state.nodes)
# print(sim.state.prosperities)
sim.state.init_main_st()
print(sim.state.roads)

# range testing
print("neighbors")
# print(sim.state.nodes[(10,10)].get_neighbors_positions())
# print(len(sim.state.nodes[(13,13)].get_ranges_positions()))
for node in sim.state.nodes(13,13).range:
    y = sim.state.rel_ground_hm[node.center[0]][ node.center[1]] - 1
    sim.state.set_block(node.center[0], y,node.center[1], "minecraft:white_wool")
#

# sim.state.prosperities[0][0] = 1

# print(sim.state.prosperities)
for center in sim.state.nodes:
    pass

# sim.state.create_road((8,20), (15,2), src.my_utils.Type.MAJOR_ROAD.name)
# sim.state.get_closest_point(sim.state.nodes[sim.state.node_pointers[(0,8)]], [], sim.state.roads, src.my_utils.Type.MAJOR_ROAD.name, False)
# sim.state.create_road((0,8), (13,13), src.my_utils.Type.MAJOR_ROAD.name)

sim.step()
# print(a)
# print(file_name+" complete")
