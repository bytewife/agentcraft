import math
from math import ceil, log2
from http_framework.bitarray import BitArray
from io import BytesIO
import requests
import nbt
import numpy as np
from math import floor


def getChunks(x, z, dx, dz, rtype='text'):
    """**Get raw chunk data.**"""
    # print("getting chunks {} {} {} {} ".format(x, z, dx, dz))

    url = 'http://localhost:9000/chunks?x={}&z={}&dx={}&dz={}'.format(
        x, z, dx, dz)
    # print("request url: {}".format(url))
    acceptType = 'application/octet-stream' if rtype == 'bytes' else 'text/raw'
    response = requests.get(url, headers={"Accept": acceptType})
    # print("result: {}".format(response.status_code))
    if response.status_code >= 400:
        print("error: {}".format(response.text))

    if rtype == 'text':
        return response.text
    elif rtype == 'bytes':
        return response.content


class CachedSection:
    """**Represents a cached chunk section (16x16x16).**"""

    def __init__(self, palette, blockStatesBitArray):
        self.palette = palette
        self.blockStatesBitArray = blockStatesBitArray


class WorldSlice:
    """**Contains information on a slice of the world.**"""
    # TODO format this to blocks

    def __init__(self, rect, heightmapTypes=["MOTION_BLOCKING", "MOTION_BLOCKING_NO_LEAVES", "OCEAN_FLOOR", "WORLD_SURFACE"], heightmapOnly = False, heightmapOnlyType="MOTION_BLOCKING_NO_LEAVES"):
        self.rect = rect
        # -16
        lowerMultOf16X = floor(rect[0]) >> 4
        lowerMultOf16Z = floor(rect[1]) >> 4
        upperMultOf16X = floor(rect[2]) >> 4
        upperMultOf16Z = floor(rect[3]) >> 4
        dx = upperMultOf16X - lowerMultOf16X + 1
        dz = upperMultOf16Z - lowerMultOf16Z + 1

        # upperMultOf16X =
        # self.chunkRect = (rect[0] >> 4, rect[1] >> 4, ((rect[0] + rect[2] - 1) >> 4) - (
        #         rect[0] >> 4) + 1, ((rect[1] + rect[3] - 1) >> 4) - (rect[1] >> 4) + 1)
        self.chunkRect = (lowerMultOf16X, lowerMultOf16Z, dx, dz)
        self.heightmapTypes = heightmapTypes


        bytes = getChunks(*self.chunkRect, rtype='bytes')

        file_like = BytesIO(bytes)

        # print("parsing NBT")
        self.nbtfile = nbt.nbt.NBTFile(buffer=file_like)


        rectOffset = [rect[0] % 16, rect[1] % 16]

        # heightmaps
        self.heightmaps = {}
        for hmName in self.heightmapTypes:
            len_x = abs(rect[2] - rect[0])
            len_z = abs(rect[3] - rect[1])
            self.heightmaps[hmName] = np.zeros( (len_x, len_z), dtype=np.int)

        # Sections are in x,z,y order!!! (reverse minecraft order :p)
        self.sections = [[[None for i in range(16)] for z in range(
            self.chunkRect[3])] for x in range(self.chunkRect[2])]
        # print(self.nbtfile['Chunks'])
        # heightmaps
        # print("extracting heightmaps")

        for x in range( self.chunkRect[2]):
            for z in range(self.chunkRect[3]):
                chunkID = x + z * self.chunkRect[2]

                hms = self.nbtfile['Chunks'][chunkID]['Level']['Heightmaps']
                for hmName in self.heightmapTypes:
                    # hmRaw = hms['MOTION_BLOCKING']


                    hmRaw = hms[hmName]
                    heightmapBitArray = BitArray(9, 16 * 16, hmRaw)
                    heightmap = self.heightmaps[hmName]
                    for cz in range(16):
                        for cx in range(16):
                            try:
                                heightmap[-rectOffset[0] + x * 16 + cx, -rectOffset[1] +
                                          z * 16 + cz] = heightmapBitArray.getAt(cz * 16 + cx)
                            except IndexError:
                                pass

        if heightmapOnly == True:
            return

        # sections

        for x in range(self.chunkRect[2]):
            for z in range(self.chunkRect[3]):
                chunkID = x + z * self.chunkRect[2]
                chunkSections = self.nbtfile['Chunks'][chunkID]['Level']['Sections']

                for section in chunkSections:
                    y = section['Y'].value

                    if not ('BlockStates' in section) or len(section['BlockStates']) == 0:
                        continue

                    palette = section['Palette']
                    rawBlockStates = section['BlockStates']
                    bitsPerEntry = max(4, ceil(log2(len(palette))))
                    blockStatesBitArray = BitArray(
                        bitsPerEntry, 16 * 16 * 16, rawBlockStates)

                    self.sections[x][z][y] = CachedSection(
                        palette, blockStatesBitArray)


    def getBlockCompoundAt(self, blockPos):
        """**Returns block data.**"""
        # chunkID = relativeChunkPos[0] + relativeChunkPos[1] * self.chunkRect[2]

        # section = self.nbtfile['Chunks'][chunkID]['Level']['Sections'][(blockPos[1] >> 4)+1]

        # if not ('BlockStates' in section) or len(section['BlockStates']) == 0:
        #     return -1 # TODO return air compound

        # palette = section['Palette']
        # blockStates = section['BlockStates']
        # bitsPerEntry = max(4, ceil(log2(len(palette))))
        chunkX = (blockPos[0] >> 4) - self.chunkRect[0]
        chunkZ = (blockPos[2] >> 4) - self.chunkRect[1]
        chunkY = blockPos[1] >> 4
        # bitarray = BitArray(bitsPerEntry, 16*16*16, blockStates) # TODO this needs to be 'cached' somewhere
        cachedSection = self.sections[chunkX][chunkZ][chunkY]

        if cachedSection == None:
            return None  # TODO return air compound instead

        bitarray = cachedSection.blockStatesBitArray
        palette = cachedSection.palette

        blockIndex = (blockPos[1] % 16) * 16 * 16 + \
                     (blockPos[2] % 16) * 16 + blockPos[0] % 16

        return palette[bitarray.getAt(blockIndex)]


    def getBlockAt(self, blockPos):
        """**Returns the block's namespaced id at blockPos.**"""
        blockCompound = self.getBlockCompoundAt(blockPos)
        if blockCompound == None:
            return "minecraft:air"
        else:
            return blockCompound["Name"].value


    ### Returns an array of the y-coordinates of the highest blocks, increased by 1.
    ### To get the ground, set y_offset to -1
    def get_heightmap(self, heightmap_type="MOTION_BLOCKING_NO_LEAVES", y_offset=0):
        heightmap = self.heightmaps[heightmap_type]
        if y_offset != 0:
            for x in range(len(heightmap)):
                for z in range(len(heightmap[x])):
                    heightmap[x][z] += y_offset
        return np.array(heightmap, dtype=np.uint8)


    ## Returns an array of the Block Compounds on the surface of a given area (x_start, x_end, z_start, z_end), with optional heightmap
    def get_surface_compounds_from(self, x1, z1, x2, z2, heightmap=None):  # Where None is an empty array
        if(heightmap is None):  #
            heightmap = self.get_heightmap()
        elif type(heightmap) is str:
            heightmap = self.get_heightmap(heightmap)
        compounds = []
        for x in range(x1, x2):
            for z in range(z1, z2):
                compound =self.getBlockCompoundAt((x, heightmap[x][z]-1, z))
                compounds.append(compound)
        return compounds


    ## TODO convert to 2d
    ## Returns an flat array of the Block Names on the surface of a given area (x_start, x_end, z_start, z_end), with optional heightmap
    def get_surface_blocks_from(self, x1, z1, x2, z2, heightmap=None):
        if (heightmap is None):  #
            heightmap = self.get_heightmap()
        elif type(heightmap) is str:
            heightmap = self.get_heightmap(heightmap)
        blocks = []
        for x in range(x1, x2):
            for z in range(z1, z2):
                block = self.getBlockCompoundAt((x, heightmap[x][z] - 1, z))["Name"]
                blocks.append(block)
        return blocks
