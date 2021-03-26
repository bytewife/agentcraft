from heapq import heappop, heappush, heappushpop
from math import sqrt
from numpy import full_like
import src.movement

cardinal_cost = 100
diagonal_cost = 141

class Pathfinding:

    def __init__(self):
        pass

    sectors = []
    sector_sizes = {}

    class Node:
        def __init__(self, pos, g=0, h=0, parent=None, action_to_here=0, action_cost=0, legal_actions=0):
            self.pos = pos
            self.g = g
            self.parent = parent
            self.h = h
            self.f = g + h
            self.parent = parent
            self.action_to_here = action_to_here
            self.action_cost = action_cost
            self.legal_actions = legal_actions

        def __lt__(self, other):  # required for heapq sort
            return self.f < other.f


    def calc_g(self, parent, g_lookup, p_to_c_cost):
        return g_lookup[parent] + p_to_c_cost


    def expand(self, parent : Node, goal, max_x, max_z, all_legal_actions):  # TODO integtrate legal actions here
        children = []
        x, z = parent.pos
        curr_legal_actions = all_legal_actions[x][z]
        for n in range(len(curr_legal_actions)):
            if curr_legal_actions[n] == False: continue
            dx = movement.directions[n][0]
            dz = movement.directions[n][1]
            tx = parent.pos[0] + dx
            tz = parent.pos[1] + dz
            if (tx < 0 or tz < 0 or tx > max_x or tz > max_z):
                continue
            pos = (tx, tz)
            g = parent.g
            if n < 4:
                g += cardinal_cost
            else:
                g += diagonal_cost
            child = self.Node(
                pos, g, self.heuristic(*pos, *goal), parent,
                action_to_here=(-dx, -dz), action_cost=cardinal_cost, legal_actions=all_legal_actions[tx][tz]
            )
            children.append(child)
        return children


    def get_path(self, start, end, max_x, max_z, legal_actions):
        first = self.Node(start, g=0, h=self.heuristic(*start, *end), parent=None, action_to_here=None, action_cost=0, legal_actions=legal_actions)
        open = [first]  # heap
        closed = set()
        path = []
        g_lookup = {}
        while len(open) > 0:
            node = heappop(open)
            if node.pos == end:
                return self.backwards_traverse(node, start)
            closed.add(node.pos)
            for child in self.expand(node, end, max_x, max_z, legal_actions):
                p_to_c_cost = child.action_cost
                if child.pos in closed: continue
                if child.pos in open and g_lookup[child] < self.calc_g(node, g_lookup, p_to_c_cost): continue # g is the action cost to get here, parent's g + parent to child g
                g_lookup[child.pos] = child.g
                heappush(open, child)
        return path


    def backwards_traverse(self, node, end):
        curr = node
        path = []
        while curr.pos != end:
            path.append(curr.pos)
            curr = curr.parent
        # path.append(curr.pos)
        return path


    def heuristic(self, x1, z1, x2, z2):
        return round(sqrt((x1 - x2) ** 2 + (z1 - z2) ** 2) * cardinal_cost)


    def create_sectors(self, heightmap, legal_actions):
        self.sectors = full_like(heightmap, -1, int)
        # self.sector_sizes = {}
        sector = 0
        for x in range(len(legal_actions)):
            for z in range(len(legal_actions[0])):
                if self.sectors[x][z] == -1:
                    sector += 1
                    self.sector_sizes[sector] = 0
                    self.propagate_sector(x, z, sector, self.sectors, self.sector_sizes, legal_actions)
                z += 1
            x += 1
        return self.sectors


    def propagate_sector(self, x, z, sector, sectors, sector_sizes, legal_actions, is_redoing=False):
        open = [(x, z)]
        closed = set()
        while len(open) > 0:  # search all adjacent until you cant go anymore
            pos = open.pop(0)
            nx, nz = pos
            if not is_redoing and sectors[nx][nz] != -1:
                continue
            sectors[nx][nz] = sector
            sector_sizes[sector] += 1
            legals = legal_actions[nx][nz]
            for n in range(len(legal_actions[nx][nz])):  # check tiles reachable from here
                a = legal_actions[nx][nz][n]
                if legal_actions[nx][nz][n] == True:
                    dir = src.movement.directions[n]
                    cx = nx + dir[0]
                    cz = nz + dir[1]
                    if cx < 0 or cx >= len(legal_actions) or cz < 0 or cz >= len(legal_actions[0]):
                        continue
                    childs_sector = sectors[cx][cz]
                    if childs_sector == -1 or childs_sector != sector:  # if the tile doesn't have a sector, add to list to expand
                        child_pos = (cx,cz)
                        if not child_pos in closed:
                            open.append(child_pos)
                        closed.add(child_pos)
                    elif childs_sector != sector:
                        sector_sizes[childs_sector] -= 1
                        child_pos = (cx,cz)
                        if not child_pos in closed:
                            open.append(child_pos)  # the or allows re-sectoring
                        closed.add(child_pos)


    def update_sector_for_block(self,x,z, sectors, sector_sizes, legal_actions):
        found_legal_action = False
        for n in range(len(legal_actions[x][z])):
            bit = legal_actions[x][z][n]
            found_legal_action = True
            if bit is True:
                dir = src.movement.directions[n]
                reachable_block = (x+dir[0], z+dir[1])
                reachable_sector = sectors[reachable_block[0], reachable_block[1]]
                if sectors[x][z] != reachable_sector:
                    sector_sizes[sectors[x][z]] -= 1
                    new_sector = reachable_sector
                    sectors[x][z] = new_sector
                    self.propagate_sector(0, 5, sector=new_sector, sectors=sectors, sector_sizes=sector_sizes, legal_actions=legal_actions, is_redoing=True)
        if not found_legal_action:
            sector = len(sector_sizes)
            self.sector_sizes[sector] = 0
            self.propagate_sector(x, z, sector, self.sectors, self.sector_sizes, legal_actions)

