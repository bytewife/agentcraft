from math import ceil, log2
from bitarray import BitArray
from io import BytesIO
import requests
import nbt
import numpy as np

## Wrapper for "GET blocks" endpoint
def getChunks(x, z, dx, dz, rtype = 'text'):
    print("getting chunks %i %i %i %i " % (x, z, dx, dz))
    
    url = 'http://localhost:9000/chunks?x=%i&z=%i&dx=%i&dz=%i' % (x, z, dx, dz)  # template string
    print("request url: %s" % url)
    acceptType = 'application/octet-stream' if rtype == 'bytes' else 'text/raw'
    response = requests.get(url, headers={"Accept": acceptType})
    print("result: %i" % response.status_code)
    if response.status_code >= 400:
        print("error: %s" % response.text)
    
    if rtype == 'text':
        return response.text
    elif rtype == 'bytes':
        return response.content

class CachedSection:
    def __init__(self, palette, blockStatesBitArray):
        self.palette = palette
        self.blockStatesBitArray = blockStatesBitArray

class WorldSlice:  # TODO wtf is this? It's called at the start of the generator
    # TODO format this to blocks
    # TODO: figure out how to get ohter types
    # NOTE: The heightmapTypes are predefined. See https://minecraft.gamepedia.com/Chunk_format
    # This is where you extract information about the world
    def __init__(self, rect, heightmapTypes=["MOTION_BLOCKING", "MOTION_BLOCKING_NO_LEAVES", "OCEAN_FLOOR", "WORLD_SURFACE"]):
        self.rect = rect  # where rect is a rect formed by the area tuple
        self.chunkRect = (
            rect[0] >> 4,
            rect[1] >> 4, 
            ((rect[0] + rect[2] - 1) >> 4) - (rect[0] >> 4) + 1,
            ((rect[1] + rect[3] - 1) >> 4) - (rect[1] >> 4) + 1
        )
        self.heightmapTypes = heightmapTypes

        bytes = getChunks(*self.chunkRect, rtype='bytes')
        file_like = BytesIO(bytes)

        # file1 = open("myfile.txt", "w")
        # file1.writelines(file_like)
        # file1.close()

        print("parsing NBT")
        self.nbtfile = nbt.nbt.NBTFile(buffer=file_like)


        rectOffset = [rect[0] % 16, rect[1] % 16]  # get rect's starting coords block x & y, clamped within ranges of 16

        # heightmaps
        self.heightmaps = {}
        for hmName in self.heightmapTypes:
            self.heightmaps[hmName] = np.zeros((rect[2], rect[3]), dtype=np.int)  # create an array of zeros with gives shape of rect[2] * rect[3

        # Sections are in x,z,y order!!! (reverse minecraft order :p)
        self.sections = [[[None for i in range(16)] for z in range(self.chunkRect[3])] for x in range(self.chunkRect[2])]  # create 3D array

        # Get a Heightmap based on the Heightmap Name (like without leaves, etc)
        print("extracting heightmaps")

        for x in range(self.chunkRect[2]):
            for z in range(self.chunkRect[3]):
                chunkID = x + z * self.chunkRect[2]

                hms = self.nbtfile['Chunks'][chunkID]['Level']['Heightmaps']
                for hmName in self.heightmapTypes:
                    # hmRaw = hms['MOTION_BLOCKING']
                    hmRaw = hms[hmName]
                    heightmapBitArray = BitArray(9, 16 * 16, hmRaw) # 256(since a chunk is 16x16 blocks) values, in which there are 9 bits per value
                    heightmap = self.heightmaps[hmName]
                    for cz in range(16):
                        for cx in range(16):
                            try:
                                heightmap[-rectOffset[0] + x * 16 + cx, -rectOffset[
                                    1] + z * 16 + cz] = heightmapBitArray.getAt(cz * 16 + cx)
                            except IndexError:
                                pass

        # sections
        print("extracting chunk sections")

        for x in range(self.chunkRect[2]):
            for z in range(self.chunkRect[3]):
                chunkID = x + z * self.chunkRect[2]
                chunkSections = self.nbtfile['Chunks'][chunkID]['Level']['Sections']

                for section in chunkSections:
                    y = section['Y'].value

                    if not ('BlockStates' in section) or len(section['BlockStates']) == 0:
                        continue

                    palette = section['Palette']  # the different set of blocks used in the Chunk
                    rawBlockStates = section['BlockStates']
                    bitsPerEntry = max(4, ceil(log2(len(palette))))
                    blockStatesBitArray = BitArray(bitsPerEntry, 16 * 16 * 16, rawBlockStates)

                    self.sections[x][z][y] = CachedSection(palette, blockStatesBitArray)  # cache the sections

        print("done")


    def getBlockCompoundAt(self, blockPos):
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
            return None # TODO return air compound instead

        bitarray = cachedSection.blockStatesBitArray
        palette = cachedSection.palette
        
        blockIndex = (blockPos[1] % 16) * 16*16 + (blockPos[2] % 16) * 16 + blockPos[0] % 16
        return palette[bitarray.getAt(blockIndex)]

    def getBlockAt(self, blockPos: object) -> object:
        blockCompound = self.getBlockCompoundAt(blockPos)
        if blockCompound == None:
            return "minecraft:air"
        else:
            return blockCompound["Name"].value