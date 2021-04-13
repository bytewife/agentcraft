# from states import *
import bitarray
import numpy as np
import src.my_utils
from enum import Enum
from scipy.spatial import KDTree
from math import dist


class Directions(Enum):
    N  = 0
    E  = 1
    S  = 2
    W  = 3
    NE = 4
    ES = 5
    SW = 6
    WN = 7

DeltaToDirIdx = {
    (1,0): 0,
    (0, 1): 1,
    (-1, 0): 2,
    (0, -1): 3,
    (1, 1): 4,
    (-1, 1): 5,
    (-1, -1): 6,
    (1, -1): 7,
}

    # N    E      S       W
cardinals = ([1,0],[0,1], [-1,0], [0,-1])
            # NE   ES     SW      WN
diagonals = ([1,1],[-1,1],[-1,-1],[1,-1])
directions = cardinals + diagonals
idirections = cardinals + diagonals + ([0,0],)
# directions = cardinals + diagonals + ()
## stored as N  E  S  W  NE ES SW WN
##           0  1  2  3  4  5  6  7


def gen_all_legal_actions(blocks, vertical_ability, heightmap, actor_height, unwalkable_blocks):
    rx = len(blocks)
    rz = len(blocks[0][0])
    # print(rx)
    fill = bitarray.bitarray('00000000')
    result = np.full((rx,rz), fill_value=fill, dtype=bitarray.bitarray)
    for x in range(rx):
        for z in range(rz):
            # pass
            result[x][z] = get_legal_actions_from_block(blocks, x, z, vertical_ability, heightmap, actor_height, unwalkable_blocks)
    return result


def get_legal_actions_from_block(blocks, x, z, vertical_ability, heightmap, actor_height, unwalkable_blocks):
    result = bitarray.bitarray('00000000')
    # the choice of heightmap here is important. It should be the on the ground, not 1 block above imo
    y = heightmap[x][z]
    for n in range(len(cardinals)):
        cardinal = cardinals[n]
        if check_if_legal_move(blocks, x, y, z, *cardinal, vertical_ability, heightmap, actor_height, unwalkable_blocks):
            result[n] = True
    for n in range(len(diagonals)):
        if result[n] is True and result[(n+1) % len(cardinals)] is True:  # Make sure the surrounding walls of the diagonal are passable to avoid skipping
            diagonal = diagonals[n]
            if check_if_legal_move(blocks, x, y, z, *diagonal, vertical_ability, heightmap, actor_height, unwalkable_blocks):
                result[n + 4] = True
    return result


def check_if_legal_move(blocks, x, y, z, x_offset, z_offset, jump_ability, heightmap, actor_height, unwalkable_blocks):
    y_max = len(blocks[0]) - 1
    target_x = x + x_offset
    target_z = z + z_offset
    if (target_x < 0 or target_z < 0 or target_x >= len(blocks) or target_z >= len(blocks[0][0])):
        return False
    target_y = heightmap[target_x][target_z]# make sure that the heightmap starts from the ground
    target_block = blocks[target_x][target_y - 1][target_z]
    if target_block in unwalkable_blocks: return False
    y_diff = abs(y - target_y)
    if y_diff > jump_ability: return False
    is_legal = True
    for i in range(0, actor_height):
        open_space = target_y + i
        if open_space > y_max: return False  # out of bounds
        target = blocks[target_x][target_y + i][target_z]
        # find [] and remove it
        if '[' in target:
            idx = target.index('[')
            target = target[:idx]
        if not (target in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value]):
            is_legal = False
            break
    if is_legal:
        return True
    return False


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


def find_nearest(x, z, spot_coords, starting_search_radius, max_iterations=20, radius_inc=1): # can be used at a sort
    if len(spot_coords) <= 0: return
    kdtree = KDTree(spot_coords)
    for iteration in range(max_iterations):
        radius = starting_search_radius + iteration * radius_inc
        idx = kdtree.query_ball_point([x, z], r=radius)
        if len(idx) > 0:
            result = []
            for i in idx:
                result.append(spot_coords[i])
            return result
    return []


def sort_by_distance(x, z, block_coords):
    dists = np.full_like(np.arange(len(block_coords), dtype=float), 0)
    dict = {}
    # put dists as keys in dict, value as index
    for n in range(len(block_coords)):
        _dist = dist((x, z), block_coords[n])
        dists[n] = _dist
        if not _dist in dict:
            dict[_dist] = [n]
        else:
            dict[_dist].append(n)
    dists.sort()
    # put indices in array in ascending
    indices = []
    for _dist in dists:
        for i in range(len(dict[_dist])):
            next = dict[_dist][i]
            indices.append(next)
    # get block coords
    result = [0] * len(block_coords)
    for n in indices:
        print(n)
        result[i] = ((block_coords[n]))
        i+=1
    return result






