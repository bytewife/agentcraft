#! /usr/bin/python3
"""### Test various aspects of the framework automatically.

The tests contained in this file include:

-

It is not meant to be imported.
"""

__all__ = []
__version__ = "v4.2_dev"

import random

# import bitarray
import blockColors
# import example
import interfaceUtils

# import time
# import timeit

# import mapUtils
# import visualizeMap
# import worldLoader

TCOLOURS = {"black":    "\033[38;2;000;000;000m",
            "grey":     "\033[38;2;128;128;128m",
            "white":    "\033[38;2;255;255;255m",
            "pink":     "\033[38;2;255;192;203m",
            "red":      "\033[38;2;255;000;000m",
            "orange":   "\033[38;2;255;165;000m",
            "yellow":   "\033[38;2;255;255;000m",
            "darkgreen": "\033[38;2;000;128;000m",
            "green":    "\033[38;2;000;255;000m",
            "blue":     "\033[38;2;135;206;235m",
            "darkblue": "\033[38;2;000;000;255m",
            "magenta":  "\033[38;2;255;000;255m",
            "brown":    "\033[38;2;139;069;019m",
            "CLR":      "\033[0m"}  # 38 is replaced by 48 for background


class TestException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


def verifyPaletteBlocks():
    """Check blockColours blocks."""
    print(f"\n{TCOLOURS['yellow']}Running blockColours palette test...")

    print(f"\t{TCOLOURS['grey']}Preparing...", end="\r")
    tester = interfaceUtils.Interface()
    counter = 0
    badcounter = 0
    passed = []
    tocheck = [block for i in blockColors.PALETTE.values()
               for block in i] + list(blockColors.TRANSPARENT)
    print(f"\t{TCOLOURS['grey']}Preparing done.")

    for block in tocheck:
        if block in passed:
            badcounter += 1
            print()
            print(f"\t\t{TCOLOURS['grey']}{block} is duplicated")
        elif not tester.placeBlock(0, 0, 0, block).isnumeric():
            badcounter += 1
            print()
            print(tester.placeBlock(0, 0, 0, block))
            print(f"\t\t{TCOLOURS['orange']}Cannot verify {block}")
        counter += 1
        passed.append(block)
        print(f"\t{TCOLOURS['blue']}{counter}"
              f"{TCOLOURS['CLR']} blocks verified.", end='\r')
    interfaceUtils.setBlock(0, 0, 0, 'air')
    if badcounter > 0:
        raise TestException(f"{TCOLOURS['red']}{badcounter}/"
                            f"{TCOLOURS['grey']}{counter}"
                            f"{TCOLOURS['red']} blocks duplicate "
                            "or could not be verified.\n"
                            f"{TCOLOURS['orange']}Please check you are running"
                            f" on Minecraft {blockColors.VERSION}")

    print(f"{TCOLOURS['green']}All {counter} blocks successfully verified!")


def xzloop(x, z):
    for x2 in range(x):
        for z2 in range(z):
            yield x2, z2


