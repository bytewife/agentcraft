import src.states
import src.scheme_utils
import src.manipulation
import src.simulation
import http_framework.worldLoader
import src.my_utils
import src.agent
from enum import Enum

x1 = -3
z1 = 36
x2 = -8
z2 = 44
area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
worldSlice = http_framework.worldLoader.WorldSlice(area)  #_so area is chunks?

file_name = ""

sim = src.simulation.Simulation(area)

ag = src.agent.Agent(sim.state, 1, 0, sim.state.rel_ground_hm, "Jonah")
sim.add_agent(ag)
la = sim.state.legal_actions
ag.set_motive(ag.Motive.LOGGING)
sim.step(16, True, 1.0)

# state_x = -6 - area[0]
# state_z = 31 - area[1]
# state_y = hm[state_x][state_z] - 1

# store in file
# src.scheme_utils.arrayXZ_to_schema(state.sectors, state.len_x, state.len_z, file_name + ".out")
#
# # put it back
# src.manipulation.set_state_block(state, state_x, state_y, state_z, "minecraft:diorite")
# state.render()
print(file_name+" complete")
