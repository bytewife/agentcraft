#! /usr/bin/python3
"""### Legal movement action computations for agents
Pre-computations for where agents can and can't go.
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"

# from states import *
import bitarray
import bitarray.util
import numpy as np
import src.my_utils
from enum import Enum
from scipy.spatial import KDTree
from math import dist

Directions = {
    0: (1,0),
    1: (0, 1),
    2: (-1, 0),
    3: (0, -1),
    4: (1, 1),
    5: (-1, 1),
    6: (-1, -1),
    7: (1, -1),
}

DeltaToDirIdx = {
    (1,0): 0,
    (0, 1): 1,
    (-1, 0): 2,
    (0, -1): 3,
    (1, 1): 4,
    (-1, 1): 5,
    (-1, -1): 6,
    (1, -1): 7,
    (1, -1): 7,
    (0, 0): 0,
}

    # N    E      S       W
cardinals = ([1,0],[0,1], [-1,0], [0,-1])
            # NE   ES     SW      WN
diagonals = ([1,1],[-1,1],[-1,-1],[1,-1])
directions = cardinals + diagonals
# directions = cardinals + diagonals + ()
## stored as N  E  S  W  NE ES SW WN
##           0  1  2  3  4  5  6  7

def gen_all_legal_actions(state, blocks, vertical_ability, heightmap, actor_height, unwalkable_blocks):
    rx = len(blocks)
    rz = len(blocks[0][0])
    # print(rx)
    fill = bitarray.util.zeros(8)
    result = np.full((rx,rz), fill_value=fill, dtype=bitarray.bitarray)
    for x in range(rx):
        for z in range(rz):
            # pass
            result[x][z] = get_legal_actions_from_block(state, blocks, x, z, vertical_ability, heightmap, actor_height, unwalkable_blocks)
    return result


def get_legal_actions_from_block(state, blocks, x, z, vertical_ability, heightmap, actor_height, unwalkable_blocks):
    result = bitarray.util.zeros(8)
    # the choice of heightmap here is important. It should be the on the ground, not 1 block above imo
    y = heightmap[x][z]
    for n in range(4): # amt of cardinal directions
        result[n] = check_if_legal_move(state, x, y, z, cardinals[n][0], cardinals[n][1], vertical_ability, heightmap, actor_height, unwalkable_blocks)
    for n in range(4): # amt of diagonal directions
        if result[n] and result[(n+1) % 4]:  # Make sure the surrounding walls of the diagonal are passable to avoid skipping
            result[n + 4] = check_if_legal_move(state, x, y, z, diagonals[n][0], diagonals[n][1], vertical_ability, heightmap, actor_height, unwalkable_blocks)
    return result

def check_if_legal_move(state, x, y, z, x_offset, z_offset, jump_ability, heightmap, actor_height, unwalkable_blocks):
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
    return target in src.my_utils.BLOCK_TYPE.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value]  # door is finnicky here

def adjacents(state, x, z):
    adjacents = []
    for dir in diagonals:  # was directions.
        ax, az = x+dir[0], z+dir[1]
        if state.out_of_bounds_2D(ax, az):
            continue
        adjacents.append((ax, az))
    for dir in cardinals:  # was directions.
        ax, az = x+dir[0], z+dir[1]
        if state.out_of_bounds_2D(ax, az):
            continue
        adjacents.append((ax, az))
    return adjacents


def find_nearest(state, x, z, spot_coords, starting_search_radius, max_iterations=20, radius_inc=1): # can be used at a sort
    if type(spot_coords) != list or len(spot_coords) <= 0: return []
    kdtree = KDTree(spot_coords)
    for iteration in range(max_iterations):
        radius = starting_search_radius + iteration * radius_inc
        idx = kdtree.query_ball_point([x, z], r=radius)
        if len(idx) > 0:
            result = []
            # result = {}
            for i in idx:
                if (state.out_of_bounds_Node(*spot_coords[i])): continue
                result.append(spot_coords[i])
                # result[spot_coords[i]] = 0
            return result
    return []