import src.my_utils
import src.states
from enum import Enum

class TASK_OUTCOME(Enum):
    FAILURE = 0
    SUCCESS = 1
    IN_PROGRESS = 2
    REDO = 3


def is_log(state, x, y, z):
    if state.out_of_bounds_3D(x, y, z):
        return False
    block = state.blocks[x][y][z]
    if not block is None and block[-3:] == 'log':
        return True
    return False


def cut_tree_at(state, x, y, z, times=1):
    for i in range(times):
        log_type = get_log_type(state.blocks[x][y][z])
        replacement = "minecraft:air"
        src.states.set_state_block(state, x, y, z, replacement)
        if is_leaf(state.get_adjacent_block(x, y, z, 0, 1, 0)) \
                  or is_leaf(state.get_adjacent_block(x, y, z, 1, 0, 0)) \
                  or is_leaf(state.get_adjacent_block(x, y, z, -1, 0, 0)) \
                  or is_leaf(state.get_adjacent_block(x, y, z, 0, 0, 1)) \
                  or is_leaf(state.get_adjacent_block(x, y, z, 0, 0, -1)):
              flood_kill_leaves(state, x, y + 1, z)
        if not is_log(state, x, y - 1, z):  # place sapling
            new_replacement = "minecraft:" + log_type + "_sapling"
            yoff = -1
            if state.blocks[x][y-1][z] == "minecraft:air":
                new_replacement = "minecraft:air"
                yoff = 0  # needs verification
            src.states.set_state_block(state, x, y, z, new_replacement)
            new_type = state.determine_type(x, z, state.rel_ground_hm, yoff) # -1 to account for sapling
            state.types[x][z] = new_type
            print("new state is "+str(state.types[x][z]))
            if (x,z) in state.trees:  # prevent sniping
                state.trees.remove((x,z))
            return TASK_OUTCOME.SUCCESS.name
        y -= 1
    return TASK_OUTCOME.IN_PROGRESS.name


def do_recur_on_adjacent(state, x, y, z, target_block_checker, recur_func, forward_call):
    forward_call(state.blocks, x, y, z)
    adj_blocks = state.get_all_adjacent_blocks(x, y, z)
    for block in adj_blocks:
        if target_block_checker(block[0]):
            recur_func(state, block[1], block[2], block[3], target_block_checker, recur_func, forward_call)


def flood_kill_leaves(state, leaf_x, leaf_y, leaf_z):
    def leaf_to_air(blocks, x, y, z):
        blocks[x][y][z] = 'minecraft:air'
        src.states.set_state_block(state, x, y, z, 'minecraft:air')
    do_recur_on_adjacent(state, leaf_x, leaf_y, leaf_z, is_leaf, do_recur_on_adjacent, leaf_to_air)


def is_leaf(block_name):
    if not block_name is None and block_name[-6:] == 'leaves':
        return True
    return False


def get_log_type(block_name):
    return block_name[10:-4]


