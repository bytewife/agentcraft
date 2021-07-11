#! /usr/bin/python3
"""### Legal movement action computations for agents
Pre-computations for where agents can and can't go.
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"

import bitarray
import bitarray.util
import numpy as np
import src.utils

# N    E      S       W
CARDINAL_DIRS = ([1, 0], [0, 1], [-1, 0], [0, -1])
            # NE   ES     SW      WN
DIAGONAL_DIRS = ([1, 1], [-1, 1], [-1, -1], [1, -1])
ALL_DIRS = CARDINAL_DIRS + DIAGONAL_DIRS

def gen_all_legal_actions(state, blocks, vertical_ability, heightmap, actor_height, unwalkable_blocks):
    """
    Initialize all legal actions (i.e. bools for each block determining traversability to neighbors
    :param state:
    :param blocks:
    :param vertical_ability:
    :param heightmap:
    :param actor_height:
    :param unwalkable_blocks:
    :return:
    """
    rx = len(blocks)
    rz = len(blocks[0][0])
    fill = bitarray.util.zeros(8)
    result = np.full((rx,rz), fill_value=fill, dtype=bitarray.bitarray)
    for x in range(rx):
        for z in range(rz):
            result[x][z] = get_legal_actions_from_block(state, blocks, x, z, vertical_ability, heightmap, actor_height, unwalkable_blocks)
    return result

def get_legal_actions_from_block(state, blocks, x, z, vertical_ability, heightmap, actor_height, unwalkable_blocks):
    result = bitarray.util.zeros(8)
    y = heightmap[x][z]
    for n in range(4): # amt of cardinal directions
        result[n] = check_if_legal_move(state, x, y, z, CARDINAL_DIRS[n][0], CARDINAL_DIRS[n][1], vertical_ability, heightmap, actor_height, unwalkable_blocks)
    for n in range(4): # amt of diagonal directions
        if result[n] and result[(n+1) % 4]:  # Make sure the surrounding walls of the diagonal are passable to avoid skipping
            result[n + 4] = check_if_legal_move(state, x, y, z, DIAGONAL_DIRS[n][0], DIAGONAL_DIRS[n][1], vertical_ability, heightmap, actor_height, unwalkable_blocks)
    return result

def check_if_legal_move(state, x, y, z, x_offset, z_offset, jump_ability, heightmap, actor_height, unwalkable_blocks):
    """
    Return T/F for whether can move from first block to next block
    :param state:
    :param x:
    :param y:
    :param z:
    :param x_offset:
    :param z_offset:
    :param jump_ability:
    :param heightmap:
    :param actor_height:
    :param unwalkable_blocks:
    :return:
    """
    target_x = x + x_offset
    target_z = z + z_offset
    if state.out_of_bounds_2D(target_x, target_z):
        return False
    target_y = heightmap[target_x][target_z]# make sure that the heightmap starts from the ground
    target_block = state.blocks(target_x,target_y - 1,target_z)
    if target_block in unwalkable_blocks: return False
    if abs(y - target_y) > jump_ability: return False
    if target_y + 1 > state.len_y-1: return False  # out of bounds
    target = state.blocks(target_x,target_y + 1,target_z)
    if not ':' in target:
        target = "minecraft:"+target
    if target[-1] == ']':
        target = target[:target.index('[')]
    return target in src.utils.BLOCK_TYPE.tile_sets[src.utils.TYPE.PASSTHROUGH.value]  # door is finnicky here

def get_pos_adjacents(state, x, z):
    """
    Generate 8 coordinate neighbors
    :param state:
    :param x:
    :param z:
    :return:
    """
    adjacents = []
    for dir in DIAGONAL_DIRS:  # was directions.
        ax, az = x+dir[0], z+dir[1]
        if state.out_of_bounds_2D(ax, az):
            continue
        adjacents.append((ax, az))
    for dir in CARDINAL_DIRS:  # was directions.
        ax, az = x+dir[0], z+dir[1]
        if state.out_of_bounds_2D(ax, az):
            continue
        adjacents.append((ax, az))
    return adjacents


