import src.my_utils
import src.states
from enum import Enum
from random import randint, random, choice
import src.movement
import math
class TASK_OUTCOME(Enum):
    FAILURE = 0
    SUCCESS = 1
    IN_PROGRESS = 2
    REDO = 3


def grow_tree_at(state, x, y, z, times=1):
    growth_rate = 1
    y = state.rel_ground_hm[x][z]
    print("starting tree y is "+str(y))  # prolly bc cut_tree insn't updating it. does it have to do with passthrough?
    # get sapling type, or if that fails get nearest log type because sometimes there's no sapling here.
    type = ''
    if is_sapling(state, x, y, z):
        type = state.blocks[x][y][z][:-8] + "_log"  # I hope it's not "minecraft:..."
    elif is_log(state, x, y, z):  # get log underneath instead
        type = state.blocks[x][y][z]
    elif state.get_nearest_tree(x, z):  # get nearest log instead
        i = 0
        max = 20
        tx, tz = choice(state.get_nearest_tree(x, z))
        type = state.blocks[tx][y][tz]
        while state.blocks[tx][y][tz] not in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.TREE.value]:
            if i > max:
                type = "oak_log"
                break
            tx, tz = choice(state.get_nearest_tree(x, z))
            i+=1
            type = state.blocks[tx][y][tz]
    else:
        type = "oak_log"
    for i in range(growth_rate):
        print("placing "+type+" at "+state.blocks[x][y+i][z])
        src.states.set_state_block(state, x, y, z, type)



# A lorax-y, wind-swept style
def grow_leaves(state, x, tree_top_y, z, type, leaves_height):
    # create lorax-y trees, where the middle circles are largest or randomized
    xto = x + randint(-1,1)
    zto = z + randint(-1,1)
    xfrom = x + randint(-2,2)
    zfrom = z + randint(-2,2)
    r = tree_top_y - leaves_height  # diff/bottom of leaves
    for y in range(r+1, tree_top_y + 1):
        idx = y - r
        x = int( (((xto - xfrom)/r) * idx) + xfrom)
        z = int( (((zto - zfrom)/r) * idx) + zfrom)
        rad = randint(1,3)
        for lx in range(x-rad, xto+rad+1):
            for lz in range(z - rad, zto + rad + 1):
                if state.out_of_bounds_2D(lx, lz):
                    continue
                dist = math.dist((lx,lz), (x,z))
                if dist <= rad and not state.out_of_bounds_3D(lx,y,lz) and state.blocks[lx][y][lz] in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value]:
                    src.states.set_state_block(state, lx, y, lz, type)




def is_sapling(state, x, y, z):
    if state.out_of_bounds_3D(x, y, z):
        return False
    block = state.blocks[x][y][z]
    if not block is None and block[-7:] == 'sapling':
        return True
    return False



def is_water(state, x, y, z):
    if state.out_of_bounds_3D(x, y, z):
        return False
    block = state.blocks[x][y][z]
    print(block)
    if not block is None and block[-5:] == 'water':
        return True
    return False


def is_log(state, x, y, z):
    if state.out_of_bounds_3D(x, y, z):
        return False
    block = state.blocks[x][y][z]
    if not block is None and block[-3:] == 'log':
        return True
    return False




def collect_water_at(state, x, y, z, times=1):
    for i in range(times):
        pass
    return TASK_OUTCOME.SUCCESS.name  # basically always return success if found


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
            # find green around here
            new_x = x
            new_y = y
            new_z = z
            found_new_spot = False
            for dir in src.movement.directions:
                tx = x + dir[0]
                tz = z + dir[1]
                ttype = state.types[tx][tz]
                node = state.nodes[state.node_pointers[(tx,tz)]]
                if ttype == src.my_utils.TYPE.GREEN.name \
                    and node not in state.built: # check if right
                    new_x = tx
                    new_y = state.rel_ground_hm[tx][tz]
                    new_z = tz
                    found_new_spot = True
                    break
            new_replacement = "minecraft:" + log_type + "_sapling"
            # new_replacement = "minecraft:air"
            yoff = -1
            if state.blocks[x][y-1][z] == "minecraft:air":
                new_replacement = "minecraft:air"
                yoff = 0  # needs verification
            src.states.set_state_block(state, x, y, z, "minecraft:air")
            removed_tree_tile_type = state.determine_type(x, z, state.rel_ground_hm, yoff) # -1 to account for sapling
            state.types[x][z] = removed_tree_tile_type
            if (x,z) in state.trees:  # when sniped
                state.trees.remove((x,z))
            if found_new_spot:
                sapling_tile_type = state.determine_type(new_x, new_z, state.rel_ground_hm, yoff)  # -1 to account for sapling
                state.types[new_x][new_z] = sapling_tile_type
                src.states.set_state_block(state, new_x, new_y, new_z, new_replacement)
                state.saplings.append((new_x,new_z))
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
        # src.states.set_state_block(x,y,z, 'minecraft:air')
        src.states.set_state_block(state, x, y, z, 'minecraft:air')
    do_recur_on_adjacent(state, leaf_x, leaf_y, leaf_z, is_leaf, do_recur_on_adjacent, leaf_to_air)


def is_leaf(block_name):
    if not block_name is None and block_name[-6:] == 'leaves':
        return True
    return False


def get_log_type(block_name):
    return block_name[10:-4]


