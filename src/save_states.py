from src.http.worldLoader import *
from src.http.interfaceUtils import *

tallest_building_height = 30

def get_state(world_slice:WorldSlice, add_talling_building_height=True):
    x1, z1, x2, z2 = world_slice.rect
    heightmap = world_slice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    def get_y_bounds(_heightmap):  ## Get the y range that we'll save tha state in?
        lowest = 99
        highest = 0
        for col in _heightmap:
            for block_y in col:
                if (block_y < lowest):
                    lowest = block_y
                elif (block_y > highest):
                    highest = block_y
        return lowest, highest
    y1, y2  = get_y_bounds(heightmap)  # keep range not too large
    if add_talling_building_height:
        y2 += tallest_building_height

    len_z = abs(z2 - z1)
    len_y = abs(y2 - y1)
    len_x = abs(x2 - x1)
    state = [[[0 for z in range(len_z)] for y in range(len_y)] for x in range(len_x)] # the format of the state isn't the same as the file's.
    xi = 0
    yi = 0
    zi = 0
    for x in range(x1, x2):
        yi *= 0
        for y in range(y1, y2):
            zi *= 0
            for z in range(z1, z2):
                block = world_slice.getBlockAt((x, y, z))
                state[xi][yi][zi] = block
                zi += 1
            yi += 1
        xi += 1
    start_y = y1
    return state, start_y  # this start_y is for load_state

def save_state(state, start_y):
    f = open("save_1.txt", 'w')
    len_x = len(state)
    len_y = len(state[0])
    len_z = len(state[0][0])
    f.write('{}, {}, {}, {}\n'.format(len_x, start_y, len_y, len_z))
    i = 0
    for y in range(0, len_y):
        for x in range(0, len_x):
            for z in range(0, len_z):
                f.write(state[x][y][z]+"\n")
                i+=1
    print(i)
    f.close()


def load_state(save_file, start_x, start_z):
    f = open(save_file, "r")
    lines = f.readlines()
    size = lines[0]
    blocks = lines[1:]
    # print(blocks)
    count = len(blocks)
    len_x, start_y, len_y, len_z = [int(i) for i in size.split(",")]

    i = 0
    for y in range(len_y):
        for x in range(len_x):
            for z in range(len_z):
                block = blocks[i]
                placeBlockBatched(start_x + x, start_y + y, start_z + z, block, count)
                i += 1
    print("done loading state")
