# import random  # standard python lib for pseudo random

from interfaceUtils import *
from worldLoader import WorldSlice
from my_utils import *
from scheme_utils import *
import numpy as np
import noise


set_USE_BATCHING(True)

area = [0, 0, 128, 128] # default build area

# Do we send blocks in batches to speed up the generation process?

# see if a build area has been specified
# you can set a build area in minecraft using the /setbuildarea command
buildArea = requestBuildArea()
if buildArea != -1:
    x1 = buildArea["xFrom"]
    z1 = buildArea["zFrom"]
    x2 = buildArea["xTo"]
    z2 = buildArea["zTo"]
    # print(buildArea)
    area = [x1, z1, x2-x1, z2-z1]

# print("Build area is at position %s, %s with size %s, %s" % area)
correct_area(area)

# load the world data
# this uses the /chunks endpoint in the background
worldSlice = WorldSlice(area)  #_so area is chunks?

arr = []

area = [92, -114, 150, -160] # default build area
correct_area(area)

def noise_place(area):
    # a = "minecraft:oak_log"
    a = "minecraft:gold_block"
    b = "minecraft:diamond_block"
    for x in range(area[0], area[2]):
        for z in range(area[1], area[3]):
            n = noise.snoise2(x, z)
            print(n)
            block = a
            if(n > 0): block = b
            setBlock(x, 100, z, block)
            # print(blockBuffer)
    sendBlocks()


# noise_place(area)
# download_schematic(143, 101, -143, 5, 5, 5, -1, 1, 1, "nethercube.txt")
download_schematic(116, 101, -150, 1, 4, 3, 1, 1, 1, "test.txt")
place_schematic("test.txt", 112, 101, -143)
print("done")
