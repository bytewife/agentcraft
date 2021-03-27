import src.my_utils

def is_log(state, x, y, z):
    block = state.blocks[x][y][z]
    if block[-3:] == 'log':
        return True
    return False


def cut_tree_at(state, x, y, z, times=1):
    for i in range(times):
        log_type = get_log_type(state.blocks[x][y][z])
        replacement = "minecraft:air"
        state.blocks[x][y][z] = replacement
        src.manipulation.set_state_block(state, x, y, z, replacement)
        if \
        is_leaf(state.get_adjacent_block(x, y, z, 0, 1, 0)) or \
        is_leaf(state.get_adjacent_block(x, y, z, 1, 0, 0)
        ):
            flood_kill_leaves(state, x, y + 1, z)
        if not is_log(state, x, y - 1, z):  # place sapling
            sapling = "minecraft:" + log_type + "_sapling"
            state.blocks[x][y][z] = sapling
            state.set_state_block(x, y, z, sapling)
            state.trees.remove((x,z))
        y -= 1


def do_recur_on_adjacent(state, x, y, z, target_block_checker, recur_func, forward_call):
    forward_call(state.blocks, x, y, z)
    adj_blocks = state.get_all_adjacent_blocks(x, y, z)
    for block in adj_blocks:
        if target_block_checker(block[0]):
            recur_func(state, block[1], block[2], block[3], target_block_checker, recur_func, forward_call)


def flood_kill_leaves(state, leaf_x, leaf_y, leaf_z):
    def leaf_to_air(blocks, x, y, z):
        blocks[x][y][z] = 'minecraft:air'
        state.set_state_block(x, y, z, 'minecraft:air')
    do_recur_on_adjacent(state, leaf_x, leaf_y, leaf_z, is_leaf, do_recur_on_adjacent, leaf_to_air)


def is_leaf(block_name):
    if block_name[-6:] == 'leaves':
        return True
    return False


def get_log_type(block_name):
    return block_name[10:-4]


def set_state_block(state, x, y, z, block_name):
    key = src.my_utils.convert_coords_to_key(x, y, z)
    print("before is ")
    state.changed_blocks[key] = block_name
