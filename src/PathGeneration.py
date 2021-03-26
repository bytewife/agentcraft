from math import sqrt
import numpy as np
from random import randint
from my_utils import Type_Tiles, Type
from states import *

class LegalPrecomp:
    def __init__(self, level:State, heightmap, path_width, restrictions, length_x, length_y, length_z, world_x, world_y, world_z, clearpoints=None):
        self.width = length_x
        self.height = length_y
        self.depth = length_z
        self.minx = world_x
        self.miny = world_y
        self.minz = world_z
        self.maxx = self.minx + self.width
        self.maxy = self.miny + self.height
        self.maxz = self.minz + self.depth
        self.level = level
        self.hmap = heightmap
        self.path_width = path_width
        self.restrictions = np.array(restrictions)  # this is occupation and hazards. It's a list with lists of
        if clearpoints is not None:
            for point in clearpoints:
                x_span = range(point[0] - path_width, point[0] + path_width + 1)
                z_span = range(point[-1] - path_width, point[-1] + path_width + 1)
                for xi in x_span:
                    for zi in z_span:
                        self.restrictions[xi][zi] = 0
        self.lateral_actions = [[1, 0], [-1, 0], [0, 1], [0, -1]]
        self.diagonal_actions = [[1, 1], [1, -1], [-1, 1], [-1, -1]]
        self.actions = self.lateral_actions + self.diagonal_actions
        self.legal_actions = [[[] for z in range(self.depth)] for x in range(self.width)]
        self.sectors = np.full_like(level.abs_ground_hm, -1, int)
        self.sector_sizes = {}
        self.precomputeActions()
        self.precomputeSectors()
        self.max_sector = 0
        # max_count = self.sector_sizes.get(0)
        max_count = self.sector_sizes.get(1)
        for sector in self.sector_sizes:
            count = self.sector_sizes[sector]
            if count > max_count:
                max_count = count
                self.max_sector = sector


    def isLegalAction(self, x, z, action, relative_to_grid=True):
        diagonal = action[0] and action[1]

        x1, z1 = x, z
        x2, z2 = x + action[0], z + action[1]

        # don't move out of bounds
        if relative_to_grid:
            if x1 < 0 or x1 >= (self.width) \
                    or z1 < 0 or z1 >= (self.depth) \
                    or x2 < 0 or x2 >= (self.width) \
                    or z2 < 0 or z2 >= (self.depth):
                return False
        else:
            if x1  < self.minx or x1  >= self.maxx \
                    or z1 < self.minz or z1 >= self.maxz \
                    or x2 < self.minx or x2 >= self.maxx \
                    or z2 < self.minz or z2 >= self.maxz:
                return False

        midh = self.hmap[x2][z2]
        for xi in range(max(x2 - self.path_width, 0),
                         min(x2 + self.path_width + 1, len(self.restrictions))):
            for zi in range(max(z2 - self.path_width, 0), # start
                             min(z2 + self.path_width + 1, len(self.restrictions[xi]))): #_end
                if bool(self.restrictions[xi][zi]):
                    return False
                h = self.hmap[x2][z2]
                if not midh-1 <= h <= midh+1:
                    return False
        return True

    def precomputeActions(self):
        for xi in range(0, len(self.restrictions)):
            for zi in range(0, len(self.restrictions[xi])):
                for action in self.actions:
                    if self.isLegalAction(xi, zi, action):
                        self.legal_actions[xi][zi].append(action)

    def precomputeSectors(self):
        x = 0
        sector = 0
        while x < len(self.legal_actions):
            z = 0
            while z < len(self.legal_actions[0]):
                if self.sectors[x][z] == -1:
                    sector += 1
                    self.sector_sizes[sector] = 0
                    open = [Node(x, z)]
                    while len(open) > 0:
                        node = open.pop(0)
                        if self.sectors[node.x, node.z] != -1:
                            continue
                        self.sectors[node.x, node.z] = sector
                        self.sector_sizes[sector] += 1
                        for a in self.legal_actions[node.x][node.z]:
                            x1 = node.x + a[0]
                            z1 = node.z + a[1]
                            if x1 < 0 or x1 >= len(self.legal_actions) or z1 < 0 or z1 >= len(self.legal_actions[0]):
                                continue
                            if self.sectors[x1, z1] == -1:
                                open.append(Node(x1, z1))
                z += 1
            x += 1


