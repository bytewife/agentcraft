import src.states
import src.scheme_utils
import src.manipulation
import src.simulation
import http_framework.worldLoader
import src.my_utils
import src.agent
from enum import Enum

x1 = -4
z1 = 36
x2 = -8
z2 = 43
area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
worldSlice = http_framework.worldLoader.WorldSlice(area)  #_so area is chunks?

file_name = "move_to_log"

sim = src.simulation.Simulation(area)
print(sim.state.heightmaps["MOTION_BLOCKING_NO_LEAVES"])
sim.state.update_heightmaps(0,0)
print(sim.state.heightmaps["MOTION_BLOCKING_NO_LEAVES"])
print(sim.state.abs_ground_hm)
# print(sim.state.abs_ground_hm)
# sim.state.pathfinder.create_sectors(sim.state.heightmaps["MOTION_BLOCKING_NO_LEAVES"],sim.state.legal_actions)  # add tihs into State
# ag = src.agent.Agent(sim.state, 0, 0, sim.state.heightmaps["MOTION_BLOCKING"], "Jonah")
# sim.add_agent(ag)
# ag.set_motive(ag.Motive.LOGGING)
# print(ag.path)
# sim.step(10, True, 1.0)

# state_x = -6 - area[0]
# state_z = 31 - area[1]
# state_y = hm[state_x][state_z] - 1

# store in file
# src.scheme_utils.arrayXZ_to_schema(state.pathfinder.sectors, state.len_x, state.len_z, file_name + ".out")
#
# # put it back
# src.manipulation.set_state_block(state, state_x, state_y, state_z, "minecraft:diorite")
# state.render()
print(file_name+" complete")
