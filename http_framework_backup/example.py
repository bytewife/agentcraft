#! /usr/bin/python3
"""### Generate an example village.

The source code of this module contains examples for:
* Retrieving the build area
* Basic heightmap functionality
* Single block placement
* Batch block placement

It is not meant to be imported.
"""
__all__ = []
# __version__

import random

import interfaceUtils
import mapUtils
from worldLoader import WorldSlice

# set up an interface for getting and placing blocks
# IMPORTANT: It is recommended not to use buffering during development
# How to use buffering (batch placement):
#   Allow block buffer placement
#       >>> interfaceUtils.setBuffering(True)
#   Change maximum buffer size (default is 1024 blocks, set 4096 for speed)
#       >>> interfaceUtils.setBufferLimit(100)
#   Send blocks to world
#       >>> interfaceUtils.sendBlocks()
#   NOTE: The buffer will automatically place its blocks once it gets full
#   NOTE: It is a good idea to call sendBlocks() after completing a task,
#       so that you can see the result without having to wait
#   IMPORTANT: A crash may prevent the blocks from being placed

# see if a build area has been specified
# you can set a build area in minecraft using the /setbuildarea command
startx, starty, startz, endx, endy, endz = interfaceUtils.requestBuildArea()


def heightAt(x, z):
    """Access height using local coordinates."""
    # Warning:
    # Heightmap coordinates are not equal to world coordinates!
    return heightmap[(x - startx, z - startz)]


def buildHouse(x1, y1, z1, x2, y2, z2):
    """Build a small house."""
    # floor
    interfaceUtils.fill(x1, y1, z1, x2 - 1, y1, z2 - 1, "cobblestone")

    # walls
    interfaceUtils.fill(x1 + 1, y1, z1, x2 - 2, y2, z1, "oak_planks")
    interfaceUtils.fill(x1 + 1, y1, z2 - 1, x2 - 2, y2, z2 - 1, "oak_planks")
    interfaceUtils.fill(x1, y1, z1 + 1, x1, y2, z2 - 2, "oak_planks")
    interfaceUtils.fill(x2 - 1, y1, z1 + 1, x2 - 1, y2, z2 - 2, "oak_planks")

    # corners
    interfaceUtils.fill(x1, y1, z1, x1, y2, z1, "oak_log")
    interfaceUtils.fill(x2 - 1, y1, z1, x2 - 1, y2, z1, "oak_log")
    interfaceUtils.fill(x1, y1, z2 - 1, x1, y2, z2 - 1, "oak_log")
    interfaceUtils.fill(x2 - 1, y1, z2 - 1, x2 - 1, y2, z2 - 1, "oak_log")

    # clear interior
    for y in range(y1 + 1, y2):
        for x in range(x1 + 1, x2 - 1):
            for z in range(z1 + 1, z2 - 1):
                # check what's at that place and only delete if not air
                if "air" not in interfaceUtils.getBlock(x, y, z):
                    interfaceUtils.setBlock(x, y, z, "air")

    # roof
    if x2 - x1 < z2 - z1:   # if the house is longer in Z-direction
        for i in range(0, (1 - x1 + x2) // 2):
            interfaceUtils.fill(x1 + i, y2 + i, z1,
                                x2 - 1 - i, y2 + i, z2 - 1, "bricks")
    else:
        # same as above but with x and z swapped
        for i in range(0, (1 - z1 + z2) // 2):
            interfaceUtils.fill(x1, y2 + i, z1 + i, x2 - 1,
                                y2 + i, z2 - 1 - i, "bricks")

    if interfaceUtils.isBuffering():
        interfaceUtils.sendBlocks()


def rectanglesOverlap(r1, r2):
    """Check whether r1 and r2 overlap."""
    if ((r1[0] >= r2[0] + r2[2]) or (r1[0] + r1[2] <= r2[0])
            or (r1[1] + r1[3] <= r2[1]) or (r1[1] >= r2[1] + r2[3])):
        return False
    else:
        return True


if __name__ == '__main__':

    print(f"Build area is at position {startx}, {startz}"
          f" with size {endx}, {endz}")

    # load the world data
    # this uses the /chunks endpoint in the background
    worldSlice = WorldSlice(startx, startz, endx, endz)

    # calculate a heightmap suitable for building:
    heightmap = mapUtils.calcGoodHeightmap(worldSlice)

    # example alternative heightmaps:
    # >>> heightmap = worldSlice.heightmaps["MOTION_BLOCKING"]
    # >>> heightmap = worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    # >>> heightmap = worldSlice.heightmaps["OCEAN_FLOOR"]
    # >>> heightmap = worldSlice.heightmaps["WORLD_SURFACE"]

    # show the heightmap as an image
    # >>> mapUtils.visualize(heightmap, title="heightmap")

    # build a fence around the perimeter
    for x in range(startx, endx):
        z = startz
        y = heightAt(x, z)
        interfaceUtils.setBlock(x, y - 1, z, "cobblestone")
        interfaceUtils.setBlock(x, y,   z, "oak_fence")
    for z in range(startz, endz):
        x = startx
        y = heightAt(x, z)
        interfaceUtils.setBlock(x, y - 1, z, "cobblestone")
        interfaceUtils.setBlock(x, y, z, "oak_fence")
    for x in range(startx, endx):
        z = endz - 1
        y = heightAt(x, z)
        interfaceUtils.setBlock(x, y - 1, z, "cobblestone")
        interfaceUtils.setBlock(x, y,   z, "oak_fence")
    for z in range(startz, endz):
        x = endx - 1
        y = heightAt(x, z)
        interfaceUtils.setBlock(x, y - 1, z, "cobblestone")
        interfaceUtils.setBlock(x, y, z, "oak_fence")

    if interfaceUtils.isBuffering():
        interfaceUtils.sendBlocks()

    houses = []
    for i in range(100):

        # pick random rectangle to place new house
        houseSizeX = random.randrange(5, 25)
        houseSizeZ = random.randrange(5, 25)
        houseX = random.randrange(
            startx + houseSizeX + 1, endx - houseSizeX - 1)
        houseZ = random.randrange(
            startz + houseSizeZ + 1, endz - houseSizeZ - 1)
        houseRect = (houseX, houseZ, houseSizeX, houseSizeZ)

        # check whether there are any overlaps
        overlapsExist = False
        for house in houses:
            if rectanglesOverlap(houseRect, house):
                overlapsExist = True
                break

        if not overlapsExist:

            print(f"building house at {houseRect[0]},{houseRect[1]} "
                  f"with size {houseRect[2]+1},{houseRect[3]+1}")

            # find the lowest corner of the house and give it a random height
            houseY = min(
                heightAt(houseX, houseZ),
                heightAt(houseX + houseSizeX - 1, houseZ),
                heightAt(houseX, houseZ + houseSizeZ - 1),
                heightAt(houseX + houseSizeX - 1, houseZ + houseSizeZ - 1)
            ) - 1
            houseSizeY = random.randrange(4, 7)

            # build the house!
            buildHouse(houseX, houseY, houseZ, houseX + houseSizeX,
                       houseY + houseSizeY, houseZ + houseSizeZ)
            houses.append(houseRect)
