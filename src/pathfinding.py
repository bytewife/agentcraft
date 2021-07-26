#! /usr/bin/python3
"""
### A* Implementation with Dynamic Sector Precomputation Optimization
Based on Troy, Ryan, & Trent's implementation.
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"

from heapq import heappop, heappush, heappushpop
from math import sqrt

import bitarray
import numpy as np
from numpy import full_like
from scipy.spatial import KDTree

from bitarray.util import count_xor, rindex

import src.utils


class Pathfinding:
    """ A* Pathfinding with Sectoring """

    DIRECTIONS = {
        0: (1, 0),
        1: (0, 1),
        2: (-1, 0),
        3: (0, -1),
        4: (1, 1),
        5: (-1, 1),
        6: (-1, -1),
        7: (1, -1),
    }

    MAX_SECTOR_PROPAGATION_DEPTH = 10 * 150
    CARDINAL_COST = 100
    DIAGONAL_COST = 141
    DIRECTION_COSTS = {
        (0, 1): CARDINAL_COST,
        (-1, 0): CARDINAL_COST,
        (0, -1): CARDINAL_COST,
        (1, 0): CARDINAL_COST,
        (-1, 1): DIAGONAL_COST,
        (-1, -1): DIAGONAL_COST,
        (1, -1): DIAGONAL_COST,
        (1, 1): DIAGONAL_COST,
        (0, 0): 0,  # for starter only
    }

    def __init__(self, state):
        self.state = state
        self.sectors_nodes = {}
        self.n_sectors = 0
        self.sector_sizes = {}
        self.sectors = full_like(state.rel_ground_hm, -1, int)

    class PathNode:
        def __init__(self, pos, g=0.0, h=0.0, parent=None, legal_moves=None):
            self.pos = pos
            self.g = g
            self.parent = parent
            self.h = h
            self.f = g + h
            self.legal_actions = legal_moves
            self.sectors = []  # Optimization where we cache each blocks' reachability
            self.sector_sizes = {}

        def __lt__(self, other):  # required for heapq sort
            return self.f < other.f

    def search(self, start: tuple, goal: tuple, max_x, max_z, legal_moves):
        """
        Perform A* Search for path
        :param start:
        :param goal:
        :param max_x:
        :param max_z:
        :param legal_moves:
        :return:
        """
        first = self.PathNode(start, g=0, h=self.heuristic(*start, *goal), parent=None, legal_moves=legal_moves)
        open = [first]  # heap
        closed = set()
        g_lookup = {}
        while len(open) > 0:
            node = heappop(open)
            if node.pos[0] == goal[0] and node.pos[1] == goal[1]:
                return self.backwards_traverse(node, start)
            closed.add(node.pos)
            for child in self.expand(node, node.g, goal, legal_moves):
                if child.pos in closed:
                    continue
                if child.pos in g_lookup and g_lookup[child.pos] <= child.g:
                    continue
                g_lookup[child.pos] = child.g
                heappush(open, child)
        return []

    def calc_g(self, parent_pos, g_lookup, p_to_c_cost_action_cost, dir_cost):
        return g_lookup[parent_pos] + p_to_c_cost_action_cost + dir_cost

    def expand(self, parent: PathNode, parent_g: float, goal: tuple, all_legal_moves):
        """ Returns list of child PathNodes from adjacent tiles to parent """
        result = []
        curr_legal_moves = all_legal_moves[parent.pos[0], parent.pos[1]]
        for n in range(len(self.DIRECTIONS)):
            if not curr_legal_moves[n]:
                continue
            dx, dz = ALL_DIRS[n]
            new_pos = (parent.pos[0] + dx, parent.pos[1] + dz)
            if self.state.out_of_bounds_Node(*new_pos):
                continue
            action_cost = 0 if self.state.nodes(*self.state.node_pointers[new_pos]) in self.state.roads else 200
            result.append(self.PathNode(pos=new_pos,
                                        g=parent_g + action_cost + self.DIRECTION_COSTS[(dx, dz)],
                                        h=self.heuristic(*new_pos, goal[0], goal[1]),
                                        parent=parent,
                                        legal_moves=all_legal_moves[new_pos[0], new_pos[1]]))
        return result


    def backwards_traverse(self, node, end):
        """
        Build path from A*_Result
        :param node:
        :param end:
        :return:
        """
        curr = node
        path = []
        while curr.pos != end:
            path.append(curr.pos)
            curr = curr.parent
        return path

    def heuristic(self, x1, z1, x2, z2):
        return round(sqrt((x1 - x2) ** 2 + (z1 - z2) ** 2))

    def merge_sectors(self, state, sectors, to_remove, new):
        """
        Move blocks from one sector into another
        :param state:
        :param sectors:
        :param to_remove:
        :param new:
        :return:
        """
        for pos in self.sectors_nodes[to_remove]:
            sectors[pos[0]][pos[1]] = new
        self.sectors_nodes[new].update(self.sectors_nodes[to_remove])
        self.sectors_nodes.pop(to_remove)
        self.sector_sizes[new] += self.sector_sizes[to_remove]
        self.sector_sizes[to_remove] = 0

    def init_sectors(self, legal_moves):
        for x in range(len(legal_moves)):
            for z in range(len(legal_moves[0])):
                if self.sectors[x][z] == -1:
                    self.n_sectors +=1
                    self.sector_sizes[self.n_sectors] = 0
                    self.sectors_nodes[self.n_sectors] = set()
                    self.init_sector(x, z, self.n_sectors, self.sectors, legal_moves)
                z += 1
            x += 1
        return self.sectors

    def grow_sector_depth_limited(self, x: int, z: int, sector: int, sectors, sector_sizes: dict, legal_moves):
        """ Update sector up to MAX_SECTOR_PROPAGATION_DEPTH away (for performance) """
        open = [(x, z)]
        closed = set()
        if sector not in self.sectors_nodes.keys():
            self.sectors_nodes[sector] = set()
        depth_count = 0
        while len(open) > 0 and depth_count < self.MAX_SECTOR_PROPAGATION_DEPTH:
            pos = open.pop(0)
            nx, nz = pos
            prev_sector = self.sectors[nx][nz]
            sectors[nx][nz] = sector
            self.sectors_nodes[prev_sector].remove(pos)
            self.sectors_nodes[sector].add(pos)
            sector_sizes[prev_sector] -= 1
            sector_sizes[sector] += 1
            for n in range(8):  # 8 directions
                if legal_moves[nx][nz][n]:
                    dir = ALL_DIRS[n]
                    cx = nx + dir[0]
                    cz = nz + dir[1]
                    if cx < 0 or cx >= len(legal_moves) or cz < 0 or cz >= len(legal_moves[0]):
                        continue
                    childs_sector = sectors[cx][cz]
                    if childs_sector == -1:  # if the tile doesn't have a sector, add to list to expand
                        child_pos = (cx, cz)
                        if not child_pos in closed:
                            open.append(child_pos)
                        closed.add(child_pos)
                    elif childs_sector != sector:
                        child_pos = (cx, cz)
                        if not child_pos in closed:
                            open.append(child_pos)  # the or allows re-sectoring
                        closed.add(child_pos)
            depth_count += 1

    def add_to_sector(self, x, z, sector):
        self.sectors_nodes[sector].add((x,z))
        self.sector_sizes[sector] += 1
        self.sectors[x][z] = sector

    def init_sector(self, x: int, z: int, sector: int, sectors, legal_moves):
        """ Initialize all sectors """
        frontier = [(x, z)]
        closed = set()
        while frontier:
            pos = frontier.pop(0)
            nx, nz = pos
            self.add_to_sector(pos[0], pos[1], sector)
            for n in range(len(legal_moves[nx][nz])):
                if legal_moves[nx][nz][n]:
                    dir = ALL_DIRS[n]
                    cx = nx + dir[0]
                    cz = nz + dir[1]
                    if self.state.out_of_bounds_2D(cx, cz):
                        continue
                    if sectors[cx][cz] == -1:
                        child_pos = (cx,cz)
                        if child_pos not in closed:
                            frontier.append(child_pos)
                        closed.add(child_pos)

    def update_block_sector(self, x: int, z: int, sector_sizes: dict, legal_moves, old_legal_moves):
        """ Update the sector for a block based on whether they're newly reachable or unreachable from neighbors """
        if count_xor(legal_moves[x][z], old_legal_moves[x][z]) > 0:  # Any Move legality changed
            changed = legal_moves[x][z] ^ old_legal_moves[x][z]
            new_sector_created = False
            did_merge = False
            for i, bit in enumerate(changed):
                if bit == False:
                    continue
                dir = self.DIRECTIONS[i]
                ox = x+dir[0]
                oz = z+dir[1]
                if self.state.out_of_bounds_2D(ox, oz): continue
                if abs(self.state.rel_ground_hm[x][z] - self.state.rel_ground_hm[ox][oz]) <= self.state.AGENT_JUMP:
                    if not did_merge:
                        cur_sector = self.sectors[x][z]
                        other_sector = self.sectors[ox][oz]
                        if cur_sector == other_sector:
                            continue
                        sector_to_prop_into = cur_sector
                        sector_to_remove = other_sector
                        self.merge_sectors(self.state, self.sectors, sector_to_remove, sector_to_prop_into)
                        did_merge = True
                else:  # tiles are no longer connected, propagate into this tile's sector, append new sector
                    if not new_sector_created and self.sectors[x][z] == self.sectors[ox][oz]:
                        new_sector_created = True
            if new_sector_created:
                sector = self.sectors[x][z]
                self.sector_sizes[sector] -= 1
                self.sectors_nodes[sector].remove((x, z))
                self.n_sectors += 1
                self.sector_sizes[self.n_sectors] = 1
                self.sectors_nodes[self.n_sectors] = {(x, z)}
                self.sectors[x][z] = self.n_sectors
                self.grow_sector_depth_limited(x, z, sector=self.n_sectors, sectors=self.sectors,
                                               sector_sizes=sector_sizes, legal_moves=legal_moves)


