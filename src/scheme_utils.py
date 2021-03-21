from src.http.interfaceUtils import *


# def download_area(origin_x, origin_y, origin_z, length_x, length_y, length_z, dir_x, dir_y, dir_z):
#     print("downloading area")
#     result = ""
#     end_x = origin_x + (dir_x * length_x)
#     end_y = origin_y + (dir_y * length_y)
#     end_z = origin_z + (dir_z * length_z)

### Returns a string containing the block names.
def download_area(origin_x, origin_y, origin_z, end_x, end_y, end_z):
    print("downloading area")
    result = ""
    dir_x = 1
    dir_y = 1
    dir_z = 1
    if end_x < origin_x:
        dir_x = -1
        # origin_x, end_x = end_x, origin_x
    if end_y < origin_y:
        dir_y = -1
    # origin_x, end_x = end_x, origin_x
    if end_z < origin_z:
        dir_z = -1
    # for y in range(origin_y, end_y, 1):
    for y in range(end_y, origin_y - 1, -dir_y):
        for z in range(origin_z, end_z+1, dir_z):
            for x in range(origin_x, end_x+1, dir_x):
                block = getBlock(x, y, z)[10:].ljust(34, ' ')  # polished_blackstone_brick_stairs
                result = result + block + " "
            result+="\n"
        result+="\n"
    print("finished downloading area")
    return result


def download_schematic(origin_x, origin_y, origin_z, end_x, end_y, end_z, file_name):
    file = open(file_name, "w")
    len_x = abs(origin_x - end_x) + 1
    len_y = abs(origin_y - end_y) + 1
    len_z = abs(origin_z - end_z) + 1
    file.write(str(len_x) + " " + str(len_y) + " " + str(len_z))
    file.write("\n")
    file.write(download_area(origin_x, origin_y, origin_z, end_x, end_y, end_z))
    file.close()


### Place a pre-authored building. Takes dir arguments, which essentially orient the schematic placement
def place_schematic(file_name, origin_x, origin_y, origin_z, dir_x=1, dir_y=-1, dir_z=1):
    file = open(file_name, "r")
    text = file.readlines()  # return an array of all lines in the file
    blocks_raw = ''
    for n in range(1, len(text)):
        blocks_raw += text[n]
    blocks = blocks_raw.split()

    length_x, length_y, length_z = text[0].split()
    length_x = int(length_x) - 1
    length_y = int(length_y) - 1
    length_z = int(length_z) - 1
    n_blocks = len(blocks)
    end_x = origin_x + int(length_x)
    end_y = origin_y + int(length_y)
    end_z = origin_z + int(length_z)

    def handle_dir():
        nonlocal origin_x, origin_y, origin_z
        nonlocal end_x, end_y, end_z
        if dir_x == -1:
            origin_x, end_x = end_x, origin_x-2
        if dir_y == 1:
            origin_y, end_y = end_y, origin_y-2
        if dir_z == -1:
            origin_z, end_z = end_z, origin_z-2
    handle_dir()

    XI = 0
    YI = max(length_y, 0)
    ZI = 0
    xi = XI
    yi = YI
    zi = ZI
    for y in range(origin_y, end_y+1, -dir_y):
        zi = ZI
        for z in range(origin_z, end_z+1, dir_z):
            xi = XI
            for x in range(origin_x, end_x+1, dir_x):
                index =yi*(length_z+1)*(length_x+1) + zi*(length_x+1) + xi
                print(index)
                block = "minecraft:"+blocks[index]
                print(block)
                setBlock(x, y, z, block)#, n_blocks-1)
                xi += 1
            zi += 1
        yi -= 1
    print("done placing schematic")
