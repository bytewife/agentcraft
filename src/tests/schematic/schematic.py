import src.states
import src.scheme_utils
import src.manipulation
import src.simulation
import http_framework.worldLoader
import src.my_utils
import src.agent
import numpy as np
from enum import Enum

x1 = 0
z1 = 0
x2 = 50
z2 = 50
area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
file_name = "schematic"

sim = src.simulation.Simulation(area)


print(file_name+" complete")
hm = sim.state.rel_ground_hm
x = 10
z = 30
src.scheme_utils.place_schematic_in_state(sim.state, "building", x, hm[x][z], z, built_arr=[], dir_x=-1, dir_z = 1, rot=1)
sim.step(10, True, 1.0)
