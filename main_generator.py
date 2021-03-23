# import random  # standard python lib for pseudo random

from src.http.worldLoader import WorldSlice
from src.my_utils import *
from src.scheme_utils import *
from src.save_states import *
import noise


areaFlex = [0, 0, 64, 64] # default build area

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

area = (0,0,128,128)
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
# place_schematic('test.txt',10, 101, 29)
state, start_y = get_state(worldSlice)
# save_state(state, start_y)
load_state("save_1.txt", area[0], area[1])

print("done")