def testCache():
    """Check Interface cache functionality."""
    print(f"\n{TCOLOURS['yellow']}Running Interface cache test...")
    SIZE = 16
    PALETTES = (("birch_fence", "stripped_birch_log"),
                ("dark_oak_fence", "stripped_dark_oak_log"))

    def clearTestbed():
        """Clean testbed for placement from memory."""
        print("\t\tWiping blocks...", end="\r")
        tester.fill(0, 1, 0, SIZE - 1, 1, SIZE - 1, "shroomlight")
        tester.sendBlocks()
        print("\n\t\tWiping blocks done.")

    def placeFromCache():
        """Replace all removed blocks from memory."""
        print("\t\tReplacing blocks from memory...", end="\r")
        tester.caching = True
        for x, z in xzloop(SIZE, SIZE):
            tester.setBlock(x, 1, z, tester.getBlock(x, 1, z))
        tester.sendBlocks()
        tester.caching = False
        print("\n\t\tReplacing blocks from memory done.")

    def checkDiscrepancies():
        """Check test bed and comparison layer for discrepancies."""
        for x, z in xzloop(SIZE, SIZE):
            print("\t\tTesting...▕" + (10 * x // SIZE) * "█"
                  + (10 - 10 * x // SIZE) * "▕", end="\r")

            for palette in PALETTES:
                if tester.getBlock(x, 1, z) == "minecraft:shroomlight":
                    raise TestException(
                        f"{TCOLOURS['red']}Block at "
                        f"{TCOLOURS['orange']}{x} 0 {z} "
                        f"{TCOLOURS['red']}was no longer in memory.")
                if tester.getBlock(x, 0, z) == palette[0]:
                    if tester.getBlock(x, 1, z) == palette[1]:
                        continue
                    else:
                        raise TestException(
                            f"{TCOLOURS['red']}Cache test failed at "
                            f"{TCOLOURS['orange']}{x} 0 {z}"
                            f"{TCOLOURS['red']}.")
        print("\t\tTesting...▕██████████")
        print(f"\t{TCOLOURS['darkgreen']}No discrepancies found.")

    # ---- preparation
    print(f"\t{TCOLOURS['grey']}Preparing...", end="\r")
    tester = interfaceUtils.Interface(buffering=True, bufferlimit=SIZE ** 2)
    tester.fill(0, 2, 0, SIZE - 1, 2, SIZE - 1, "bedrock")
    tester.fill(0, 0, 0, SIZE - 1, 1, SIZE - 1, "air")
    tester.sendBlocks()
    tester.cache.maxsize = (SIZE ** 2)
    print("\tPerparing done.")

    # ---- test block scatter
    print("\tScattering test blocks...", end="\r")
    for x, z in xzloop(SIZE, SIZE):
        print("\tPlacing pattern...▕" + (10 * x // SIZE) * "█"
              + (10 - 10 * x // SIZE) * "▕", end="\r")
        type = random.choice(PALETTES)
        tester.caching = True
        tester.setBlock(x, 1, z, type[1])
        tester.caching = False
        tester.setBlock(x, 0, z, type[0])
    tester.sendBlocks()
    print("\tPlacing pattern...▕██████████")
    print("\tScattering test blocks done.")

    # ---- first run (caching through setBlock)
    print(f"\t{TCOLOURS['grey']}First run: Cache updated via setBlock")

    clearTestbed()
    placeFromCache()
    checkDiscrepancies()

    # ---- second run (caching through getBlock)
    print(f"\t{TCOLOURS['grey']}Second run: Cache updated via getBlock")

    tester.cache.clear
    tester.caching = True
    for x, z in xzloop(SIZE, SIZE):
        print("\t\tReading...▕" + (10 * x // SIZE) * "█"
              + (10 - 10 * x // SIZE) * "▕", end="\r")
        tester.getBlock(x, 1, z)
    tester.caching = False
    print("\t\tReading...▕██████████")
    print("\t\tCache refilled.")

    clearTestbed()
    placeFromCache()
    checkDiscrepancies()

    # ---- third run (randomized get-/setBlock)
    print(f"\t{TCOLOURS['grey']}Third run: Cache updated via random methods")
    for i in range(4 * SIZE):
        print("\t\tMuddling...▕" + (10 * i // SIZE) * "█"
              + (10 - 10 * i // SIZE) * "▕", end="\r")
        x = random.randint(0, SIZE - 1)
        z = random.randint(0, SIZE - 1)
        if random.choice([True, False]):
            type = random.choice(PALETTES)
            tester.caching = True
            tester.setBlock(x, 1, z, type[1])
            tester.caching = False
            tester.setBlock(x, 0, z, type[0])
            tester.sendBlocks()
        else:
            tester.caching = True
            tester.getBlock(x, 1, z)
            tester.caching = False
    print("\t\tMuddling...▕██████████")
    print("\t\tMuddling complete.")

    clearTestbed()
    placeFromCache()
    checkDiscrepancies()

    # ---- fourth run (using WorldSlice)

    print(f"\t{TCOLOURS['grey']}Fourth run: Cache updated via WorldSlice")
    for i in range(4 * SIZE):
        print("\t\tMuddling...▕" + (10 * i // SIZE) * "█"
              + (10 - 10 * i // SIZE) * "▕", end="\r")
        x = random.randint(0, SIZE - 1)
        z = random.randint(0, SIZE - 1)
        if random.choice([True, False]):
            type = random.choice(PALETTES)
            tester.setBlock(x, 1, z, type[1])
            tester.setBlock(x, 0, z, type[0])
            tester.sendBlocks()
        else:
            tester.getBlock(x, 1, z)
    print("\t\tMuddling...▕██████████")
    print("\t\tMuddling complete.")

    interfaceUtils.makeGlobalSlice()

    clearTestbed()
    placeFromCache()
    checkDiscrepancies()

    # ---- cleanup
    print(f"{TCOLOURS['green']}Cache test complete!")
    tester.fill(0, 0, 0, SIZE, 1, SIZE, "bedrock")
    interfaceUtils.globalWorldSlice = None
    interfaceUtils.globalDecay = None


if __name__ == '__main__':
    TESTS = (verifyPaletteBlocks, testCache)

    print(f"Beginning test suite for version "
          f"{TCOLOURS['blue']}{__version__}: {len(TESTS)} tests")
    failed = 0
    errors = ""
    for test in TESTS:
        try:
            test()
        except TestException as e:
            errors += f"{TCOLOURS['red']}> {test.__name__}() failed.\n" \
                + f"{TCOLOURS['grey']}Cause: {e}\n"
            failed += 1
    print(f"\n{TCOLOURS['CLR']}Test suite completed with "
          f"{TCOLOURS['orange']}{failed}"
          f"{TCOLOURS['CLR']} fails!\n")
    if errors != "":
        print(f"==== Summary ====\n{errors}{TCOLOURS['CLR']}")
