import random  # standard python lib for pseudo random

import mapUtils
import interfaceUtils
from worldLoader import WorldSlice

# x position, z position, x size, z size
area = (0, 0, 128, 128) # default build area

# Do we send blocks in batches to speed up the generation process?
USE_BATCHING = True

# see if a build area has been specified
# you can set a build area in minecraft using the /setbuildarea command
buildArea = interfaceUtils.requestBuildArea()
if buildArea != -1:
    x1 = buildArea["xFrom"]
    z1 = buildArea["zFrom"]
    x2 = buildArea["xTo"]
    z2 = buildArea["zTo"]
    # print(buildArea)
    area = (x1, z1, x2-x1, z2-z1)

print("Build area is at position %s, %s with size %s, %s" % area)

# load the world data
# this uses the /chunks endpoint in the background
worldSlice = WorldSlice(area)  #_so area is chunks?
# heightmap = worldSlice.heightmaps["MOTION_BLOCKING"]
# heightmap = worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
# heightmap = worldSlice.heightmaps["OCEAN_FLOOR"]
# heightmap = worldSlice.heightmaps["WORLD_SURFACE"]

# caclulate a heightmap that ignores trees:
heightmap = mapUtils.calcGoodHeightmap(worldSlice)

# show the heightmap as an image
# mapUtils.visualize(heightmap, title="heightmap")

# define a function for easier heightmap access
# heightmap coordinates are not equal to world coordinates!
def heightAt(heightmap, x, z):
    return heightmap[(x - area[0], z - area[1])]

# a wrapper function for setting blocks
def setBlock(x, y, z, block):
    if USE_BATCHING:
        interfaceUtils.placeBlockBatched(x, y, z, block, 100)
    else:
        interfaceUtils.setOneBlock(x, y, z, block)

# build a fence around the perimeter
for x in range(area[0], area[0] + area[2]):
    z = area[1]
    y = heightAt(x, z)
    setBlock(x, y-1, z, "cobblestone")
    setBlock(x, y,   z, "oak_fence")
for z in range(area[1], area[1] + area[3]):
    x = area[0]
    y = heightAt(x, z)
    setBlock(x, y-1, z, "cobblestone")
    setBlock(x, y  , z, "oak_fence")
for x in range(area[0], area[0] + area[2]):
    z = area[1] + area[3] - 1
    y = heightAt(x, z)
    setBlock(x, y-1, z, "cobblestone")
    setBlock(x, y,   z, "oak_fence")
for z in range(area[1], area[1] + area[3]):
    x = area[0] + area[2] - 1
    y = heightAt(x, z)
    setBlock(x, y-1, z, "cobblestone")
    setBlock(x, y  , z, "oak_fence")

# function that builds a small house
def buildHouse(x1, y1, z1, x2, y2, z2):
    # floor
    for x in range(x1, x2):
        for z in range(z1, z2):
            setBlock(x, y1, z, "cobblestone");
    # walls
    for y in range(y1+1, y2):
        for x in range(x1 + 1, x2 - 1):
            setBlock(x, y, z1, "oak_planks")
            setBlock(x, y, z2 - 1, "oak_planks")
        for z in range(z1 + 1, z2 - 1):
            setBlock(x1, y, z, "oak_planks")
            setBlock(x2 - 1, y, z, "oak_planks")
    # corners
    for dx in range(2):
        for dz in range(2):
            x = x1 + dx * (x2 - x1 - 1)
            z = z1 + dz * (z2 - z1 - 1)
            for y in range(y1, y2):
                setBlock(x, y, z, "oak_log");
    # clear interior
    for y in range(y1 + 1, y2):
        for x in range(x1+1, x2-1):
            for z in range(z1+1, z2-1):
                setBlock(x, y, z, "air")
    # roof
    if x2-x1 < z2-z1:
        for i in range(0, x2-x1, 2):
            halfI = int(i/2)
            for x in range(x1 + halfI, x2 - halfI):
                for z in range(z1, z2):
                    setBlock(x, y2 + halfI, z, "bricks")
    else:
        # same as above but with x and z swapped
        for i in range(0, z2-z1, 2):
            halfI = int(i/2)
            for z in range(z1 + halfI, z2 - halfI):
                for x in range(x1, x2):
                    setBlock(x, y2 + halfI, z, "bricks")

# build up to a hundred random houses and remember them to avoid overlaps
def rectanglesOverlap(r1, r2):
    if (r1[0]>=r2[0]+r2[2]) or (r1[0]+r1[2]<=r2[0]) or (r1[1]+r1[3]<=r2[1]) or (r1[1]>=r2[1]+r2[3]):
        return False
    else:
        return True

houses = []
for i in range(100):
    houseSizeX = random.randrange(5,25)
    houseSizeZ = random.randrange(5,25)
    houseX = random.randrange(area[0] + houseSizeX + 1, area[0] + area[2] - houseSizeX - 1)
    houseZ = random.randrange(area[1] + houseSizeZ + 1, area[1] + area[3] - houseSizeZ - 1)
    houseRect = (houseX, houseZ, houseSizeX, houseSizeZ)

    overlapsExisting = False
    for house in houses:
        if rectanglesOverlap(houseRect, house):
            overlapsExisting = True
            break
    
    if not overlapsExisting:
        houses.append(houseRect)
        print("building house at %i, %i with size %i,%i" % houseRect)

        houseY = min(
            heightAt(houseX, houseZ),
            heightAt(houseX + houseSizeX - 1, houseZ),
            heightAt(houseX, houseZ + houseSizeZ - 1),
            heightAt(houseX + houseSizeX - 1, houseZ + houseSizeZ - 1)
        ) - 1
        houseSizeY = random.randrange(4,7)

        buildHouse(houseX, houseY, houseZ, houseX + houseSizeX, houseY + houseSizeY, houseZ + houseSizeZ)


if USE_BATCHING:
    # we need to send remaining blocks in the buffer at the end of the program, when using batching
    interfaceUtils.sendBlocks()
