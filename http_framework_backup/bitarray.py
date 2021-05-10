#! /usr/bin/python3
"""### Read the bitarray format used by Minecraft.
"""
__all__ = ['BitArray']

# __version__

from math import floor


def inclusiveBetween(start, end, value):
    if value < start or value > end:
        raise ValueError(
            f"The value {value} is not in the inclusive range of {start} to {end}")


# Minecraft stores block and heightmap data in compacted arrays of longs. This class does the proper index mapping
# and bit shifting to get to the actual data.

class BitArray:
    def __init__(self, bitsPerEntryIn, arraySizeIn, data):
        inclusiveBetween(1, 32, bitsPerEntryIn)
        self.arraySize = arraySizeIn
        self.bitsPerEntry = bitsPerEntryIn
        self.maxEntryValue = (1 << bitsPerEntryIn) - 1
        self.entriesPerLong = floor(64 / bitsPerEntryIn)
        j = floor((arraySizeIn + self.entriesPerLong - 1) / self.entriesPerLong)
        if data is not None:
            if len(data) != j:
                raise Exception(
                    f"Invalid length given for storage, got: {len(data)} but expected: {j}")

            self.longArray = data
        else:
            self.longArray = []  # length j

    def getPosOfLong(self, index):
        return int(index / self.entriesPerLong)

    def getAt(self, index):
        inclusiveBetween(0, (self.arraySize - 1), index)
        i = self.getPosOfLong(index)
        # print("{} > {}".format(index, i))
        j = self.longArray[i]
        k = (index - i * self.entriesPerLong) * self.bitsPerEntry
        return j >> k & self.maxEntryValue

    def size(self):
        return self.arraySize
