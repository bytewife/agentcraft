import cv2
import matplotlib.pyplot as plt
import numpy as np

import interfaceUtils
from worldLoader import WorldSlice

rect = (108, -119, 128, 128)

buildArea = interfaceUtils.requestBuildArea()
if buildArea != -1:
    x1 = buildArea["xFrom"]
    z1 = buildArea["zFrom"]
    x2 = buildArea["xTo"]
    z2 = buildArea["zTo"]
    print(buildArea)
    rect = (x1, z1, x2-x1, z2-z1)
    print(rect)

slice = WorldSlice(rect)

heightmap1 = np.array(slice.heightmaps["MOTION_BLOCKING_NO_LEAVES"], dtype = np.uint8)
heightmap2 = np.array(slice.heightmaps["OCEAN_FLOOR"], dtype = np.uint8)
heightmap = np.minimum(heightmap1, heightmap2)
watermap = heightmap - heightmap2 + 128

bHM = cv2.blur(heightmap, (7, 7))

dx = cv2.Scharr(heightmap, cv2.CV_16S, 1, 0)
dy = cv2.Scharr(heightmap, cv2.CV_16S, 0, 1)
atan = np.arctan2(dx, dy, dtype=np.float64) * 5 / 6.283
atan = atan % 5
atan = atan.astype('uint8')

finalHM = cv2.medianBlur(heightmap, 7)

diffmap = finalHM.astype('float64') - heightmap.astype('float64')
diffmap = np.round(diffmap)
diffmap = diffmap.astype('int8')

# diff
img = heightmap
diffx = cv2.Scharr(img, cv2.CV_16S, 1, 0)
diffy = cv2.Scharr(img, cv2.CV_16S, 0, 1)
dmag = np.absolute(diffx) + np.absolute(diffy)
# thres = 32
# dmag = dmag - thres
dmag = dmag.clip(0, 255)
dmag = dmag.astype('uint8')

# block visualization

palette = [
    "unknown",
    "minecraft:dirt",
    "minecraft:grass",
    "minecraft:grass_block",
    "minecraft:stone",
    "minecraft:sand",
    "minecraft:snow",
    "minecraft:water",
    "minecraft:ice",
    "minecraft:white_wool",
    "minecraft:white_concrete",
]
paletteColors = [
    0x000000,
    0x777733,
    0x33aa33,
    0x33aa33,
    0x777777,
    0xffffaa,
    0xffffff,
    0x3333ee,
    0xaaaaee,
    0xffffff,
    0xffffff,
]
paletteReverseLookup = {}
for i in range(len(palette)):
    paletteReverseLookup[palette[i]] = i

topmap = np.zeros((rect[2],rect[3]), dtype='int')
topcolor = np.zeros(topmap.shape, dtype="int")

unknownBlocks = set()

for dx in range(rect[2]):
    for dz in range(rect[3]):
        for dy in range(5):
            x = rect[0] + dx
            z = rect[1] + dz
            y = int(heightmap1[(dx,dz)]) - dy

            blockCompound = slice.getBlockCompoundAt((x,y,z))
            
            if blockCompound != None:
                blockID = blockCompound["Name"].value
                if(blockID in ["minecraft:air", "minecraft:cave_air"]):
                    continue
                else:
                    numID = paletteReverseLookup.get(blockID, 0)
                    if(numID == 0): unknownBlocks.add(blockID)
                    # print("%s > %i" % (blockID, numID))
                    topmap[(dx, dz)] = numID
                    topcolor[(dx, dz)] = paletteColors[numID]
                    break

print("unknown blocks: %s" % str(unknownBlocks))

# topcolor = np.pad(topcolor, 16, mode='edge')
topcolor = cv2.merge(((topcolor) & 0xff, (topcolor >> 8) & 0xff, (topcolor >> 16) & 0xff))

off = np.expand_dims((diffx + diffy).astype("int"), 2)
# off = np.pad(off, ((16, 16), (16, 16), (0, 0)), mode='edge')
off = off.clip(-64, 64)
topcolor += off
topcolor = topcolor.clip(0, 255)

topcolor = topcolor.astype('uint8')

topcolor = np.transpose(topcolor, (1,0,2))
plt_image = cv2.cvtColor(topcolor, cv2.COLOR_BGR2RGB)
imgplot = plt.imshow(plt_image)

plt.show()
