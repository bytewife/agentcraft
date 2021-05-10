# ! /usr/bin/python3
"""### Provides tools for reading chunk data.

This module contains functions to:
* Calculate a heightmap ideal for building
* Visualise numpy arrays
"""
__all__ = ['WorldSlice']
# __version__

from io import BytesIO
from math import ceil, log2

import nbt
import numpy as np
import requests
from http_framework.bitarray import BitArray


def getChunks(x, z, dx, dz, rtype='text'):
    """**Get raw chunk data**."""
    # print(f"getting chunks {x} {z} {dx} {dz} ")

    url = f'http://localhost:9000/chunks?x={x}&z={z}&dx={dx}&dz={dz}'
    # print(f"request url: {url}")
    acceptType = 'application/octet-stream' if rtype == 'bytes' else 'text/raw'
    response = requests.get(url, headers={"Accept": acceptType})
    # print(f"result: {response.status_code}")
    if response.status_code >= 400:
        print(f"error: {response.text}")

    if rtype == 'text':
        return response.text
    elif rtype == 'bytes':
        return response.content


class CachedSection:
    """**Represents a cached chunk section (16x16x16)**."""

    def __init__(self, palette, blockStatesBitArray):
        self.palette = palette
        self.blockStatesBitArray = blockStatesBitArray


class WorldSlice:
    """**Contains information on a slice of the world**."""

    def __init__(self, x1, z1, x2, z2,
                 heightmapTypes=["MOTION_BLOCKING",
                                 "MOTION_BLOCKING_NO_LEAVES",
                                 "OCEAN_FLOOR",
                                 "WORLD_SURFACE"]):
        """**Initialise WorldSlice with region and heightmaps**."""
        self.rect = x1, z1, x2 - x1, z2 - z1
        self.chunkRect = (self.rect[0] >> 4, self.rect[1] >> 4,
                          ((self.rect[0] + self.rect[2] - 1) >> 4)
                          - (self.rect[0] >> 4) + 1,
                          ((self.rect[1] + self.rect[3] - 1) >> 4)
                          - (self.rect[1] >> 4) + 1)
        self.heightmapTypes = heightmapTypes

        bytes = getChunks(*self.chunkRect, rtype='bytes')
        file_like = BytesIO(bytes)

        print("Retrieving NBT data from running Minecraft World! Please don't modify it until complete.")
        try:
            self.nbtfile = nbt.nbt.NBTFile(buffer=file_like)
        except nbt.nbt.MalformedFileError:
            print("Error during NBT retrieval! This happens sometimes, usually when the world was modified during retrieval.")
            exit(1)

        rectOffset = [self.rect[0] % 16, self.rect[1] % 16]

        # heightmaps
        self.heightmaps = {}
        for hmName in self.heightmapTypes:
            self.heightmaps[hmName] = np.zeros(
                (self.rect[2], self.rect[3]), dtype=np.int)

        # Sections are in x,z,y order!!! (reverse minecraft order :p)
        self.sections = [[[None for i in range(16)] for z in range(
            self.chunkRect[3])] for x in range(self.chunkRect[2])]

        # heightmaps
        # print("extracting heightmaps")

        for x in range(self.chunkRect[2]):
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
                                heightmap[-rectOffset[0] + x * 16 + cx,
                                          -rectOffset[1] + z * 16 + cz] \
                                    = heightmapBitArray.getAt(cz * 16 + cx)
                            except IndexError:
                                pass

        # sections
        # print("extracting chunk sections")

        for x in range(self.chunkRect[2]):
            for z in range(self.chunkRect[3]):
                chunkID = x + z * self.chunkRect[2]
                chunk = self.nbtfile['Chunks'][chunkID]
                chunkSections = chunk['Level']['Sections']

                for section in chunkSections:
                    y = section['Y'].value

                    if (not ('BlockStates' in section)
                            or len(section['BlockStates']) == 0):
                        continue

                    palette = section['Palette']
                    rawBlockStates = section['BlockStates']
                    bitsPerEntry = max(4, ceil(log2(len(palette))))
                    blockStatesBitArray = BitArray(
                        bitsPerEntry, 16 * 16 * 16, rawBlockStates)

                    self.sections[x][z][y] = CachedSection(
                        palette, blockStatesBitArray)

        print("Finished retrieving NBT data! Now attempting to find valid settlement location:")

    def getBlockCompoundAt(self, x, y, z):
        """**Return block data**."""
        chunkX = (x >> 4) - self.chunkRect[0]
        chunkZ = (z >> 4) - self.chunkRect[1]
        chunkY = y >> 4

        cachedSection = self.sections[chunkX][chunkZ][chunkY]

        if cachedSection is None:
            return None  # TODO return air compound instead

        bitarray = cachedSection.blockStatesBitArray
        palette = cachedSection.palette

        blockIndex = (y % 16) * 16 * 16 + \
            (z % 16) * 16 + x % 16
        return palette[bitarray.getAt(blockIndex)]

    def getBlockAt(self, x, y, z):
        """**Return the block's namespaced id at blockPos**."""
        blockCompound = self.getBlockCompoundAt(x, y, z)
        if blockCompound is None:
            return "minecraft:air"
        else:
            return blockCompound["Name"].value
