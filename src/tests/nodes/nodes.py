import src.states
import src.scheme_utils
import src.manipulation
import src.simulation
import http_framework.worldLoader
import src.my_utils
import src.agent
from enum import Enum
from math import floor, ceil

# 0 > chunk 0
# 0 > chunk 0
# 16 > chunk 1
# for x in range(32, 65):
#     for z in range(32,65):
#         rect = (-15, 0, 14, 17)
#         lowerMultOf16X = floor(rect[0]) >> 4
#         lowerMultOf16Z = floor(rect[1]) >> 4
#         upperMultOf16X = floor(rect[2]) >> 4
#         upperMultOf16Z = floor(rect[3]) >> 4
#
#         dx = upperMultOf16X - lowerMultOf16X + 1 # + 1 because of range function usage
#         # dz = upperMultOf16Z - lowerMultOf16Z
#         # dz = upperMultOf16Z - lowerMultOf16Z
#         chunkRect = (rect[0] >> 4, rect[1] >> 4, ((rect[0] + rect[2] - 1) >> 4) - (
#                 rect[0] >> 4) + 1, ((rect[1] + rect[3] - 1) >> 4) - (rect[1] >> 4) + 1)
#         # a = (lowerMultOf16X, lowerMultOf16Z, upperMultOf16Z - lowerMultOf16Z)
#         print(dx)
#         print(chunkRect)
#         # print(a)
#         # print(chunkRect)
#         if a != chunkRect:
#             print("wrong")
#             exit(2)

##
x1 = -10
z1 = 21
x2 = -23
z2 = 34
area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
sim = src.simulation.Simulation(area)
# print(sim.state.abs_ground_hm)
# sim.step(16, True, 1.0)