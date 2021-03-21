import cv2
import matplotlib.pyplot as plt
import numpy as np

from src.http import blockColors, interfaceUtils
from src.http.worldLoader import WorldSlice

# rect = (108, -119, 128, 128)

def visualize_topography(rect):
    buildArea = interfaceUtils.requestBuildArea()
    if buildArea != -1:
        x1 = buildArea["xFrom"]
        z1 = buildArea["zFrom"]
        x2 = buildArea["xTo"]
        z2 = buildArea["zTo"]
        rect = (x1, z1, x2-x1, z2-z1)

    chunk_data = WorldSlice(rect)

    # heightmap1 = np.array(chunk_data.heightmaps["MOTION_BLOCKING_NO_LEAVES"], dtype = np.uint8)  # Doesn't show leaves
    # heightmap2 = np.array(chunk_data.heightmaps["OCEAN_FLOOR"], dtype = np.uint8)
    heightmap1 = chunk_data.get_heightmap("MOTION_BLOCKING_NO_LEAVES")
    heightmap2 = chunk_data.get_heightmap("OCEAN_FLOOR")
    heightmap = np.minimum(heightmap1, heightmap2)
    watermap = heightmap - heightmap2 + 128

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

    for dx in range(rect[2]):
        for dz in range(rect[3]):
            # check up to 5 blocks below the heightmap
            for dy in range(5):
                # calculate absolute coordinates
                x = rect[0] + dx
                z = rect[1] + dz
                y = int(heightmap1[(dx, dz)]) - dy

                blockID = slice.getBlockAt((x, y, z))
                if blockID in blockColors.TRANSPARENT:
                    # transparent blocks are ignored
                    continue
                else:
                    if blockID not in palette:
                        # unknown blocks remembered for debug purposes
                        unknownBlocks.add(blockID)
                    else:
                        topcolor[(dx, dz)] = palette[blockID]
                    break

    if len(unknownBlocks) > 0:
        print("Unknown blocks: " + str(unknownBlocks))

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