def find_nearest(state, x: int, z: int, possibilities: list, start_radius: float, iterations=20, increment=1):
    """
    Use KDTree to find nearest position within given spots
    :return: list of nearby elements
    """
    if type(possibilities) != list or len(possibilities) <= 0:
        return []
    tree = KDTree(possibilities)
    for iteration in range(iterations):
        radius = start_radius + iteration * increment
        founds = tree.query_ball_point([x, z], r=radius)
        result = [possibilities[i] for i in founds if not state.out_of_bounds_Node(*possibilities[i])]
        if len(result) > 0:
            return result
    return []


# N    E      S       W
CARDINAL_DIRS = ([1, 0], [0, 1], [-1, 0], [0, -1])
# NE   ES     SW      WN
DIAGONAL_DIRS = ([1, 1], [-1, 1], [-1, -1], [1, -1])
ALL_DIRS = CARDINAL_DIRS + DIAGONAL_DIRS


def gen_all_legal_moves(state, vertical_ability, heightmap, actor_height, unwalkable_blocks):
    """
    Initialize all legal actions (i.e. bools for each block determining traversability to neighbors
    :param state:
    :param vertical_ability:
    :param heightmap:
    :param actor_height:
    :param unwalkable_blocks:
    :return:
    """
    fill = bitarray.util.zeros(8)
    result = np.full((state.len_x,state.len_z), fill_value=fill, dtype=bitarray.bitarray)
    for x in range(state.len_x):
        for z in range(state.len_z):
            result[x][z] = get_block_legal_moves(state, x, z, vertical_ability, heightmap, actor_height,
                                                 unwalkable_blocks)
    return result


def get_block_legal_moves(state, x, z, vertical_ability, heightmap, actor_height, unwalkable_blocks):
    result = bitarray.util.zeros(8)
    y = heightmap[x][z]
    for n in range(4): # amt of cardinal directions
        result[n] = check_if_legal_move(state, x, y, z, CARDINAL_DIRS[n][0], CARDINAL_DIRS[n][1], vertical_ability,
                                        heightmap, actor_height, unwalkable_blocks)
    for n in range(4): # amt of diagonal directions
        if result[n] and result[(n+1) % 4]:
            result[n + 4] = check_if_legal_move(state, x, y, z, DIAGONAL_DIRS[n][0], DIAGONAL_DIRS[n][1],
                                                vertical_ability, heightmap, actor_height, unwalkable_blocks)
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