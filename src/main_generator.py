# import random  # standard python lib for pseudo random

from src.http_framework.worldLoader import WorldSlice
from src.my_utils import *
from src.scheme_utils import *
from src.states import *
from visualizeMap import *
from block_manipulation import *
from simulation import *
import noise

############## debug
def global_to_state_coords(world_x, world_z, build_area):
    # I want to take a global coord and change it to state y
    x = world_x - build_area[0]
    z = world_z - build_area[1]
    return (x, z)

def get_state_surface_y(state_x, state_z, state_heightmap, state_y):
    return state_heightmap[state_x][state_z] - state_y
#############

areaFlex = [0, 0, 32, 32] # default build area

# Do we send blocks in batches to speed up the generation process?

# see if a build area has been specified
# you can set a build area in minecraft using the /setbuildarea command
buildArea = requestBuildArea()
if buildArea != -1:
    x1 = buildArea["xFrom"]
    z1 = buildArea["zFrom"]
    x2 = buildArea["xTo"]
    z2 = buildArea["zTo"]
    areaFlex = [x1, z1, x2-x1, z2-z1]

area = correct_area(areaFlex)

# load the world data
# this uses the /chunks endpoint in the background
worldSlice = WorldSlice(area)  #_so area is chunks?

def noise_place(area):
    # a = "minecraft:oak_log"
    a = "minecraft:gold_block"
    b = "minecraft:diamond_block"
    for x in range(area[0], area[2]):
        for z in range(area[1], area[3]):
            n = noise.snoise2(x, z)
            block = a
            if(n > 0): block = b
            setBlock(x, 100, z, block, 200)
    sendBlocks()

# noise_place(area)'

# noise_place(area)
# download_schematic(143, 101, -143, 5, 5, 5, -1, 1, 1, "nethercube.txt")
# download_schematic(116, 101, -150, 1, 4, 3, 1, 1, 1, "nethercude.txt")
# place_schematic("nethercube.txt", 143, 101, -128)

# print(worldSlice.getBlockAt((0,101,0)))  ## Get sign Properties. Here's how you access block data from client-downloaded data



# visualizeMap.visualize_topography(area)
a = worldSlice.get_surface_blocks_from(*(0, 0, 2, 2))


# download_schematic(13, 101, 9, 10, 103, 12, "test.txt")
sim = Simulation(area)

place_schematic_in_state(sim.state, "./test.txt", 0, 25, 0, dir_y=1)
# print(changed_blocks)
# save_state(state, state_y, "../hope.txt")
# load_state("../hope.txt", area[0], area[1])
# visualize_topography(area, state, state_heightmap, state_y)

## tree tests
check_x = 5
check_z = 7
tree_y = get_state_surface_y(*global_to_state_coords( check_x, check_z, area), state_y=sim.state.world_y, state_heightmap=sim.state.heightmap)
if is_log(sim.state, check_x, tree_y, check_z):
    cut_tree_at(sim.state, check_x, tree_y, check_z)
    # trim_leaves(state, check_x, tree_y, check_z-1)

sim.state.save_state(sim.state, "hope.txt")
sim.state.load_state("hope.txt", area[0], area[1])


print("done")
