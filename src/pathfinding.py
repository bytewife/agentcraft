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
from numpy import full_like
from scipy.spatial import KDTree

import src.legal
from bitarray.util import count_xor, rindex

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
        pass

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
        curr_legal_actions = all_legal_moves[parent.pos[0], parent.pos[1]]
        for n in range(len(self.DIRECTIONS)):
            if not curr_legal_actions[n]:
                continue
            dx, dz = src.legal.ALL_DIRS[n]
            new_pos = (parent.pos[0] + dx, parent.pos[1] + dz)
            if self.state.out_of_bounds_Node(*new_pos):
                continue
            action_cost = 0 if self.state.nodes(*self.state.node_pointers[new_pos]) in self.state.roads else 200
            result.append(self.PathNode(new_pos,
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

    def create_sectors(self, heightmap, legal_moves):
        self.sectors = full_like(heightmap, -1, int)
        self.n_sectors = 0
        self.sector_sizes = {}
        for x in range(len(legal_moves)):
            for z in range(len(legal_moves[0])):
                if self.sectors[x][z] == -1:
                    self.n_sectors +=1
                    self.sector_sizes[self.n_sectors] = 0
                    self.sectors_nodes[self.n_sectors] = set()
                    self.init_propagate_sector(x, z, self.n_sectors, self.sectors, self.sector_sizes, legal_moves)
                z += 1
            x += 1
        return self.sectors

    def propagate_sector_depth_limited(self, x, z, sector, sectors, sector_sizes, legal_moves, is_redoing=False):
        """
        Update sector up to MAX_SECTOR_PROPAGATION_DEPTH away (for performance)
        :param x:
        :param z:
        :param sector:
        :param sectors:
        :param sector_sizes:
        :param legal_moves:
        :param is_redoing:
        :return:
        """
        open = [(x, z)]
        closed = set()
        if sector not in self.sectors_nodes.keys():
            self.sectors_nodes[sector] = set()
        depth_count = 0
        while len(open) > 0 and depth_count < self.MAX_SECTOR_PROPAGATION_DEPTH:  # search all adjacent until you cant go anymore
            pos = open.pop(0)
            nx, nz = pos
            if not is_redoing and sectors[nx][nz] != -1:
                continue
            prev_sector = self.sectors[nx][nz]
            sectors[nx][nz] = sector
            self.sectors_nodes[prev_sector].remove(pos)
            self.sectors_nodes[sector].add(pos)
            sector_sizes[prev_sector] -= 1
            sector_sizes[sector] += 1
            for n in range(8):  # check tiles reachable from here
                if legal_moves[nx][nz][n] == True:
                    dir = src.legal.ALL_DIRS[n]
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
            depth_count+=1

    def add_to_sector(self, x, z, sector):
        self.sectors_nodes[sector].add((x,z))
        self.sector_sizes[sector] += 1
        self.sectors[x][z] = sector

    def init_propagate_sector(self, x, z, sector, sectors, sector_sizes, legal_moves, is_redoing=False):
        """
        Initialize all sectors
        :param x:
        :param z:
        :param sector:
        :param sectors:
        :param sector_sizes:
        :param legal_moves:
        :param is_redoing:
        :return:
        """
        open = [(x, z)]
        closed = set()
        while len(open) > 0:  # search all adjacent until you cant go anymore
            pos = open.pop(0)
            nx, nz = pos
            self.add_to_sector(pos[0], pos[1], sector)
            for n in range(len(legal_moves[nx][nz])):  # check tiles reachable from here
                if legal_moves[nx][nz][n]:
                    dir = src.legal.ALL_DIRS[n]
                    cx = nx + dir[0]
                    cz = nz + dir[1]
                    if self.state.out_of_bounds_2D(cx, cz): continue
                    if sectors[cx][cz] == -1:  # if the tile doesn't have a sector, add to list to expand
                        child_pos = (cx,cz)
                        if not child_pos in closed:
                            open.append(child_pos)
                        closed.add(child_pos)

    def update_sector_for_block(self, x, z, sectors, sector_sizes, legal_moves, old_legal_actions):
        """
        Update the sector for a block based on whether they're newly reachable or unreachable from neighbors
        :param x:
        :param z:
        :param sectors:
        :param sector_sizes:
        :param legal_moves:
        :param old_legal_actions:
        :return:
        """
        if count_xor(legal_moves[x][z], old_legal_actions[x][z]) > 0:
            changed = legal_moves[x][z] ^ old_legal_actions[x][z]
            i = 0
            new_sector_created = False
            did_merge = False
            for bit in changed:
                if bit == False: continue
                dir = self.DIRECTIONS[i]
                i += 1
                ox = x+dir[0]
                oz = z+dir[1]
                if self.state.out_of_bounds_2D(ox, oz): continue
                if abs(self.state.rel_ground_hm[x][z] - self.state.rel_ground_hm[ox][oz]) <= self.state.AGENT_JUMP: # can now go here after not being able to
                    if not did_merge:
                        sector = self.sectors[x][z]
                        osector = self.sectors[ox][oz]
                        if sector == osector: continue
                        sector_to_prop_into = sector
                        sector_to_remove = osector
                        self.merge_sectors(self.state, self.sectors, sector_to_remove, sector_to_prop_into)
                        did_merge = True
                else:  # tiles are no longer connected, propagate into this tile's sector, append new sector
                    if not new_sector_created:
                        if self.sectors[x][z] != self.sectors[ox][oz]:  # already done
                            continue
                        new_sector_created = True
            if new_sector_created:
                sector = self.sectors[x][z]
                self.sector_sizes[sector] -= 1
                self.sectors_nodes[sector].remove((x, z))
                self.n_sectors += 1
                self.sector_sizes[self.n_sectors] = 1
                self.sectors_nodes[self.n_sectors] = {(x, z)}
                self.sectors[x][z] = self.n_sectors
                self.propagate_sector_depth_limited(x, z, sector=self.n_sectors, sectors=self.sectors, sector_sizes=sector_sizes, legal_moves=legal_moves, is_redoing=True)


# def find_nearest(state, x, z, choices: list, start_radius: 0.0, iterations=20, increment=1):
def find_nearest(state, x, z, spot_coords, starting_search_radius, max_iterations=20, radius_inc=1): # can be used at a sort
    """
    Use KDTree to find nearest position within given spots
    :param state:
    :param x:
    :param z:
    :param spot_coords:
    :param starting_search_radius:
    :param max_iterations:
    :param radius_inc:
    :return:
    """
    if type(spot_coords) != list or len(spot_coords) <= 0: return []
    kdtree = KDTree(spot_coords)
    for iteration in range(max_iterations):
        radius = starting_search_radius + iteration * radius_inc
        idx = kdtree.query_ball_point([x, z], r=radius)
        if len(idx) > 0:
            result = []
            for i in idx:
                if (state.out_of_bounds_Node(*spot_coords[i])): continue
                result.append(spot_coords[i])
            return result
    return []
