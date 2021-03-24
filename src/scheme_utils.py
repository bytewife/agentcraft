from src.http_framework.interfaceUtils import *
from src.states import mark_changed_blocks

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
    for y in range(end_y, origin_y-dir_y, -dir_y):
        for z in range(origin_z, end_z+dir_z, dir_z):
            for x in range(origin_x, end_x+dir_x, dir_x):
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
def place_schematic_in_world(file_name, origin_x, origin_y, origin_z, dir_x=1, dir_y=-1, dir_z=1):
    size, blocks = get_schematic_parts(file_name)
    length_x, length_y, length_z = size
    length_x = int(length_x)
    length_y = int(length_y)
    length_z = int(length_z)
    n_blocks = len(blocks)
    end_x = origin_x + int(length_x) - 1
    end_y = origin_y + int(length_y) - 1
    end_z = origin_z + int(length_z) - 1
    origin_x, origin_y, origin_z, end_x, end_y, end_z = handle_dir(
        origin_x, origin_y, origin_z, end_x, end_y, end_z, dir_x, dir_y, dir_z
        )

    XI = 0
    YI = max(length_y-1, 0)
    ZI = 0
    yi = YI
    for y in range(origin_y, end_y+1, -dir_y):
        zi = ZI
        for z in range(origin_z, end_z+1, dir_z):
            xi = XI
            for x in range(origin_x, end_x+1, dir_x):
                index =yi*length_z*length_x + zi*length_x + xi
                print(index)
                block = "minecraft:"+blocks[index]
                print(block)
                placeBlockBatched(x, y, z, block, n_blocks)#, n_blocks-1)
                xi += 1
            zi += 1
        yi -= 1
    print("done placing schematic")


## where the origin coords are the local coords within state
def place_schematic_in_state(state, file_name, origin_x, origin_y, origin_z, dir_x=1, dir_y=-1, dir_z=1):
    size, blocks = get_schematic_parts(file_name)
    length_x, length_y, length_z = size

    if (abs(origin_x + length_x) > abs(len(state)) or
            abs(origin_y + length_y) > abs(len(state[0])) or
            abs(origin_z + length_z) > abs(len(state[0][0]))):
        print("Tried to place schematic that didn't fit in the state!")
        return

    length_x = int(length_x)
    length_y = int(length_y)
    length_z = int(length_z)

    end_x = origin_x + int(length_x) - 1
    end_y = origin_y + int(length_y) - 1
    end_z = origin_z + int(length_z) - 1
    origin_x, origin_y, origin_z, end_x, end_y, end_z = handle_dir(
        origin_x, origin_y, origin_z, end_x, end_y, end_z, dir_x, dir_y, dir_z
    )

    XI = 0
    YI = max(length_y-1, 0)
    ZI = 0
    yi = YI
    i = 0
    for y in range(origin_y, end_y+1, -dir_y):
        zi = ZI
        for z in range(origin_z, end_z+1, dir_z):
            xi = XI
            for x in range(origin_x, end_x+1, dir_x):
                index = yi*(length_z)*(length_x) + zi*(length_x) + xi
                block = "minecraft:"+blocks[index]
                state[x][y][z] = block
                mark_changed_blocks(x, y, z, block)
                i+=1
                xi += 1
            zi += 1
        yi -= 1
    print(str(i)+" schematic blocks placed")
    print("done placing schematic")



def get_schematic_parts(file_name):
    file = open(file_name)
    raw = file.readlines()

    size_str = raw[0]
    size_arr = (int(i) for i in size_str.split())

    blocks_lines = raw[1:]
    blocks_str = ''
    for n in range(len(blocks_lines)):
        blocks_str += blocks_lines[n]
    blocks_arr = blocks_str.split()

    file.close()

    return size_arr, blocks_arr


def handle_dir(origin_x, origin_y, origin_z, end_x, end_y, end_z, dir_x, dir_y, dir_z):
    if dir_x == -1:
        origin_x, end_x = end_x, origin_x - 2
    if dir_y == 1:
        origin_y, end_y = end_y, origin_y - 2
    if dir_z == -1:
        origin_z, end_z = end_z, origin_z - 2
    return(origin_x, origin_y, origin_z, end_x, end_y, end_z)
