import http_framework.interfaceUtils
from enum import Enum

### Returns a string containing the block names.
def download_area(origin_x, origin_y, origin_z, end_x, end_y, end_z):
    print("downloading area")
    block_string = ""
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
                block = http_framework.interfaceUtils.getBlock(x, y, z)[10:].ljust(100, ' ')  # polished_blackstone_brick_stairs
                block_string = block_string + block + " "
            block_string+="\n"
        block_string+="\n"
    print("finished downloading area")
    return block_string


class Facing(Enum):
    north = 0
    east = 1
    south = 2
    west = 3


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
                block = "minecraft:"+blocks[index]
                facing_i = block.find("facing=")
                if facing_i != -1:
                    # get facing dir string
                    curr_dir = 0
                    start_i = facing_i + 7
                    facing_substr = block[start_i:start_i + 5]  # len of "facing="
                    # find dir
                    for dir in Facing:
                        if dir.name in facing_substr:
                            curr_dir = dir.value
                    # change direction based on dir
                    new_dir = Facing((curr_dir + dir_x + 2*dir_z) % 4).name
                    # string maniup to add new dir
                    first, second_old = block.split('facing=')
                    second_old = second_old[4:]
                    if second_old[0] == "h":
                        second_old = second_old[1:]
                    new_second = "facing=" + new_dir + second_old
                    block = first + new_second
                    print(block)

                if block[-1] == '}':  # if it uses block data
                    print("data block")
                    http_framework.interfaceUtils.setBlockWithData(x, y, z, block)
                    n_blocks -= 1  # just make sure the last block isn't a special case
                else:
                    http_framework.interfaceUtils.placeBlockBatched(x, y, z, block, n_blocks)#, n_blocks-1)
                xi += 1
            zi += 1
        yi -= 1
    print("done placing schematic")


## where the origin coords are the local coords within state
def place_schematic_in_state(state, file_name, origin_x, origin_y, origin_z, dir_x=1, dir_y=-1, dir_z=1):
    size, blocks = get_schematic_parts(file_name)
    length_x, length_y, length_z = size

    if (abs(origin_x + length_x) > abs(len(state.blocks)) or
            abs(origin_y + length_y) > abs(len(state.blocks[0])) or
            abs(origin_z + length_z) > abs(len(state.blocks[0][0]))):
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
                state.blocks[x][y][z] = block
                state.set_state_block(x, y, z, block)
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
    size_arr = [int(i) for i in size_str.split()]

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


def array_XYZ_to_schema(blocks, dx, dy, dz, file_out_name):
    out = open(file_out_name, "w")
    out.write(str(dx)+" "+str(dy)+" "+str(dz)+'\n')
    block_string = ''
    for y in range(dy):
        for z in range(dz):
            for x in range(dx):
                inv_y = dy - 1 - y
                block = blocks[x][inv_y][z].ljust(100, ' ')  # polished_blackstone_brick_stairs
                block_string = block_string + block + " "
            block_string+="\n"
        block_string+="\n"
    out.write(block_string)


def arrayXZ_to_schema(blocks, dx, dz, file_out_name):
    out = open(file_out_name, "w")
    out.write(str(dx)+" "+str(dz)+'\n')
    block_string = ''
    for x in range(dx):
        for z in range(dz):
            block = str(blocks[x][z]).ljust(100, ' ')  # polished_blackstone_brick_stairs
            block_string = block_string + block + " "
        block_string+="\n"
    out.write(block_string)


def download_heightmap(heightmap, file_name):
    f = open(file_name, "w")
    f.write(heightmap)


