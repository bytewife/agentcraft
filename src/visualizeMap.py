import cv2
import matplotlib.pyplot as plt
import numpy as np

from http_framework import blockColors, interfaceUtils
from http_framework.worldLoader import WorldSlice

# rect = (108, -119, 128, 128)

def visualize_topography(rect, state, state_heightmap, state_y):
    buildArea = interfaceUtils.requestBuildArea()
    if buildArea != -1:
        x1 = buildArea["xFrom"]
        z1 = buildArea["zFrom"]
        x2 = buildArea["xTo"]
        z2 = buildArea["zTo"]
        rect = (x1, z1, x2-x1, z2-z1)

    slice = WorldSlice(rect)

    # heightmap1 = np.array(chunk_data.heightmaps["MOTION_BLOCKING_NO_LEAVES"], dtype = np.uint8)  # Doesn't show leaves

    # heightmap2 = np.array(chunk_data.heightmaps["OCEAN_FLOOR"], dtype = np.uint8)
    # heightmap1 = slice.get_heightmap("MOTION_BLOCKING_NO_LEAVES")
    # heightmap2 = slice.get_heightmap("OCEAN_FLOOR")

    heightmap = np.array(slice.heightmaps["OCEAN_FLOOR"], dtype=np.uint8)
    # watermap = heightmap - heightmap2 + 128

    gradientX = cv2.Scharr(heightmap, cv2.CV_16S, 1, 0)
    gradientY = cv2.Scharr(heightmap, cv2.CV_16S, 0, 1)

    # create a dictionary mapping block ids ("minecraft:...") to colors
    palette = {}

    for hex, blocks in blockColors.PALETTE.items():
        for block in blocks:
            palette[block] = hex

    # create a 2d map containing the surface block colors
    topcolor = np.zeros((rect[2], rect[3]), dtype='int')
    unknownBlocks = set()

    unknownBlocks = set()

    print(rect[3])
    print('must equal')
    print(len(state[0][0]))
    for x in range(rect[2]):
        for z in range(rect[3]):
            for dy in range(3):
            # check up to 5 assets below the heightmap
                # calculate absolute coordinates
                # dx = rect[0] + dx
                # dz = rect[1] + dz
                upper_y = state_heightmap[x][z] + 1
                # if x == 0 and z == 0:
                    # print(upper_y)
                    # print(upper_y-state_y)
                    # print(state[0][upper_y-state_y][0])
                y = upper_y - state_y - dy
                if (y < 0): break

            #####
                blockID = state[x][y][z]
                # print(blockID)
                # blockID = chunk_data.getBlockAt((x, y, z))
                #####

                if blockID in blockColors.TRANSPARENT:
                    # transparent assets are ignored
                    continue
                else:
                    if blockID not in palette:
                        # unknown assets remembered for debug purposes
                        unknownBlocks.add(blockID)
                    else:
                        topcolor[(x, z)] = palette[blockID]
                    break

    if len(unknownBlocks) > 0:
        print("Unknown assets: " + str(unknownBlocks))

        # separate the color map into three separate color channels
    topcolor = cv2.merge(((topcolor) & 0xff, (topcolor >> 8)
                          & 0xff, (topcolor >> 16) & 0xff))

    # calculate a brightness value from the gradient
    brightness = np.expand_dims((gradientX + gradientY).astype("int"), 2)
    brightness = brightness.clip(-64, 64)

    topcolor += brightness
    topcolor = topcolor.clip(0, 255)

    # display the map
    topcolor = topcolor.astype('uint8')
    topcolor = np.transpose(topcolor, (1, 0, 2))
    plt_image = cv2.cvtColor(topcolor, cv2.COLOR_BGR2RGB)

    plt.imshow(plt_image)
    plt.show()