class PathGenerator:

    GROUND_BLOCKS = [ 1,         2,   3,       12,    24,  80,  110, 121, 179, 208 ]
    GROUND_DATA =   [ [0,1,3,5], [0], [0,1,2], [0,1], [0], [0], [0], [0], [0], [0] ]
    PATH_MARKER = 204

    def __init__(self, x1, z1, x2, z2, level, heightmap, path_width, block_list, data_list,
                 legal, length_x, length_y, length_z, world_x, world_y, world_z, ground=None, relative_to_grid=False, old_path=None, verbose=False):

        self.width = length_x
        self.height = length_y
        self.depth = length_z
        self.minx = world_x
        self.miny = world_y
        self.minz = world_z
        self.maxx = self.minx + self.width
        self.maxy = self.miny + self.height
        self.maxz = self.minz + self.depth
        self.grid = level.abs_ground_hm


        self.level = level
        self.hmap = heightmap
        self.path_width = path_width
        self.block_list = block_list
        self.data_list = data_list
        self.v = verbose
        self.relative_to_grid = relative_to_grid
        xoffset = 0 if relative_to_grid else self.minx
        zoffset = 0 if relative_to_grid else self.minz
        self.startx = int(x1 - xoffset)
        self.startz = int(z1 - zoffset)
        self.endx = int(x2 - xoffset)
        self.endz = int(z2 - zoffset)
        self.basecost = 100
        self.open = [Node(self.startx,
                          self.startz,
                          None,
                          None,
                          0,
                          self.heuristic(self.startx, self.startz, self.endx, self.endz))]
        self.path = np.full((self.maxx - self.minx, self.maxz - self.minz), 0)
        self.lat_cost = self.basecost # cost for a lateral move
        self.diag_cost = round(sqrt(self.basecost**2 * 2)) # cost for a diagonal move
        self.legal = legal
        self.sectors = legal.sectors
        self.legal_actions = legal.legal_actions
        self.closed = np.full_like(self.grid, 0)  #_MAYBE_TODO
        # ensure start and goal are not closed
        if ground is None:
            self.ground = self.mapGround()
        else:
            self.ground = ground
        self.old_path = old_path

    def heuristic(self, x1, z1, x2, z2):
        return round(sqrt((x1-x2)**2 + (z1-z2)**2) * self.basecost)


    def mapGround(self):
        print("Mapping ground blocks")
        ground_map = np.full_like(self.grid, 0)
        for xi in range(self.width):
            for zi in range(self.depth):
                x = int(xi + self.minx)
                z = int(zi + self.minz)
                y = int(self.grid[xi][zi]) - self.level.world_y  # TODO change this to be cleaner
                currentBlock = self.level.blocks[x][y][z]
                ground_map[xi][zi] = 1  #mine

                # if currentBlock in PathGenerator.GROUND_BLOCKS:
                    # blockData = self.level.blockDataAt(x, y, z)
                    # i = PathGenerator.GROUND_BLOCKS.index(currentBlock)
                    # if blockData in PathGenerator.GROUND_DATA[i]:
                    #     ground_map[xi][zi] = 1
        return ground_map


    def makePath(self, safe=False):
        if safe:
            try:
                return self.makePath()
            except Exception:
                print ("Path fail")
                return False
        else:
            if self.v:
                print ("Calculating...")
            calc = self.calculatePath()
            if calc:
                if self.v: print("Generating...")
                self.generatePath()
            return calc

    # Set ground blocks on path to path blocks
    def generatePath(self):
        paved = np.full_like(self.ground, False)
        for xi in range(len(self.path)):
            for zi in range(len(self.path[xi])):
                if self.path[xi, zi]:
                    if self.ground[xi, zi] and not paved[xi, zi]:
                        x = int(xi + self.hmap.minx)
                        y = int(self.hmap[xi][zi])
                        z = int(zi + self.minz)
                        i = randint(0, len(self.data_list) - 1)
                        self.level.blocks[x][y][z] = self.block_list[i]
                        # self.level.setBlockDataAt(x, y, z, self.data_list[i])
                        y2 = y + 1
                        while self.level.blocks[x][y2][z] in Type_Tiles.tile_sets[Type.CITY_GARDEN]:
                            if y2 - y > 2:
                                break
                            self.level.blocks[x][y2][z] = 'minecraft:gold_block'
                            # self.level.setBlockDataAt(x, y2, z, 0)
                            y2 += 1
                        paved[xi][zi] = True

    def setPath(self, node):
        while node is not None:
            for xi in range(max(node.x - self.path_width, 0),
                             min(node.x + self.path_width + 1, len(self.path))):
                for zi in range(max(node.z - self.path_width, 0),
                                 min(node.z + self.path_width + 1, len(self.path[xi]))):
                    self.path[xi, zi] = 1
            node = node.parent
        if self.v:
            print(self.path)

    def goalCheck(self, node):
        x = node.x
        z = node.z

        # If node is goal:
        if self.endx == x and self.endz == z:
            self.setPath(node)
            return True
        return False

    # A*
    def calculatePath(self):

        if self.sectors[self.startx, self.startz] != self.sectors[self.endx-1, self.endz-1]:  #mine
            return False

        while True:

            # If open is empty, search failed
            if len(self.open) == 0:
                if self.v:
                    xoffset = self.hmap.minx if self.relative_to_grid else 0
                    zoffset = self.hmap.minz if self.relative_to_grid else 0
                    startstr = "(" + str(self.startx + xoffset) + ", " + str(self.startz + zoffset) + ")"
                    endstr = "(" + str(self.endx + xoffset) + ", " + str(self.endz + zoffset) + ")"
                    print("No path found from " + startstr + " to " + endstr)
                return False

            node = self.pop_min_f()
            x = node.x
            z = node.z

            if self.goalCheck(node):
                return True
            if self.closed[x][z]:
                continue
            self.closed[x][z] = True
            for action in self.legal_actions[x][z]:
                new_x = x + action[0]
                new_z = z + action[1]
                if self.closed[new_x][new_z]:
                    continue
                new_g = node.g + (self.diag_cost if bool(action[0]) and bool(action[-1]) else self.lat_cost)
                new_h = self.heuristic(x, z, self.endx, self.endz)
                child = Node(new_x, new_z, node, action, new_g, new_h)
                self.open.append(child)

    def pop_min_f(self):
        min_node = self.open[0]
        index = 0
        for i in range(1, len(self.open)):
            min_f = min_node.g + min_node.h
            f = self.open[i].g + self.open[i].h
            if f < min_f:
                min_node = self.open[i]
                index = i
            elif f == min_f:
                if self.open[i].h < min_node.h:
                    min_node = self.open[i]
                    index = i
        return self.open.pop(index)


class Node:
    def __init__(self, x, z, parent=None, action=None, g=None, h=None):
        self.x = x
        self.z = z
        self.action = action
        self.parent = parent
        self.g = g
        self.h = h

