
#! /usr/bin/python3
"""### Legal movement action computations for agents
Pre-computations for where agents can and can't go. This portion is built on, and modified from, Troy, Ryan, & Trent's 2020 GDMC entry.
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"


from heapq import heappop, heappush, heappushpop
from math import sqrt
from numpy import full_like
import src.movement
from bitarray.util import count_xor, rindex

MAX_SECTOR_PROPAGATION_DEPTH = 10*150
cardinal_cost = 100
diagonal_cost = 141
path_cost_diff = abs(diagonal_cost - cardinal_cost)
path_cost_lookup = {
    (0, 1): cardinal_cost,
    (-1, 0): cardinal_cost,
    (0, -1): cardinal_cost,
    (1, 0): cardinal_cost,
    (-1, 1): diagonal_cost,
    (-1, -1): diagonal_cost,
    (1, -1): diagonal_cost,
    (1, 1): diagonal_cost,
    (0, 0): 0,  # for starter only
}
a = 0


class Pathfinding:

    def __init__(self, state):
        self.state = state
        self.sectors_nodes = {}
        pass


    class PathNode:
        def __init__(self, state, pos, g=0, h=0, parent=None, action_to_here=0, action_cost=0, legal_actions=0):
            self.pos = pos
            self.g = g
            self.parent = parent
            self.h = h
            self.f = g + h
            self.parent = parent
            self.action_to_here = action_to_here
            nptr = state.node_pointers[pos]
            # todo this might be expensive because it inits all nodes?
            self.action_cost = action_cost
            # if state.node_pointers[pos] is None:
            #     self.action_cost = 100
            # else:
            #     self.action_cost = state.nodes[state.node_pointers[pos]].action_cost
            self.legal_actions = legal_actions
            self.sectors = []
            self.sector_sizes = {}

        def __lt__(self, other):  # required for heapq sort
            return self.f < other.f


    def calc_g(self, parent_pos, g_lookup, p_to_c_cost_action_cost, dir_cost):
        return g_lookup[parent_pos] + p_to_c_cost_action_cost + dir_cost


    i = 0
    ## this method is a bottleneck so its uglified sorta
    def expand(self, parent : PathNode, parent_g, goal, max_x, max_z, all_legal_actions, g_lookup):  # TODO integtrate legal actions here
        """
        Creates child PathNodes from adjacent tiles to parent
        """
        children = []
        x, z = parent.pos
        curr_legal_actions = all_legal_actions[x][z]
        for n in range(8):  # num of diff moves
            if curr_legal_actions[n] == False: continue
            dx = src.movement.directions[n][0]
            dz = src.movement.directions[n][1]
            tx = parent.pos[0] + dx
            tz = parent.pos[1] + dz
            if tx < 0 or tz < 0 or tx > max_x or tz > max_z:
                continue
            nptr = self.state.node_pointers[(tx, tz)]
            action_cost = 0 if nptr is not None and self.state.nodes(*nptr) in self.state.roads else 200
            #     self.action_cost = 100
            # else:
            #     self.action_cost = state.nodes[state.node_pointers[pos]].action_cost
            # g= parent_g + action_cost +
            g = parent_g + action_cost + path_cost_lookup[(dx, dz)]
            # print(str(g))
            # g = parent.g + cardinal_cost + (n >= 4) * cost_diff  # optimize for 1000x1000 xD
            # g = parent.g
            # if n < 4:
            #     g += cardinal_cost
            # else:
            #     g += diagonal_cost
            h = self.heuristic(tx, tz, goal[0], goal[1])
            children.append(self.PathNode(
                self.state, (tx, tz), g, h, parent,
                action_to_here=(-dx, -dz), action_cost=action_cost, legal_actions=all_legal_actions[tx][tz]
            ))
        return children


    def get_path(self, start, end : list, max_x, max_z, legal_actions):
        first = self.PathNode(self.state, start, g=0, h=self.heuristic(*start, *end), parent=None, action_to_here=None, action_cost=0, legal_actions=legal_actions)
        open = [first]  # heap
        closed = set() # change to a dict with coord-node
        g_lookup = {}
        while len(open) > 0:
            node = heappop(open)
            if node.pos[0] == end[0] and node.pos[1] == end[1]:  # to account for both tuples and lists
                return self.backwards_traverse(node, start)
            closed.add(node.pos)
            for child in self.expand(node, node.g, end, max_x, max_z, legal_actions, g_lookup):
                # p_to_c_cost = child.action_cost
                if child.pos in closed: continue
                # TODO fix the below to be "if child.pos in open" and the last if.
                # if child.pos in g_lookup.keys() and g_lookup[child.pos] <= child.g: continue
                if child.pos in g_lookup and g_lookup[child.pos] <= child.g: continue
                g_lookup[child.pos] = child.g
                heappush(open, child)
        return []


    def backwards_traverse(self, node, end):
        curr = node
        path = []
        while curr.pos != end:
            path.append(curr.pos)
            curr = curr.parent
        # path.append(curr.pos)
        return path


    def heuristic(self, x1, z1, x2, z2):
        # return round(sqrt((x1 - x2) ** 2 + (z1 - z2) ** 2) * cardinal_cost)
        return round(sqrt((x1 - x2) ** 2 + (z1 - z2) ** 2))# * cardinal_cost)


    # a bottleneck
    def merge_sectors(self, state, sectors, to_remove, new):
        for pos in self.sectors_nodes[to_remove]:
            sectors[pos[0]][pos[1]] = new
        self.sectors_nodes[new].update(self.sectors_nodes[to_remove])
        self.sectors_nodes.pop(to_remove)
        self.sector_sizes[new] += self.sector_sizes[to_remove]
        self.sector_sizes[to_remove] = 0


    def create_sectors(self, heightmap, legal_actions):
        self.sectors = full_like(heightmap, -1, int)
        self.n_sectors = 0
        self.sector_sizes = {}
        for x in range(len(legal_actions)):
            for z in range(len(legal_actions[0])):
                if self.sectors[x][z] == -1:
                    self.n_sectors +=1
                    self.sector_sizes[self.n_sectors] = 0
                    self.sectors_nodes[self.n_sectors] = set()
                    self.init_propagate_sector(x, z, self.n_sectors, self.sectors, self.sector_sizes, legal_actions)
                z += 1
            x += 1
        return self.sectors

    # def propagate_sector1(self, x, z, sector, sectors, sector_sizes, legal_actions, is_redoing=False):
    #     open = [(x, z)]
    #     closed = set()
    #     while len(open) > 0:  # search all adjacent until you cant go anymore
    #         pos = open.pop(0)
    #         nx, nz = pos
    #         if not is_redoing and sectors[nx][nz] != -1:
    #             continue
    #         sectors[nx][nz] = sector
    #         sector_sizes[sector] += 1
    #         for n in range(len(legal_actions[nx][nz])):  # check tiles reachable from here
    #             if legal_actions[nx][nz][n] == True:
    #                 dir = src.movement.directions[n]
    #                 cx = nx + dir[0]
    #                 cz = nz + dir[1]
    #                 if cx < 0 or cx >= len(legal_actions) or cz < 0 or cz >= len(legal_actions[0]):
    #                     continue
    #                 childs_sector = sectors[cx][cz]
    #                 if childs_sector != sector or childs_sector == -1:  # if the tile doesn't have a sector, add to list to expand
    #                     child_pos = (cx, cz)
    #                     if not child_pos in closed:
    #                         open.append(child_pos)
    #                     closed.add(child_pos)
    #                 elif childs_sector != sector:
    #                     sector_sizes[childs_sector] -= 1
    #                     child_pos = (cx, cz)
    #                     if not child_pos in closed:
    #                         open.append(child_pos)  # the or allows re-sectoring
    #                     closed.add(child_pos)

    def propagate_sector_depth_limited(self, x, z, sector, sectors, sector_sizes, legal_actions, is_redoing=False):
        open = [(x, z)]
        closed = set()
        if sector not in self.sectors_nodes.keys():
            self.sectors_nodes[sector] = set()
        i = 0
        while len(open) > 0 and i < MAX_SECTOR_PROPAGATION_DEPTH:  # search all adjacent until you cant go anymore
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
                depth = 0
                depth_max = 50
                if legal_actions[nx][nz][n] == True:
                    dir = src.movement.directions[n]
                    cx = nx + dir[0]
                    cz = nz + dir[1]
                    if cx < 0 or cx >= len(legal_actions) or cz < 0 or cz >= len(legal_actions[0]):
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
            i+=1

    def add_to_sector(self, x, z, sector):
        self.sectors_nodes[sector].add((x,z))
        self.sector_sizes[sector] += 1
        self.sectors[x][z] = sector

    def init_propagate_sector(self, x, z, sector, sectors, sector_sizes, legal_actions, is_redoing=False):
        open = [(x, z)]
        closed = set()
        while len(open) > 0:  # search all adjacent until you cant go anymore
            pos = open.pop(0)
            nx, nz = pos
            # if not is_redoing and sectors[nx][nz] != -1:
            #     continue
            self.add_to_sector(pos[0], pos[1], sector)
            for n in range(len(legal_actions[nx][nz])):  # check tiles reachable from here
                if legal_actions[nx][nz][n]:
                    dir = src.movement.directions[n]
                    cx = nx + dir[0]
                    cz = nz + dir[1]
                    if self.state.out_of_bounds_2D(cx, cz): continue
                    # if cx < 0 or cx >= len(legal_actions) or cz < 0 or cz >= len(legal_actions[0]):
                    # childs_sector =
                    if sectors[cx][cz] == -1:  # if the tile doesn't have a sector, add to list to expand
                        child_pos = (cx,cz)
                        if not child_pos in closed:
                            open.append(child_pos)
                        closed.add(child_pos)
                    # elif childs_sector != sector:
                    #     sector_sizes[childs_sector] -= 1
                    #     child_pos = (cx,cz)
                    #     self.sectors_nodes[childs_sector].remove(child_pos)
                    #     if not child_pos in closed:
                    #         open.append(child_pos)  # the or allows re-sectoring
                    #     closed.add(child_pos)


    # def update_sector_for_block(self,x,z, sectors, sector_sizes, legal_actions, old_legal_actions):
    #     found_legal_action = False
    #     # i think u should do this only if a change is legal actions was found
    #
    #     if count_xor(legal_actions[x][z], old_legal_actions[x][z]) > 0:
    #         changed = legal_actions[x][z] ^ old_legal_actions[x][z]
    #         rmost = -1
    #         try:
    #             rmost = rindex(legal_actions[x][z], True)
    #         except ValueError:
    #             rmost = -1
    #         # print(str(old_legal_actions[x][z]) +" and "+str(legal_actions[x][z])+" give rise to "+str(changed))
    #         i = 0
    #         new_sector_created = False
    #         for bit in changed:
    #         # check the sectors height in new dir, compare heights
    #         # if can jump between diff in heights, get sector with smaller size. this'll be the sector to propagate from the other
    #             dir = src.movement.Directions[i]
    #             ox = x+dir[0]
    #             oz = x+dir[1]
    #             if self.state.out_of_bounds_2D(ox, oz): continue
    #             if abs(self.state.rel_ground_hm[x][z] - self.state.rel_ground_hm[ox][oz]) <= self.state.agent_jump_ability: # can now go here after not being able to
    #                 # get larger sector
    #                 sector = self.sectors[x][z]
    #                 osector = self.sectors[ox][oz]
    #                 if sector == osector: continue
    #                 coord_to_prop_into = (x,z) # smaller
    #                 sector_to_prop_into = sector
    #                 size = self.sector_sizes[sector]
    #                 osize = self.sector_sizes[osector]
    #                 sector_to_remove = osector
    #                 if osize < size:
    #                     coord_to_prop_into = (ox, oz)
    #                     sector_to_prop_into = osector
    #                     sector_to_remove = sector
    #                 self.merge_sectors(self.state, sectors, sector_to_remove, sector_to_prop_into)
    #                 # self.sector_sizes[sector_to_remove] = 0
    #                 # self.propagate_sector_depth_limited(*coord_to_prop_into, sector=sector_to_prop_into, sectors=sectors,
    #                 #                        sector_sizes=sector_sizes, legal_actions=legal_actions, is_redoing=True)
    #
    #                 # self.sector_sizes[sector_to_remove] = 0
    #                 # TODO one thing we can do here is keep an array of the tiles in each sector, and simply append them toghether when merging, rather than propagaping
    #                 # self.propagate_sector1(*coord_to_prop_into, sector=sector_to_prop_into, sectors=sectors, sector_sizes=sector_sizes, legal_actions=legal_actions, is_redoing=True)
    #             else:  # tiles are no longer connected, propagate into this tile's sector, append new sector
    #                 if not new_sector_created:
    #                     if self.sectors[x][z] != self.sectors[ox][oz]:  # already done
    #                         continue
    #                     # #_if a this tile is now connected to another sector, append to that instead. might break it?
    #                     if rmost != -1:
    #                         dir = src.movement.Directions[rmost]
    #                         nx = x+dir[0]
    #                         nz = z+dir[1]
    #                         old_sector = self.sectors[x][z]
    #                         new_sector = self.sectors[nx][nz]
    #                         self.sectors[x][z] = new_sector
    #                         self.sector_sizes[old_sector] -= 1
    #                         # self.sector_sizes[new_sector] += 1  # TODO figure out where teh entry for sector_sizes isn't being created
    #                     else:
    #                         sector = self.sectors[x][z]
    #                         self.sector_sizes[sector] -= 1
    #                         self.n_sectors += 1
    #                         self.sector_sizes[self.n_sectors] = 1
    #                         self.sectors[x][z] = self.n_sectors
    #                         # if this is ever called, dont call it again
    #                         self.propagate_sector_depth_limited(x, z, sector=self.n_sectors, sectors=sectors, sector_sizes=sector_sizes, legal_actions=legal_actions, is_redoing=True)
    #                     new_sector_created = True
    #                 # src.pathfinding.a+=1
    #                 # print(src.pathfinding.a)
    #         i+=1


    # if legal_actions[x][z] != old_legal_actions[x][z]:
    #     self.n_sectors += 1
    #     self.sector_sizes[self.n_sectors] = 0
    #     found_legal_action = False
    #     for n in range(len(legal_actions[x][z])):
    #         bit = legal_actions[x][z][n]
    #         found_legal_action = bit
    #         if bit is True:
    #             self.propagate_sector(x, z, sector=self.n_sectors, sectors=sectors, sector_sizes=sector_sizes, legal_actions=legal_actions, is_redoing=True)
    #             break
    #     if not found_legal_action:
    #         self.propagate_sector(x, z, self.n_sectors, sectors=sectors, sector_sizes=self.sector_sizes, legal_actions=legal_actions, is_redoing=True)  # might not do the last arg



    # def get_path(self, start, end : list, max_x, max_z, legal_actions):
    #     first = self.PathNode(self.state, start, g=0, h=self.heuristic(*start, *end), parent=None, action_to_here=None, action_cost=0, legal_actions=legal_actions)
    #     open = [first]  # heap
    #     closed = set() # change to a dict with coord-node
    #     g_lookup = {}
    #     while len(open) > 0:
    #         node = heappop(open)
    #         if node.pos[0] == end[0] and node.pos[1] == end[1]:  # to account for both tuples and lists
    #             return self.backwards_traverse(node, start)
    #         closed.add(node.pos)
    #         for child in self.expand(node, node.g, end, max_x, max_z, legal_actions, g_lookup):
    #             # p_to_c_cost = child.action_cost
    #             if child.pos in closed: continue
    #             # TODO fix the below to be "if child.pos in open" and the last if.
    #             if child.pos in g_lookup and g_lookup[child.pos] <= child.g: continue
    #             g_lookup[child.pos] = child.g
    #             heappush(open, child)
    #     return []
    #
    #
    # def backwards_traverse(self, node, end):
    #     curr = node
    #     path = []
    #     while curr.pos != end:
    #         path.append(curr.pos)
    #         curr = curr.parent
    #     # path.append(curr.pos)
    #     return path
    #
    #
    # def heuristic(self, x1, z1, x2, z2):
    #     # return round(sqrt((x1 - x2) ** 2 + (z1 - z2) ** 2) * cardinal_cost)
    #     return round(sqrt((x1 - x2) ** 2 + (z1 - z2) ** 2))# * cardinal_cost)
    #
    #
    # # a bottleneck
    # def merge_sectors(self, state, sectors, to_remove, new):
    #     for pos in self.sectors_nodes[to_remove]:
    #         sectors[pos[0]][pos[1]] = new
    #     self.sectors_nodes[new].update(self.sectors_nodes[to_remove])
    #     self.sectors_nodes.pop(to_remove)
    #     self.sector_sizes[new] += self.sector_sizes[to_remove]
    #     self.sector_sizes.pop(to_remove)


    def create_sectors(self, heightmap, legal_actions):
        self.sectors = full_like(heightmap, -1, int)
        self.n_sectors = 0
        self.sector_sizes = {}
        for x in range(len(legal_actions)):
            for z in range(len(legal_actions[0])):
                if self.sectors[x][z] == -1:
                    self.n_sectors +=1
                    self.sector_sizes[self.n_sectors] = 0
                    self.sectors_nodes[self.n_sectors] = set()
                    self.init_propagate_sector(x, z, self.n_sectors, self.sectors, self.sector_sizes, legal_actions)
                z += 1
            x += 1
        return self.sectors

    # def propagate_sector1(self, x, z, sector, sectors, sector_sizes, legal_actions, is_redoing=False):
    #     open = [(x, z)]
    #     closed = set()
    #     while len(open) > 0:  # search all adjacent until you cant go anymore
    #         pos = open.pop(0)
    #         nx, nz = pos
    #         if not is_redoing and sectors[nx][nz] != -1:
    #             continue
    #         sectors[nx][nz] = sector
    #         sector_sizes[sector] += 1
    #         for n in range(len(legal_actions[nx][nz])):  # check tiles reachable from here
    #             if legal_actions[nx][nz][n] == True:
    #                 dir = src.movement.directions[n]
    #                 cx = nx + dir[0]
    #                 cz = nz + dir[1]
    #                 if cx < 0 or cx >= len(legal_actions) or cz < 0 or cz >= len(legal_actions[0]):
    #                     continue
    #                 childs_sector = sectors[cx][cz]
    #                 if childs_sector != sector or childs_sector == -1:  # if the tile doesn't have a sector, add to list to expand
    #                     child_pos = (cx, cz)
    #                     if not child_pos in closed:
    #                         open.append(child_pos)
    #                     closed.add(child_pos)
    #                 elif childs_sector != sector:
    #                     sector_sizes[childs_sector] -= 1
    #                     child_pos = (cx, cz)
    #                     if not child_pos in closed:
    #                         open.append(child_pos)  # the or allows re-sectoring
    #                     closed.add(child_pos)

    # def propagate_sector_depth_limited(self, x, z, sector, sectors, sector_sizes, legal_actions, is_redoing=False):
    #     open = [(x, z)]
    #     closed = set()
    #     if sector not in self.sectors_nodes.keys():
    #         self.sectors_nodes[sector] = set()
    #     while len(open) > 0:  # search all adjacent until you cant go anymore
    #         pos = open.pop(0)
    #         nx, nz = pos
    #         if not is_redoing and sectors[nx][nz] != -1:
    #             continue
    #         sectors[nx][nz] = sector
    #         self.sectors_nodes[sector].add(pos)
    #         sector_sizes[sector] += 1
    #         # for n in range(len(legal_actions[nx][nz])):  # check tiles reachable from here
    #         for n in range(8):  # check tiles reachable from here
    #             depth = 0
    #             depth_max = 50
    #             if legal_actions[nx][nz][n] == True:
    #                 dir = src.movement.directions[n]
    #                 cx = nx + dir[0]
    #                 cz = nz + dir[1]
    #                 if cx < 0 or cx >= len(legal_actions) or cz < 0 or cz >= len(legal_actions[0]):
    #                     continue
    #                 childs_sector = sectors[cx][cz]
    #                 if childs_sector != sector or childs_sector == -1:  # if the tile doesn't have a sector, add to list to expand
    #                     child_pos = (cx, cz)
    #                     if not child_pos in closed:
    #                         open.append(child_pos)
    #                     closed.add(child_pos)
    #                 elif childs_sector != sector:
    #                     sector_sizes[childs_sector] -= 1
    #                     child_pos = (cx, cz)
    #                     self.sectors_nodes[childs_sector].remove(child_pos)
    #                     if not child_pos in closed:
    #                         open.append(child_pos)  # the or allows re-sectoring
    #                     closed.add(child_pos)


    # def init_propagate_sector(self, x, z, sector, sectors, sector_sizes, legal_actions, is_redoing=False):
    #     open = [(x, z)]
    #     closed = set()
    #     while len(open) > 0:  # search all adjacent until you cant go anymore
    #         pos = open.pop(0)
    #         nx, nz = pos
    #         # if not is_redoing and sectors[nx][nz] != -1:
    #         #     continue
    #         sectors[nx][nz] = sector
    #         self.sectors_nodes[sector].add(pos)
    #         sector_sizes[sector] += 1
    #         for n in range(len(legal_actions[nx][nz])):  # check tiles reachable from here
    #             if legal_actions[nx][nz][n]:
    #                 dir = src.movement.directions[n]
    #                 cx = nx + dir[0]
    #                 cz = nz + dir[1]
    #                 if self.state.out_of_bounds_2D(cx, cz): continue
    #                 # if cx < 0 or cx >= len(legal_actions) or cz < 0 or cz >= len(legal_actions[0]):
    #                 # childs_sector =
    #                 if sectors[cx][cz] == -1:  # if the tile doesn't have a sector, add to list to expand
    #                     child_pos = (cx,cz)
    #                     if not child_pos in closed:
    #                         open.append(child_pos)
    #                     closed.add(child_pos)
    #                 # elif childs_sector != sector:
    #                 #     sector_sizes[childs_sector] -= 1
    #                 #     child_pos = (cx,cz)
    #                 #     self.sectors_nodes[childs_sector].remove(child_pos)
    #                 #     if not child_pos in closed:
    #                 #         open.append(child_pos)  # the or allows re-sectoring
    #                 #     closed.add(child_pos)


    def update_sector_for_block(self,x,z, sectors, sector_sizes, legal_actions, old_legal_actions):
        found_legal_action = False
        # i think u should do this only if a change is legal actions was found

        if count_xor(legal_actions[x][z], old_legal_actions[x][z]) > 0:
            changed = legal_actions[x][z] ^ old_legal_actions[x][z]
            rmost = -1
            try:
                rmost = rindex(legal_actions[x][z], True)
            except ValueError:
                rmost = -1
            # print(str(old_legal_actions[x][z]) +" and "+str(legal_actions[x][z])+" give rise to "+str(changed))
            i = 0
            new_sector_created = False
            did_merge = False
            for bit in changed:
                # check the sectors height in new dir, compare heights
                # if can jump between diff in heights, get sector with smaller size. this'll be the sector to propagate from the other
                if bit == False: continue
                dir = src.movement.Directions[i]
                i += 1
                ox = x+dir[0]
                oz = z+dir[1]
                if self.state.out_of_bounds_2D(ox, oz): continue
                if abs(self.state.rel_ground_hm[x][z] - self.state.rel_ground_hm[ox][oz]) <= self.state.agent_jump_ability: # can now go here after not being able to
                    # get larger sector
                    if not did_merge:
                        sector = self.sectors[x][z]
                        osector = self.sectors[ox][oz]
                        if sector == osector: continue
                        coord_to_prop_into = (x,z) # smaller
                        sector_to_prop_into = sector
                        size = self.sector_sizes[sector]
                        osize = self.sector_sizes[osector]
                        sector_to_remove = osector
                        # if osize < size:
                        #     coord_to_prop_into = (ox, oz)
                        #     sector_to_prop_into = osector
                        #     sector_to_remove = sector
                        sector_to_prop_into = sector
                        sector_to_remove = osector
                        self.merge_sectors(self.state, self.sectors, sector_to_remove, sector_to_prop_into)
                        did_merge = True
                    # self.sector_sizes[sector_to_remove] = 0
                    # self.propagate_sector_depth_limited(*coord_to_prop_into, sector=sector_to_prop_into, sectors=sectors,
                    #                        sector_sizes=sector_sizes, legal_actions=legal_actions, is_redoing=True)

                    # self.sector_sizes[sector_to_remove] = 0
                    # TODO one thing we can do here is keep an array of the tiles in each sector, and simply append them toghether when merging, rather than propagaping
                    # self.propagate_sector1(*coord_to_prop_into, sector=sector_to_prop_into, sectors=sectors, sector_sizes=sector_sizes, legal_actions=legal_actions, is_redoing=True)
                else:  # tiles are no longer connected, propagate into this tile's sector, append new sector
                    if not new_sector_created:
                        if self.sectors[x][z] != self.sectors[ox][oz]:  # already done
                            continue
                        # #_if a this tile is now connected to another sector, append to that instead. might break it?
                        # if rmost != -1:  # this doesn't actually make sense since the final changaed bit can be in the first if statement
                        #     dir = src.movement.Directions[rmost]
                        #     nx = x+dir[0]
                        #     nz = z+dir[1]
                        #     old_sector = self.sectors[x][z]
                        #     new_sector = self.sectors[nx][nz]
                        #     self.sectors[x][z] = new_sector
                        #     self.sector_sizes[old_sector] -= 1
                        #     self.sector_sizes[new_sector] += 1
                        # else:
                        # if this is ever called, dont call it again
                        new_sector_created = True
            if new_sector_created:
                sector = self.sectors[x][z]
                self.sector_sizes[sector] -= 1
                self.sectors_nodes[sector].remove((x, z))
                self.n_sectors += 1
                self.sector_sizes[self.n_sectors] = 1
                self.sectors_nodes[self.n_sectors] = {(x, z)}
                self.sectors[x][z] = self.n_sectors
                self.propagate_sector_depth_limited(x, z, sector=self.n_sectors, sectors=self.sectors, sector_sizes=sector_sizes, legal_actions=legal_actions, is_redoing=True)

                # src.pathfinding.a+=1
                # print(src.pathfinding.a)


    # if legal_actions[x][z] != old_legal_actions[x][z]:
    #     self.n_sectors += 1
    #     self.sector_sizes[self.n_sectors] = 0
    #     found_legal_action = False
    #     for n in range(len(legal_actions[x][z])):
    #         bit = legal_actions[x][z][n]
    #         found_legal_action = bit
    #         if bit is True:
    #             self.propagate_sector(x, z, sector=self.n_sectors, sectors=sectors, sector_sizes=sector_sizes, legal_actions=legal_actions, is_redoing=True)
    #             break
    #     if not found_legal_action:
    #         self.propagate_sector(x, z, self.n_sectors, sectors=sectors, sector_sizes=self.sector_sizes, legal_actions=legal_actions, is_redoing=True)  # might not do the last arg

