"""
###Node Class
3x3 areas of blocks that the settlement is built upon
"""
import src.pathfinding
import src.utils
import math

class Node:
    """
    A 3x3 group of blocks holding holistic information
    """
    LOCAL_RADIUS = 3
    RANGE_RADIUS = 4
    NEIGHBOR_RADIUS = 1
    ADJACENT_RADIUS = 1

    def __init__(self, state, center, types, size=3):
        self.center = center
        self.size = size
        self.mask_type = set()  # Type given to Node but not Blocks
        self.mask_type.update(types)
        self.lot = None
        self.state = state
        self.tiles = self.gen_tiles()
        self.type = None
        self.adjacent_centers = None
        self.adjacent_cached = set()
        self.gend_adjacent = False
        self.range_centers = None
        self.range_cached = set()
        self.gend_range = False
        self.neighbors_centers = None
        self.neighbors_cached = set()
        self.gend_neighbors = False
        self.local_centers = None
        self.local_cached = set()
        self.gend_local = False


    def adjacent(self):
        if self.gend_adjacent:  # placed first for efficiency
            return self.adjacent_cached
        else:
            for pos in self.adjacent_centers:
                self.adjacent_cached.add(self.state.nodes(*pos))
            self.gend_adjacent = True
            return self.adjacent_cached


    def range(self):
        if not self.gend_range:
            for pos in self.range_centers:
                node = self.state.nodes(*pos)
                if node.type == None:
                    node.get_type()
                if src.utils.TYPE.WATER.name in node.type:
                    continue
                self.range_cached.add(node)
            self.gend_range = True
        return self.range_cached


    def neighbors(self):
        if not self.gend_neighbors:
            for pos in self.neighbors_centers:
                self.neighbors_cached.add(self.state.nodes(*pos))
            self.gend_neighbors = True
        return self.neighbors_cached


    def local(self):
        if not self.gend_local:
            for pos in self.local_centers:
                node = self.state.nodes(*pos)
                if src.utils.TYPE.WATER.name in node.get_type():
                    continue
                self.local_cached.add(node)
            self.gend_local = True
        return self.local_cached


    def gen_tiles(self):
        tiles = []
        radius = math.floor(self.size / 2)
        for x in range(-radius, radius + 1):
            for z in range(-radius, radius + 1):
                nx = max(min(self.center[0] + x, self.state.last_node_pointer_x), 0)
                nz = max(min(self.center[1] + z, self.state.last_node_pointer_z), 0)
                tiles.append((nx, nz))
        return tiles


    def get_tiles(self):
        return self.tiles


    def get_type(self):
        if self in self.state.built:
            self.add_mask_type(src.utils.TYPE.BUILT.name)
        self.type = set()
        for tile_pos in self.get_tiles():
            self.type.add(self.state.types[tile_pos[0]][tile_pos[1]])  # each block has a single type
        self.type.update(self.mask_type)
        return self.type


    def add_prosperity(self, amt):
        self.state.prosperities[self.center[0]][self.center[1]] += amt
        self.state.update_flags[self.center[0]][self.center[1]] = 1


    def get_prosperity(self):
        return self.state.prosperities[self.center[0]][self.center[1]]

    def add_mask_type(self, type):
        self.mask_type.add(type)


    def clear_type(self, state):
        if self in state.construction:
            state.construction.discard(self)
        self.mask_type.clear()


    def gen_adjacent_centers(self, state):
        adj = set()
        for dir in src.pathfinding.ALL_DIRS:
            pos = (self.center[0] + dir[0] * self.size, self.center[1] + dir[1] * self.size)
            if state.out_of_bounds_Node(*pos): continue
            adj.add(pos)
        return adj


    def add_neighbor(self, node):
        self.neighbors_cached.add(node)
        self.neighbors_centers.add(node.center)


    def gen_neighbors_centers(self, state):
        neighbors = self.adjacent_centers.copy()
        i = 0
        for r in range(2, Node.NEIGHBOR_RADIUS + 1):
            for ox in range(-r, r + 1, 2 * r):  # rings only
                for oz in range(-r, r + 1):
                    if ox == 0 and oz == 0: continue
                    x = (self.center[0]) + ox * self.size
                    z = (self.center[1]) + oz * self.size
                    if state.out_of_bounds_Node(x, z):
                        continue
                    neighbors.add((x, z))
            for ox in range(-r + 1, r):
                for oz in range(-r, r + 1, 2 * r):
                    if ox == 0 and oz == 0: continue
                    x = (self.center[0]) + ox * self.size
                    z = (self.center[1]) + oz * self.size
                    if state.out_of_bounds_Node(x, z):
                        continue
                    neighbors.add((x, z))
        return neighbors


    def gen_local_centers(self, state):
        local = self.neighbors_centers.copy()
        for r in range( Node.NEIGHBOR_RADIUS + 1, Node.LOCAL_RADIUS + 1):
            for ox in range(-r, r + 1, 2 * r):
                for oz in range(-r, r + 1):
                    x = (self.center[0]) + ox * self.size
                    z = (self.center[1]) + oz * self.size
                    local.add(
                        (min(max(1, x), state.last_node_pointer_x), min(max(1, z), state.last_node_pointer_z)))
            for ox in range(-r + 1, r):
                for oz in range(-r, r + 1, 2 * r):
                    x = (self.center[0]) + ox * self.size
                    z = (self.center[1]) + oz * self.size
                    local.add(
                        (min(max(1, x), state.last_node_pointer_x), min(max(1, z), state.last_node_pointer_z)))
        return local


    def gen_range_centers(self, state):
        local = self.local_centers.copy()
        local.add(self.center)
        for r in range( Node.LOCAL_RADIUS + 1, Node.RANGE_RADIUS + 1):
            for ox in range(-r, r + 1, 2 * r):
                for oz in range(-r, r + 1):
                    x = (self.center[0]) + ox * self.size
                    z = (self.center[1]) + oz * self.size
                    local.add(
                        (min(max(1, x), state.last_node_pointer_x), min(max(1, z), state.last_node_pointer_z)))
            for ox in range(-r + 1, r):
                for oz in range(-r, r + 1, 2 * r):
                    x = (self.center[0]) + ox * self.size
                    z = (self.center[1]) + oz * self.size
                    local.add(
                        (min(max(1, x), state.last_node_pointer_x), min(max(1, z), state.last_node_pointer_z)))
        return local


    def get_locals_positions(self):
        arr = []
        for node in self.local():
            arr.append(node.center)
        return arr


    def get_neighbors_positions(self):
        return self.neighbors_centers


    def get_ranges_positions(self):
        return self.range_centers


    def get_lot(self):
        lot = set([self])
        new_neighbors = set()
        for i in range(5):
            new_neighbors = set([e for n in lot for e in n.adjacent() if e not in lot and (
                    src.utils.TYPE.GREEN.name in e.mask_type or src.utils.TYPE.TREE.name in e.mask_type or src.utils.TYPE.CONSTRUCTION.name in e.mask_type)])
            accept = set([n for n in new_neighbors if src.utils.TYPE.CONSTRUCTION.name not in n.mask_type])
            if len(new_neighbors) == 0:
                break
            lot.update(accept)
        if len([n for n in new_neighbors if
                src.utils.TYPE.CONSTRUCTION.name not in n.mask_type]) == 0:  # neighbors except self
            return lot
        else:
            return None
