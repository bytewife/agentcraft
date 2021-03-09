from interfaceUtils import *


### Returns a string containing the block names.
def download_area(origin_x, origin_y, origin_z, length_x, length_y, length_z, dir_x, dir_y, dir_z):
    print("downloading area")
    result = ""
    end_x = origin_x + (dir_x * length_x)
    end_y = origin_y + (dir_y * length_y)
    end_z = origin_z + (dir_z * length_z)

    def handle_dir():
        nonlocal origin_x, origin_y, origin_z
        nonlocal end_x, end_y, end_z
        if dir_x == -1:
            origin_x, end_x = end_x-1, origin_x-1
        if dir_y == -1:
            origin_y, end_y = end_y-1, origin_y-1
        if dir_z == -1:
            origin_z, end_z = end_z-1, origin_z-1


    # for y in range(origin_y, end_y, 1):
    for y in range(origin_y, end_y, dir_y):
        for x in range(origin_x, end_x, dir_x):
            for z in range(origin_z, end_z, dir_z):
                block = getBlock(x, y, z)
                result = result + block + " "
    print("finished downloading area")
    return result


def download_schematic(origin_x, origin_y, origin_z, length_x, length_y, length_z, dir_x, dir_y, dir_z, file_name):
    file = open(file_name, "w")
    file.write(download_area(origin_x, origin_y, origin_z, length_x, length_y, length_z, dir_x, dir_y, dir_z))
    file.write("\n")
    file.write(str(length_x) + " " + str(length_y) + " " + str(length_z))
    file.close()


### Place a pre-authored building. Takes dir arguments, which essentially orient the schematic placement
def place_schematic(file_name, origin_x, origin_y, origin_z, dir_x=1, dir_y=1, dir_z=1):
    file = open(file_name, "r")
    text = file.readlines()
    blocks_arr = text[0].split()

    length_x, length_y, length_z = text[1].split()
    length_x = int(length_x)
    length_y = int(length_y)
    length_z = int(length_z)
    n_blocks = length_x * length_y * length_z

    end_x = origin_x + int(length_x)
    end_y = origin_y + int(length_y)
    end_z = origin_z + int(length_z)

    def handle_dir():
        nonlocal origin_x, origin_y, origin_z
        nonlocal end_x, end_y, end_z
        if dir_x == -1:
            origin_x, end_x = end_x-1, origin_x-1
        if dir_y == -1:
            origin_y, end_y = end_y-1, origin_y-1
        if dir_z == -1:
            origin_z, end_z = end_z-1, origin_z-1
    handle_dir()

    i = 0
    for y in range(origin_y, end_y, dir_y):
        for x in range(origin_x, end_x, dir_x):
            for z in range(origin_z, end_z, dir_z):
                setBlock(x, y, z, blocks_arr[i], n_blocks)
                i += 1
