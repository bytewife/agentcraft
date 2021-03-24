
## do we wanna cache tree locations? I don't want them to cut down buildings lol
def is_log(state, x, y, z):
    block = state[x][y][z]
    if block[-3:] == 'log':
        return True
    return False

## assumes there's a tree at the location
def cut_log_at(state, x, y, z):
    log_type = get_log_type(state[x][y][z])
    state[x][y][z] = "minecraft:air"
    if is_leaf(get_adjacent_block(state, x, y, z, 0, 1, 0)) or is_leaf(get_adjacent_block(state, x, y, z, 1, 0, 0)):
        trim_leaves(state, x, y+1, z)
    if not is_log(state, x, y-1, z):  # place sapling
        state[x][y][z] = "minecraft:"+log_type+"_sapling"

##
def get_adjacent_block(state, x_origin, y_origin, z_origin, x_off, y_off, z_off):
    x_target = x_origin + x_off
    y_target = y_origin + y_off
    z_target = z_origin + z_off
    if x_target >= len(state) or y_target >= len(state[0]) or z_target >= len(state[0][0]):
        #TODO this might lead to clipping
        print("Cannot check for block out of state bounds")
        return None
    return state[x_target][y_target][z_target]


def get_all_adjacent_blocks(state, x_origin, y_origin, z_origin):
    adj_blocks = []
    for x_off in range(-1, 2):
        for y_off in range(-1, 2):
            for z_off in range(-1, 2):
                if x_off == 0 and y_off == 0 and z_off == 0:
                    continue
                block = get_adjacent_block(state, x_origin, y_origin, z_origin, x_off, y_off, z_off)
                if block is None:
                    continue
                adj_blocks.append((block, x_origin+x_off, y_origin+y_off, z_origin+z_off))
    return adj_blocks


def perform_on_adj_recursively(state, x, y, z, target_block_checker, recur_func, forward_call):
    # recur_args = (state, x, y, z, target_block_checker, recur_func, callback)
    forward_call(state, x, y, z)
    adj_blocks = get_all_adjacent_blocks(state, x, y, z)
    for block in adj_blocks:
        if target_block_checker(block[0]):
            recur_func(state, block[1], block[2], block[3], target_block_checker, recur_func, forward_call)


def trim_leaves(state, leaf_x, leaf_y, leaf_z):
    def leaf_to_air(state, x, y, z):
        state[x][y][z] = 'minecraft:air'
    perform_on_adj_recursively(state, leaf_x, leaf_y, leaf_z, is_leaf, perform_on_adj_recursively, leaf_to_air)


def is_leaf(block_name):
    if block_name[-6:] == 'leaves':
        return True
    return False

def get_log_type(block_name):
    return block_name[10:-4]