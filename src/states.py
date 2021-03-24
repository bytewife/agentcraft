from src.http_framework.worldLoader import *
from src.http_framework.interfaceUtils import *

tallest_building_height = 30

changed_blocks = {}

def mark_changed_blocks(state_x, state_y, state_z, block_name):
    key = str(state_x)+','+str(state_y)+','+str(state_z)
    changed_blocks[key] = block_name


def get_state(world_slice:WorldSlice, max_y_offset=tallest_building_height):
    x1, z1, x2, z2 = world_slice.rect
    state_heightmap = world_slice.get_heightmap("MOTION_BLOCKING_NO_LEAVES", -1) # inclusive of ground
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
    y1, y2  = get_y_bounds(state_heightmap)  # keep range not too large
    y2 += max_y_offset

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
    state_y = y1
    return state, state_y, state_heightmap  # this start_y is for load_state


def save_state(state, state_y, file_name):
    f = open(file_name, 'w')
    len_x = len(state)
    len_y = len(state[0])
    len_z = len(state[0][0])
    f.write('{}, {}, {}, {}\n'.format(len_x, state_y, len_y, len_z))
    i = 0
    for position,block in changed_blocks.items():
        to_write = position+';'+block+"\n"
        f.write(to_write)
        i += 1
    f.close()
    print(str(i)+" blocks saved")


def load_state(save_file, world_x, world_z):
    f = open(save_file, "r")
    lines = f.readlines()
    size = lines[0]
    blocks = lines[1:]
    n_blocks = len(blocks)
    len_x, state_starting_y, len_y, len_z = [int(i) for i in size.split(",")]
    i = 0
    for line in blocks:
        position_raw, block = line.split(';')
        print("position is "+position_raw)
        state_x, state_y, state_z = [int(coord) for coord in position_raw.split(',')]
        placeBlockBatched(world_x + state_x, int(state_starting_y) + state_y, world_z + state_z, block, n_blocks)
        print("placing at ")
        print(str(world_x + state_z), str(int(state_starting_y) + state_y), str(world_z + state_z))
        i += 1
    f.close()
    changed_blocks.clear()
    print(str(i)+" blocks loaded")
    print("done loading state")
