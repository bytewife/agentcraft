#! /usr/bin/python3
"""### Block Manipulation
Some misc functions on modifying individual blocks in the State.
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"


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


grow_type = 'oak_log'
def grow_tree_at(state, x, y, z, times=1):
    growth_rate = 1
    y = state.rel_ground_hm[x][z]
    # get sapling type, or if that fails get nearest log type because sometimes there's no sapling here.
    type = grow_type+'_log'
    for i in range(growth_rate):
        src.states.set_state_block(state, x, y, z, type)



# A lorax-y, wind-swept style
def grow_leaves(state, x, tree_top_y, z, type, leaves_height):
    # create lorax-y trees, where the middle circles are largest or randomized
    xto = x + randint(-1,1)
    zto = z + randint(-1,1)
    xfrom = x + randint(-2,2)
    zfrom = z + randint(-2,2)
    r = max(1, tree_top_y - leaves_height)  # diff/bottom of leaves.  max bc there was a division by 0
    for y in range(r+1, tree_top_y + 1):
        idx =y - r
        x = int( (((xto - xfrom)/r) * idx) + xfrom)
        z = int( (((zto - zfrom)/r) * idx) + zfrom)
        rad = randint(1,3)
        for lx in range(x-rad, xto+rad+1):
            for lz in range(z - rad, zto + rad + 1):
                if state.out_of_bounds_2D(lx, lz):
                    continue
                dist = math.dist((lx,lz), (x,z))
                if dist <= rad and not state.out_of_bounds_3D(lx,y,lz) and state.blocks(lx,y,lz )in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value]:
                    src.states.set_state_block(state, lx, y, lz, type)




def is_sapling(state, x, y, z):
    if state.out_of_bounds_3D(x, y, z):
        return False
    block = state.blocks(x,y,z)
    return block in {
        "minecraft:oak_sapling",
        "minecraft:oak_sapling[stage=0]",
        "minecraft:oak_sapling[stage=1]",
        "minecraft:oak_sapling[stage=2]",
        "minecraft:oak_sapling[stage=3]",
        "minecraft:spruce_sapling",
        "minecraft:spruce_sapling[stage=0]",
        "minecraft:spruce_sapling[stage=1]",
        "minecraft:spruce_sapling[stage=2]",
        "minecraft:spruce_sapling[stage=3]",
        "minecraft:birch_sapling",
        "minecraft:birch_sapling[stage=0]",
        "minecraft:birch_sapling[stage=1]",
        "minecraft:birch_sapling[stage=2]",
        "minecraft:birch_sapling[stage=3]",
        "minecraft:jungle_sapling",
        "minecraft:jungle_sapling[stage=0]",
        "minecraft:jungle_sapling[stage=1]",
        "minecraft:jungle_sapling[stage=2]",
        "minecraft:jungle_sapling[stage=3]",
        "minecraft:acacia_sapling",
        "minecraft:acacia_sapling[stage=0]",
        "minecraft:acacia_sapling[stage=1]",
        "minecraft:acacia_sapling[stage=2]",
        "minecraft:acacia_sapling[stage=3]",
        "minecraft:dark_oak_sapling",
        "minecraft:dark_oak_sapling[stage=0]",
        "minecraft:dark_oak_sapling[stage=1]",
        "minecraft:dark_oak_sapling[stage=2]",
        "minecraft:dark_oak_sapling[stage=3]",
        "minecraft:oak_sapling",
        "minecraft:oak_sapling[stage=0]",
        "minecraft:oak_sapling[stage=1]",
        "minecraft:oak_sapling[stage=2]",
        "minecraft:oak_sapling[stage=3]",
        "minecraft:spruce_sapling",
        "minecraft:spruce_sapling[stage=0]",
        "minecraft:spruce_sapling[stage=1]",
        "minecraft:spruce_sapling[stage=2]",
        "minecraft:spruce_sapling[stage=3]",
        "minecraft:birch_sapling",
        "minecraft:birch_sapling[stage=0]",
        "minecraft:birch_sapling[stage=1]",
        "minecraft:birch_sapling[stage=2]",
        "minecraft:birch_sapling[stage=3]",
        "minecraft:jungle_sapling",
        "minecraft:jungle_sapling[stage=0]",
        "minecraft:jungle_sapling[stage=1]",
        "minecraft:jungle_sapling[stage=2]",
        "minecraft:jungle_sapling[stage=3]",
        "minecraft:acacia_sapling",
        "minecraft:acacia_sapling[stage=0]",
        "minecraft:acacia_sapling[stage=1]",
        "minecraft:acacia_sapling[stage=2]",
        "minecraft:acacia_sapling[stage=3]",
        "minecraft:dark_oak_sapling",
        "minecraft:dark_oak_sapling[stage=0]",
        "minecraft:dark_oak_sapling[stage=1]",
        "minecraft:dark_oak_sapling[stage=2]",
        "minecraft:dark_oak_sapling[stage=3]",

        "oak_sapling",
        "oak_sapling[stage=0]",
        "oak_sapling[stage=1]",
        "oak_sapling[stage=2]",
        "oak_sapling[stage=3]",
        "spruce_sapling",
        "spruce_sapling[stage=0]",
        "spruce_sapling[stage=1]",
        "spruce_sapling[stage=2]",
        "spruce_sapling[stage=3]",
        "birch_sapling",
        "birch_sapling[stage=0]",
        "birch_sapling[stage=1]",
        "birch_sapling[stage=2]",
        "birch_sapling[stage=3]",
        "jungle_sapling",
        "jungle_sapling[stage=0]",
        "jungle_sapling[stage=1]",
        "jungle_sapling[stage=2]",
        "jungle_sapling[stage=3]",
        "acacia_sapling",
        "acacia_sapling[stage=0]",
        "acacia_sapling[stage=1]",
        "acacia_sapling[stage=2]",
        "acacia_sapling[stage=3]",
        "dark_oak_sapling",
        "dark_oak_sapling[stage=0]",
        "dark_oak_sapling[stage=1]",
        "dark_oak_sapling[stage=2]",
        "dark_oak_sapling[stage=3]",
    }


def is_water(state, x, y, z):
    if state.out_of_bounds_3D(x, y, z):
        return False
    return state.blocks(x,y,z) in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.WATER.value]


def is_log(state, x, y, z):
    if state.out_of_bounds_3D(x, y, z):
        return False
    block = state.blocks(x,y,z)
    return block in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.TREE.value]


def collect_water_at(state, x, y, z, times=1):
    for i in range(times):
        pass
    return TASK_OUTCOME.SUCCESS.name  # basically always return success if found


def cut_tree_at(state, x, y, z, times=1):
    for i in range(times):
        # get log type
        block = state.blocks(x, y, z)
        start = 0
        if 'mine' in block[:4]:
            start = block.index(':')+1
        end = block.index('_')
        block = block[start:end]  # change replenish type
        log_type = block
        # print("log type being "+log_type)

        replacement = "minecraft:air"
        src.states.set_state_block(state, x, y, z, replacement)
        if is_leaf(state.get_adjacent_block(x, y, z, 0, 1, 0)) \
                  or is_leaf(state.get_adjacent_block(x, y, z, 1, 0, 0)) \
                  or is_leaf(state.get_adjacent_block(x, y, z, -1, 0, 0)) \
                  or is_leaf(state.get_adjacent_block(x, y, z, 0, 0, 1)) \
                  or is_leaf(state.get_adjacent_block(x, y, z, 0, 0, -1)):
              flood_kill_leaves(state, x, y + 1, z, 0)
        if not is_log(state, x, y - 1, z):  # place sapling
            # find green around here
            new_x = x
            new_y = y
            new_z = z
            found_new_spot = False
            if log_type[0] == 'j':  # because of how minecraft's heightmap doesn't consider leaves as air, put jungle saplings in same spot
                found_new_spot = True
            else:
                for dir in src.movement.directions:
                    tx = x + dir[0]
                    tz = z + dir[1]
                    if state.out_of_bounds_2D(tx,tz):
                        continue
                    ttype = state.types[tx][tz]
                    node_ptr = state.node_pointers[(tx,tz)]
                    if node_ptr == None: continue
                    node = state.nodes(*node_ptr)
                    if ttype == src.my_utils.TYPE.GREEN.name \
                        and node not in state.built \
                        and node not in state.roads: # check if right
                        new_x = tx
                        new_y = state.rel_ground_hm[tx][tz]
                        new_z = tz
                        found_new_spot = True
                        break
            new_replacement = "minecraft:" + log_type + "_sapling"
            # new_replacement = "minecraft:air"
            yoff = -1
            if state.blocks(x,y-1,z )== "minecraft:air":
                new_replacement = "minecraft:air"
                yoff = 0  # needs verification
            src.states.set_state_block(state, x, y, z, "minecraft:air")
            removed_tree_tile_type = state.determine_type(x, z, state.rel_ground_hm, yoff) # -1 to account for sapling
            state.types[x][z] = removed_tree_tile_type.name
            if (x,z) in state.trees:  # when sniped
                state.trees.remove((x,z))
            if found_new_spot:
                sapling_tile_type = state.determine_type(new_x, new_z, state.rel_ground_hm, yoff)  # -1 to account for sapling
                state.types[new_x][new_z] = sapling_tile_type.name
                src.states.set_state_block(state, new_x, new_y, new_z, new_replacement)
                state.saplings.append((new_x,new_z))
            return TASK_OUTCOME.SUCCESS.name
        y -= 1
    return TASK_OUTCOME.IN_PROGRESS.name


def do_recur_on_adjacent(state, x, y, z, target_block_checker, recur_func, forward_call, itr):
    if itr > 10: return
    forward_call(state, x, y, z)
    adj_blocks = state.get_all_adjacent_blocks(x, y, z)
    for block in adj_blocks:
        if target_block_checker(block[0]):
            itr+=1
            recur_func(state, block[1], block[2], block[3], target_block_checker, recur_func, forward_call, itr)


def flood_kill_leaves(state, leaf_x, leaf_y, leaf_z, itr):
    def leaf_to_air(state, x, y, z):
        # src.states.set_state_block(x,y,z, 'minecraft:air')
        src.states.set_state_block(state, x, y, z, 'minecraft:air')
    do_recur_on_adjacent(state, leaf_x, leaf_y, leaf_z, is_leaf, do_recur_on_adjacent, leaf_to_air, itr)


def is_log_flood(block):
    return block in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.TREE.value]

def flood_kill_logs(state, log_x, log_y, log_z, itr=12):
    def to_air(state, x, y, z):
        src.states.set_state_block(state, x, y, z, 'minecraft:air')
    do_recur_on_adjacent(state, log_x, log_y, log_z, is_log_flood, do_recur_on_adjacent, to_air, itr)


def is_leaf(block_name):
    return block_name in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.LEAVES.value]


def get_log_type(block_name):
    return block_name[10:-4]


