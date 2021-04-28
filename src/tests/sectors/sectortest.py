import src.states
import src.scheme_utils
import src.manipulation
import http_framework.worldLoader
import src.my_utils

x1 = -4
z1 = 30
x2 = -8
z2 = 34
area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
worldSlice = http_framework.worldLoader.WorldSlice(area)  #_so area is chunks?

file_name = "sectors/sectortest"

state = src.states.State(worldSlice)
state.pathfinder.create_sectors(state.heightmaps["MOTION_BLOCKING_NO_LEAVES"],state.legal_actions)  # add tihs into State
hm = state.rel_ground_hm

src.scheme_utils.arrayXZ_to_schema(state.sectors, state.len_x, state.len_z, file_name + ".in")
state_x = -6 - area[0]
state_z = 31 - area[1]
state_y = hm[state_x][state_z] - 1

# remove diorite
src.states.set_state_block(state, state_x, state_y, state_z, "minecraft:air")
print(state.sectors)

# update sectors
state.step()

# store in file
src.scheme_utils.arrayXZ_to_schema(state.sectors, state.len_x, state.len_z, file_name + ".out")

# put it back
src.states.set_state_block(state, state_x, state_y, state_z, "minecraft:diorite")
state.step()
print(file_name+" complete")
