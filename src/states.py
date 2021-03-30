import math
from math import floor

import http_framework.interfaceUtils
import http_framework.worldLoader
import src.my_utils
import src.movement
import src.pathfinding
import src.scheme_utils
import numpy as np
from random import choice
import src.linedrawing

class State:

    tallest_building_height = 30
    changed_blocks = {}
    blocks = []  # 3D Array of all the blocks in the state
    abs_ground_hm = []
    rel_ground_hm = [] # TODO create function for this. Agents will be armor stands, and they can be updated in real time
    trees = []
    water = []
    world_y = 0
    world_x = 0
    world_z = 0
    len_x = 0
    len_y = 0
    len_z = 0
    unwalkable_blocks = []
    agent_height = 2
    agent_jump_ability = 2
    heightmap_offset = -1
    node_size = 3
    road_nodes = {}
    roads = []
    road_segs = set()
    built = set()
    lots = set()

    ## Create surface grid
    def __init__(self, world_slice=None, blocks_file=None, max_y_offset=tallest_building_height):
        if not world_slice is None:
            self.blocks, self.world_y, self.len_y, self.abs_ground_hm = self.gen_blocks_array(world_slice)
            self.rel_ground_hm = self.gen_rel_ground_hm(self.abs_ground_hm)  # a heightmap based on the state's y values. -1
            self.heightmaps = world_slice.heightmaps
            self.types = self.gen_types(self.rel_ground_hm)  # 2D array. Exclude leaves because it would be hard to determine tree positions
            self.world_x = world_slice.rect[0]
            self.world_z = world_slice.rect[1]
            self.len_x = world_slice.rect[2] - world_slice.rect[0]
            self.len_z = world_slice.rect[3] - world_slice.rect[1]
            self.legal_actions = src.movement.gen_all_legal_actions(
                self.blocks, vertical_ability=self.agent_jump_ability, heightmap=self.rel_ground_hm, actor_height=self.agent_height, unwalkable_blocks=[]
            )
            self.pathfinder = src.pathfinding.Pathfinding()
            self.sectors = self.pathfinder.create_sectors(self.heightmaps["MOTION_BLOCKING_NO_LEAVES"],
                                            self.legal_actions)  # add tihs into State
            self.nodes, self.node_pointers = self.gen_nodes(self.len_x, self.len_z, self.node_size)
            # self.prosperities = [[0] * self.len_z] * self.len_x
            self.prosperities = np.zeros((self.len_x,self.len_z))


        else:  # for testing
            print("State instantiated for testing!")
            def parse_blocks_file(file_name):
                size, blocks = src.scheme_utils.get_schematic_parts(file_name)
                dx, dy, dz = size
                blocks3D = [[[0 for z in range(dz)] for y in range(dy)] for x in range(dx)]
                for x in range(dx):
                    for y in range(dy):
                        for z in range(dz):
                            index = y*(dz)*(dx) + z*(dx) + x
                            inv_y = dy - 1 - y
                            blocks3D[x][inv_y][z] = "minecraft:"+blocks[index]
                return dx, dy, dz, blocks3D
            self.len_x, self.len_y, self.len_z, self.blocks = parse_blocks_file(blocks_file)


    # note: not every block has a node. These will point to None
    def gen_nodes(self, len_x, len_z, node_size):
        if len_x < 0 or len_z < 0:
            print("Lengths cannot be <0")
        node_size = 3  # in blocks
        nodes_in_x = int(len_x / node_size)
        nodes_in_z = int(len_z / node_size)
        node_count = nodes_in_x * nodes_in_z
        self.last_node_pointer_x = nodes_in_x * node_size
        self.last_node_pointer_z = nodes_in_z * node_size
        nodes = {}  # contains coord pointing to data struct
        node_pointers = np.full((len_x,len_z), None)
        for x in range(nodes_in_x):
            for z in range(nodes_in_z):
                cx = x*node_size+1
                cz = z*node_size+1
                node = self.Node(center=(cx, cz), types=[src.my_utils.Type.BROWN.name], size=self.node_size)  # TODO change type
                nodes[(cx, cz)] = node
                node_pointers[cx][cz] = (cx, cz)
                for dir in src.movement.directions:
                    nx = cx + dir[0]
                    nz = cz + dir[1]
                    node_pointers[nx][nz] = (cx, cz)
        for node in nodes.values():
            node.neighbors = node.gen_neighbors(nodes, node_pointers, self)
            node.local = node.gen_local(nodes, node_pointers, self)
            node.range = node.gen_range()
            node.adjacent = node.gen_adjacent(nodes, node_pointers)
            # print("ranges for " + str(node.center))
            # print(node.get_ranges_positions())
        return nodes, node_pointers


    class Node:

        local = set()
        def __init__(self, center, types, size):
            self.center = center
            self.size = size
            self.local_prosperity = 0  # sum of all of its blocks
            self.prosperity = 0
            self.type = set()
            self.type.update(types)
            self.neighbors = set()
            self.lot = None
            self.range = set()
            self.adjacent = set()
            self.locality_radius = 2
            self.range_radius = 3
            self.neighborhood_radius = 4
            self.adjacent_radius = 1


        def add_type(self, type):
            self.type.add(type)


        def clear_type(self, built_arr):
            if self in built_arr:
                built_arr.discard(self)
            # if src.my_utils.BUILDING.name
            self.type.clear()


        def gen_adjacent(self, nodes, node_pointers):
            adj = set()
            for dir in src.movement.directions:
                pos = (self.center[0] + dir[0], self.center[1] + dir[1])
                node = nodes[node_pointers[pos]]
                adj.add(node)
            return adj


        def add_neighbor(self, node):
            self.neighbors.add(node)


        def gen_neighbors(self, nodes, node_pointers, state):
            neighbors = set()
            i = 0
            for r in range(1, self.neighborhood_radius+1):
                for ox in range(-r, r+1):
                    for oz in range(-r, r+1):
                        x = (self.center[0])+ox*self.size
                        z = (self.center[1])+oz*self.size
                        if state.out_of_bounds_Node(x, z):
                            continue
                        node = nodes[node_pointers[(x, z)]]
                        neighbors.add(node)
            return neighbors


        # get local nodes
        def gen_local(self, nodes, node_pointers, state):
            local = set()
            i = 0
            for r in range(1, self.locality_radius + 1):
                for ox in range(-r, r + 1):
                    for oz in range(-r, r + 1):
                        x = (self.center[0]) + ox * self.size
                        z = (self.center[1]) + oz * self.size
                        if state.out_of_bounds_Node(x, z):
                            continue
                        node = nodes[node_pointers[(x, z)]]
                        local.add(node)
            return local


        def get_locals_positions(self):
            arr = []
            for node in self.local:
                arr.append(node.center)
            return arr


        def get_neighbors_positions(self):
            arr = []
            for node in self.neighbors:
                arr.append(node.center)
            return arr


        def get_ranges_positions(self):
            arr = []
            for node in self.range:
                arr.append(node.center)
            return arr


        def gen_range(self):
            local = {self}
            _range = []
            for i in range(1, self.range_radius+1):
                new_neighbors = set([e for n in local for e in n.neighbors if e not in local])
                if len(new_neighbors) == 0:
                    _range = list(local)
                    self.water_neighbors = [l for l in _range if src.my_utils.Type.WATER.name in l.type]
                    self.resource_neighbors = [l for l in _range if (
                                src.my_utils.Type.BUILDING.name in l.type and l.prosperity > 300) or src.my_utils.Type.TREE.name in l.type or src.my_utils.Type.GREEN.name in l.type]
                    break
                local.update(new_neighbors)

                if i == self.range_radius - 1:
                    _range = list(local)
                    self.water_neighbors = [l for l in _range if src.my_utils.Type.WATER.name in l.type]
                    self.resource_neighbors = [l for l in _range if (
                                src.my_utils.Type.BUILDING.name in l.type and l.prosperity > 300) or src.my_utils.Type.TREE.name in l.type or src.my_utils.Type.GREEN.name in l.type]
            self.built_resources = self.prosperity
            return _range


    def calc_local_prosperity(self, node_center):
        x = node_center[0]
        z = node_center[1]
        local_p = self.prosperities[x][z]
        for dir in src.movement.directions:
            local_p += self.prosperities[x+dir[0]][z+dir[1]]
        return local_p


    def gen_heightmaps(self, world_slice):
        result = {}
        for name, heightmap in world_slice.heightmaps.items():
            result[name] = []
            for x in range(len(heightmap)):
                result[name].append([])
                for z in range(len(heightmap[0])):
                    state_adjusted_y = heightmap[x][z]# + self.heightmap_offset
                    result[name][x].append(state_adjusted_y)
        return result


    def gen_blocks_array(self, world_slice, max_y_offset=tallest_building_height):
        x1, z1, x2, z2 = world_slice.rect
        abs_ground_hm = world_slice.get_heightmap("MOTION_BLOCKING_NO_LEAVES", -1) # inclusive of ground
        def get_y_bounds(_heightmap):  ## Get the y range that we'll save tha state in?
            lowest = _heightmap[0][0]
            highest = _heightmap[0][0]
            for col in _heightmap:
                for block_y in col:
                    if (block_y < lowest):
                        lowest = block_y
                    elif (block_y > highest):
                        highest = block_y
            return lowest, highest
        y1, y2  = get_y_bounds(abs_ground_hm)  # keep range not too large
        y2 += max_y_offset
        if (y2 > 150):
            print("warning: Y bound is really high!")

        len_z = abs(z2 - z1)
        len_y = abs(y2 - y1)
        len_x = abs(x2 - x1)
        blocks = [[[0 for z in range(len_z)] for y in range(len_y)] for x in range(len_x)] # the format of the state isn't the same as the file's.
        xi = 0
        yi = 0
        zi = 0
        for x in range(x1, x2):
            yi = 0
            for y in range(y1, y2):
                zi = 0
                for z in range(z1, z2):
                    block = world_slice.getBlockAt((x, y, z))
                    blocks[xi][yi][zi] = block
                    zi += 1
                yi += 1
            xi += 1
        world_y = y1
        len_y = y2 - y1
        return blocks, world_y, len_y, abs_ground_hm


    def gen_rel_ground_hm(self, abs_ground_hm):
        result = []
        for x in range(len(abs_ground_hm)):
            result.append([])
            for z in range(len(abs_ground_hm[0])):
                state_adjusted_y = int(abs_ground_hm[x][z]) - self.world_y + 1#+ self.heightmap_offset
                result[x].append(state_adjusted_y)
        return result


    def update_node_type(self, x, z):
        prev_type = self.types[x][z]
        new_type = self.determine_type(x, z)
        if prev_type == "TREE":
            if new_type != "TREE":
                self.trees.remove((x, z))
        #     y = self.heightmaps["MOTION_BLOCKING_NO_LEAVES"][x][z]-self.world_y+self.heightmap_offset
        #     if self.is_log(x, y, z):
        #         new_type = "TREE"
        self.types[x][z] = new_type


    ## hope this isn't too expensive. may need to limit area if it is
    # def update_heightmaps(self, x, z):
    #     x_to = x + 1
    #     z_to = z + 1
    #     area = [x + self.world_x, z + self.world_z, x_to + self.world_x, z_to + self.world_z]
    #     area = src.my_utils.correct_area(area)
    #     worldSlice = http_framework.worldLoader.WorldSlice(area, heightmapOnly=True)
    #     hm_type = "MOTION_BLOCKING_NO_LEAVES"  # only update one for performance
    #     for index in range(1,len(worldSlice.heightmaps)+1):
    #         name = src.my_utils.Heightmaps(index).name
    #         new_y = int(worldSlice.heightmaps[name][0][0]) - 1
    #         self.heightmaps[name][x][z] = new_y
    #     hm_base = self.heightmaps[hm_type]
    #     state_adjusted_y = int(hm_base[x][z])
    #     self.abs_ground_hm[x][z] = state_adjusted_y
    #     # self.abs_ground_hm[x][z] = self.heightmaps["MOTION_BLOCKING_NO_LEAVES"][x][z]
    #     self.rel_ground_hm = self.gen_rel_ground_hm(self.abs_ground_hm)

    def update_heightmaps(self):
        area = [self.world_x, self.world_z, self.world_x + self.len_x, self.world_z + self.len_z]
        area = src.my_utils.correct_area(area)
        worldSlice = http_framework.worldLoader.WorldSlice(area, heightmapOnly=True)
        hm_type = "MOTION_BLOCKING_NO_LEAVES"  # only update one for performance
        for index in range(1,len(worldSlice.heightmaps)+1):
            self.heightmaps[hm_type] = worldSlice.heightmaps[src.my_utils.Heightmaps(index).name]
        for x in range(len(self.heightmaps[hm_type])):
            for z in range(len(self.heightmaps[hm_type])):
                self.heightmaps[hm_type][x][z] = worldSlice.heightmaps[hm_type][x][z] - 1
        self.abs_ground_hm = self.heightmaps[hm_type]
        self.rel_ground_hm = self.gen_rel_ground_hm(self.abs_ground_hm)
        return worldSlice


    def gen_types(self, heightmap):
        xlen = len(self.blocks)
        zlen = len(self.blocks[0][0])
        types = [["str" for i in range(zlen)] for j in range(xlen)]
        for x in range(xlen):
            for z in range(zlen):
                type = self.determine_type(x, z, heightmap)
                if type == "TREE":
                    self.trees.append((x, z))
                if type == "WATER":
                    self.water.append((x,z))
                types[x][z] = type
        print("done initializing types")
        return types


    def determine_type(self, x, z, heightmap):
        block_y = int(heightmap[x][z]) - 1
        block = self.blocks[x][block_y][z]
        for i in range(1, len(src.my_utils.Type)+1):
            if block in src.my_utils.Type_Tiles.tile_sets[i]:
                return src.my_utils.Type(i).name
        return src.my_utils.Type.BROWN.name



    def save_state(self, state, file_name):
        f = open(file_name, 'w')
        len_x = len(state.blocks)
        len_y = len(state.blocks[0])
        len_z = len(state.blocks[0][0])
        f.write('{}, {}, {}, {}\n'.format(len_x, state.world_y, len_y, len_z))
        i = 0
        for position,block in self.changed_blocks.items():
            to_write = position+';'+block+"\n"
            f.write(to_write)
            i += 1
        f.close()
        print(str(i)+" blocks saved")


    def load_state(self, save_file):
        f = open(save_file, "r")
        lines = f.readlines()
        size = lines[0]
        blocks = lines[1:]
        n_blocks = len(blocks)
        i = 0
        for line in blocks:
            position_raw, block = line.split(';')
            state_x, state_y, state_z = src.my_utils.convert_key_to_coords(position_raw)
            http_framework.interfaceUtils.placeBlockBatched(
                self.world_x + state_x, self.world_y + state_y, self.world_z + state_z, block, n_blocks
            )
            i += 1
        f.close()
        self.changed_blocks.clear()
        print(str(i)+" blocks loaded")


    # NOTE: you need to get heihtmaps after you place block info. they should be last
    def render(self):
        i = 0
        n_blocks = len(self.changed_blocks)
        for position, block in self.changed_blocks.items():
            state_x, state_y, state_z = src.my_utils.convert_key_to_coords(position)
            http_framework.interfaceUtils.placeBlockBatched(self.world_x + state_x, self.world_y + state_y, self.world_z + state_z, block, n_blocks)
            # http_framework.interfaceUtils.setBlock(self.world_x + state_x, self.world_y + state_y, self.world_z + state_z, block)
            i += 1
        self.update_heightmaps()  # must wait until all blocks are placed
        for position, block in self.changed_blocks.items():
            state_x, state_y, state_z = src.my_utils.convert_key_to_coords(position)
            self.update_block_info(state_x, state_y, state_z)  # Must occur after new blocks have been placed
        self.changed_blocks.clear()
        print(str(i)+" blocks rendered")


    ## do we wanna cache tree locations? I don't want them to cut down buildings lol


    # is this state x
    def update_block_info(self, x, y, z):  # this might be expensive if you use this repeatedly in a group
        # update heightmap was here
        for xo in range(-1, 2):
            for zo in range(-1, 2):
                bx = x + xo
                bz = z + zo
                if self.out_of_bounds_2D(bx, bz):
                    continue
                self.legal_actions[bx][bz] = src.movement.get_legal_actions_from_block(self.blocks, bx, bz, self.agent_jump_ability,
                                                                                   self.rel_ground_hm, self.agent_height,
                                                                                   self.unwalkable_blocks)
        self.pathfinder.update_sector_for_block(x, z, self.sectors,
                                                sector_sizes=self.pathfinder.sector_sizes,
                                                legal_actions=self.legal_actions)


    def get_adjacent_block(self, x_origin, y_origin, z_origin, x_off, y_off, z_off):
        x_target = x_origin + x_off
        y_target = y_origin + y_off
        z_target = z_origin + z_off
        if self.out_of_bounds_3D(x_target, y_target, z_target):
            return None
        return self.blocks[x_target][y_target][z_target]


    def get_all_adjacent_blocks(self, x_origin, y_origin, z_origin):
        adj_blocks = []
        for x_off in range(-1, 2):
            for y_off in range(-1, 2):
                for z_off in range(-1, 2):
                    if x_off == 0 and y_off == 0 and z_off == 0:
                        continue
                    block = self.get_adjacent_block(x_origin, y_origin, z_origin, x_off, y_off, z_off)
                    if block is None:
                        continue
                    adj_blocks.append((block, x_origin+x_off, y_origin+y_off, z_origin+z_off))
        return adj_blocks


    def world_to_state(self,coords):
        x = coords[0] - self.world_x
        z = coords[2] - self.world_z
        y = self.rel_ground_hm[x][z]
        result = (x,y,z)
        return result


    def out_of_bounds_3D(self, x, y, z):
        return True if \
            x >= len(self.blocks) \
            or y >= len(self.blocks[0]) \
            or z >= len(self.blocks[0][0]) \
            or x < 0 \
            or y < 0 \
            or z < 0 \
            else False


    def out_of_bounds_2D(self, x, z):
        return True if x < 0 or z < 0 or x >= len(self.blocks) or z >= len(self.blocks[0][0]) \
            else False

    def out_of_bounds_Node(self, x, z):
        if x < 0 or z < 0 or  x > self.last_node_pointer_x or z > self.last_node_pointer_z: # the problem is that some blocks don't point to a tile.
            return True
        return False


    def set_block(self, x, y, z, block_name):
        self.blocks[x][y][z] = block_name
        key = src.my_utils.convert_coords_to_key(x, y, z)
        self.changed_blocks[key] = block_name


    def set_type_building(self, nodes):
        for node in nodes:
            if src.my_utils.Type.GREEN.name in node.type or \
                    src.my_utils.Type.BROWN.name in node.type or \
                    src.my_utils.Type.TREE.name in node.type:
                node.clear_type()
                node.add_type(src.my_utils.Type.BUILDING.name)
                self.built.add(node)


    def set_type_road(self, node_points, road_type):
        for point in node_points:
            node = self.nodes[self.node_pointers[point]]
            if src.my_utils.Type.WATER.name in node.type:
                node.clear_type()
                node.add_type(src.my_utils.Type.BRIDGE.name)
            else:
                node.clear_type(self.built)
                node.add_type(road_type)
            for road in self.roads:
                node.add_neighbor(road)
                road.add_neighbor(node)
            self.roads.append(node)  # put node in roads array


    def init_main_st(self):
        (x1, y1) = choice(self.water)
        n = self.nodes[self.node_pointers[(x1, y1)]]
        n1_options = list(set(n.range) - set(n.local)) # far away nodes
        # n1_options = list(set(self.nodes[self.node_pointers[(10,10)]])) # far away nodes
        n1 = np.random.choice(n1_options, replace=False)
        print(n1)
        print(n1)
        while src.my_utils.Type.WATER.name in n1.type:  # generate and test until n1 isn't water
            n1 = np.random.choice(n1_options, replace=False)
        n2_options = list(set(n1.range) - set(n1.local))
        n2 = np.random.choice(n2_options, replace=False)
        points = src.linedrawing.get_line((n1.center[0], n1.center[1]), (n2.center[0], n2.center[1]))
        while any(src.my_utils.Type.WATER.name in self.nodes[self.node_pointers[(x, y)]].type for (x, y) in
                  points):  # if any of the points of the potential road are in water, regenerate
            n2 = np.random.choice(n2_options, replace=False)
            points = src.linedrawing.get_line((n1.x, n1.y), (n2.x, n2.y))

        points = self.points_to_nodes(points)
        (x1, y1) = points[0]
        (x2, y2) = points[len(points) - 1]
        self.set_type_road(points, src.my_utils.Type.MAJOR_ROAD.name) # TODO check if the fact that this leads to repeats causes issue
        middle_nodes = []
        if len(points) > 2:
            middle_nodes = points[1:len(points) - 1]
        self.road_segs.add(
            RoadSegment(self.nodes[(x1,y1)], self.nodes[(x2,y2)], middle_nodes, src.my_utils.Type.MAJOR_ROAD.name, self.road_segs))
        for (x, y) in points:
            adjacent = self.nodes[(x,y)].adjacent
            adjacent = [s for n in adjacent for s in n.adjacent]  # every node in the road builds buildings around them
            for pt in adjacent:
                if pt not in points:
                    self.set_type_building([self.nodes[(pt.center[0], pt.center[1])]])
        self.init_lots(x1, y1, x2, y2)  # main street is a lot


    def init_lots(self, x1, y1, x2, y2):
        (mx, my) = (int(x1 + x2) // 2, int(y1 + y2) // 2)  # middle
        self.add_lot([(mx - 25, my - 25), (mx + 25, my + 25)])


    def add_lot(self, points):
        lot = Lot(self, points)
        if lot is not None:
            self.lots.add(lot)
            return True
        return False


    def points_to_nodes(self, points):
        nodes = []
        for point in points:
            node = self.node_pointers[point]  # node coords
            if node not in nodes:
                nodes.append(node)
        return nodes

    # might have to get point2 within the func, rather than pass it in
    def create_road(self, point1, point2, road_type):
        # self.roads.append((point1))
        self.roads.append(self.nodes[self.node_pointers[point1]])
        block_path = src.linedrawing.get_line(point1, point2) # inclusive
        # add road segnmets
        middle_nodes = []
        node_path = []
        if len(block_path) > 0:
            start = self.node_pointers[block_path[0]]
            node_path.append(start) # start
            for n in range(1, len(block_path)-1):
                node = self.node_pointers[block_path[n]]
                if not node in self.road_segs and node != None:
                    middle_nodes.append(node)
                    node_path.append(node)
            a = self.node_pointers
            end = self.node_pointers[block_path[len(block_path)-1]]
            node_path.append(self.node_pointers[block_path[len(block_path)-1]])  # end

        # draw two more lines
        for card in src.movement.cardinals:
            # offset1 = choice(src.movement.cardinals)
            aux1 = src.linedrawing.get_line(
                (point1[0]+ card[0], point1[1] +card[1]),
                (point2[0]+ card[0], point2[1] + card[1]),
            )
            block_path.extend(aux1)
        # render
        road_segment = RoadSegment(point1, point2, middle_nodes, road_type, self.road_segs)
        for block in block_path:
            x = block[0]
            z = block[1]
            y = int(self.rel_ground_hm[x][z]) - 1
            set_state_block(self, x, y, z, "minecraft:blue_concrete")
        self.set_type_road(node_path, src.my_utils.Type.MAJOR_ROAD.name)

        def create_road(self, point1, point2, road_type):
            # self.roads.append((point1))
            self.roads.append(self.nodes[self.node_pointers[point1]])
            block_path = src.linedrawing.get_line(point1, point2)  # inclusive
            # add road segnmets
            middle_nodes = []
            node_path = []
            if len(block_path) > 0:
                start = self.node_pointers[block_path[0]]
                node_path.append(start)  # start
                for n in range(1, len(block_path) - 1):
                    node = self.node_pointers[block_path[n]]
                    if not node in self.road_segs and node != None:
                        middle_nodes.append(node)
                        node_path.append(node)
                a = self.node_pointers
                end = self.node_pointers[block_path[len(block_path) - 1]]
                node_path.append(self.node_pointers[block_path[len(block_path) - 1]])  # end

            # draw two more lines
            for card in src.movement.cardinals:
                # offset1 = choice(src.movement.cardinals)
                aux1 = src.linedrawing.get_line(
                    (point1[0] + card[0], point1[1] + card[1]),
                    (point2[0] + card[0], point2[1] + card[1]),
                )
                block_path.extend(aux1)
            # render
            road_segment = RoadSegment(point1, point2, middle_nodes, road_type, self.road_segs)
            for block in block_path:
                x = block[0]
                z = block[1]
                y = int(self.rel_ground_hm[x][z]) - 1
                set_state_block(self, x, y, z, "minecraft:blue_concrete")
            self.set_type_road(node_path, src.my_utils.Type.MAJOR_ROAD.name)


    # def init_main_st(self, water_pts):
    #     (x1, y1) = random.choice(water_pts)  # start in water
    #     n = self.array[x1][y1]
    #     n1_options = list(set(n.range()) - set(n.local()))
    #     n1 = np.random.choice(n1_options, replace=False)
    #     while Type.WATER in n1.type:  # generate and test until n1 isn't water
    #         n1 = np.random.choice(n1_options, replace=False)
    #     n2_options = list(set(n1.range()) - set(n1.local()))
    #     n2 = np.random.choice(n2_options, replace=False)
    #     points = get_line((n1.x, n1.y), (n2.x, n2.y))
    #     while any(Type.WATER in self.array[x][y].type for (x, y) in
    #               points):  # if any of the points of the potential road are in water, regenerate
    #         n2 = np.random.choice(n2_options, replace=False)
    #         points = get_line((n1.x, n1.y), (n2.x, n2.y))
    #
    #     (x1, y1) = points[0]
    #     (x2, y2) = points[len(points) - 1]
    #     self.set_type_road(points, Type.MAJOR_ROAD)
    #     middle_nodes = []
    #     if len(points) > 2:
    #         middle_nodes = points[1:len(points) - 1]
    #     self.roadsegments.add(
    #         RoadSegment(self.array[x1][y1], self.array[x2][y2], middle_nodes, Type.MAJOR_ROAD, self.roadsegments))
    #     for (x, y) in points:
    #         adjacent = self.array[x][y].adjacent
    #         adjacent = [s for n in adjacent for s in n.adjacent]  # every node in the road builds buildings around them
    #         for pt in adjacent:
    #             if pt not in points:
    #                 self.set_type_building([self.array[pt.x][pt.y]])
    #     self.init_lots(x1, y1, x2, y2)  # main street is a lot


    def append_road(self, point, road_type):
        # convert point to node
        point = self.node_pointers[point]
        # self.roads.append((point1))
        closest_point, middle_points = self.get_closest_point(self.nodes[self.node_pointers[point]], # get closest point to any road
                                                              [],
                                                              self.roads,
                                                              road_type,
                                                              False)
        self.create_road(point, closest_point, road_type)




    def get_closest_point(self, node, lots, possible_targets, road_type, leave_lot, correction=5):
        x, z = node.center
        nodes = possible_targets
        nodes = [n for n in nodes if src.my_utils.Type.BRIDGE.name not in n.type]
        if len(nodes) == 0:
            print("leave_lot = {} no road segments".format(leave_lot))
            return None, None
        for i in nodes:
            a = i
        dists = [math.hypot(n.center[0] - x, n.center[1] - z) for n in nodes]
        node2 = nodes[dists.index(min(dists))]
        (x2, z2) = (node2.center[0], node2.center[1])
        xthr = 2
        zthr = 2
        if node.lot is None:
            if road_type is not src.my_utils.Type.MINOR_ROAD.name and abs(x2 - x) > xthr and abs(
                    z2 - z) > zthr:
                if node2.lot is not None:
                    (cx2, cy2) = node2.lot.center
                    (x, z) = (x + x - cx2, z + z - cy2)
                    # clamp road endpoints
                    if x >= self.len_x:
                        x = self.len_x - 1
                    if x < 0:
                        x = 0
                    if z >= self.len_z:
                        z = self.len_z - 1
                    if z < 0:
                        z = 0
                if abs(x2 - x) > 10 and abs(z2 - z) > 10:
                    if not node.landscape.add_lot([(x2, z2), (x, z)]):
                        print("leave_lot = {} add lot failed".format(leave_lot))
                        return None, None
            else:
                return None, None
        points = src.linedrawing.get_line((x, z), (node2.center[0], node2.center[1]))
        if len(points) <= 2:
            return None, None
        if not leave_lot:
            for (i, j) in points:
                if src.my_utils.Type.WATER.name in self.nodes[self.node_pointers[(i, j)]].type:
                    return None, None
        closest_point = (node2.center[0], node2.center[1])
        return closest_point, points


    def apply_local_prosperity(self, x, z, value):
        self.prosperities[x][z] += value


def set_state_block(state, x, y, z, block_name):
    state.blocks[x][y][z] = block_name
    key = src.my_utils.convert_coords_to_key(x, y, z)
    state.changed_blocks[key] = block_name


class RoadSegment:
    def __init__(self, rnode1, rnode2, nodes, type, rs_list):
        self.start = rnode1
        self.end = rnode2
        self.type = type
        self.shape = []
        self.nodes = nodes


    def merge(self, rs2, match, rs_list, roadnodes):
        if self.type != rs2.type:
            return
        if self.start == match:
            self.shape.reverse()
            self.start = self.end
        self.shape.append((match.x, match.y))
        self.nodes.append((match.x, match.y))
        if rs2.end == match:
            rs2.shape.reverse()
            rs2.end = rs2.start
        self.shape.extend(rs2.shape)
        self.nodes.extend(rs2.nodes)
        self.end = rs2.end
        rs_list.discard(rs2)
        roadnodes.remove(match)
        roadnodes.remove(match)


    def split(self, node, rs_list, roadnodes):
        roadnodes.append(node)
        roadnodes.append(node)

        i = 0
        while i < len(self.nodes) - 1:
            if self.nodes[i] == (node.x, node.y):
                break
            i += 1
        nodes1 = self.nodes[:i]
        nodes2 = self.nodes[i + 1:]

        new_rs = RoadSegment(node, self.end, nodes2, self.type, roadnodes)
        rs_list.add(new_rs)

        self.nodes = nodes1
        self.end = node


class Lot:
    def __init__(self, state, points):
        self.state = state
        # self.neighbors = set() # neighbor lots, not currently used
        self.get_lot(points)

    def get_pt_avg(self, points):
        x = sum(x for (x, y) in points) / len(points)
        y = sum(y for (x, y) in points) / len(points)
        return (x, y)

    def get_lot(self, points):
        [pt1, pt2] = points

        (ax, ay) = self.get_pt_avg(points)
        self.center = (cx, cy) = (int(ax), int(ay))
        center_node = self.state.nodes[(cx,cy)]

        lot = set([center_node])
        self.border = set()
        while True:
            neighbors = set([e for n in lot for e in n.adjacent if \
                             e not in lot and e.lot is None and e.x != pt1[0] and e.x != pt2[0] and e.y != pt1[
                                 1] and e.y != pt2[1] \
                             and src.my_utils.Type.WATER.name not in e.type])
            if len(neighbors) > 0:
                lot.update(neighbors)
                self.border = neighbors
            else:
                break

        for node in lot:
            node.lot = self
        self.nodes = lot


    def get_nodes(self):
        return self.nodes
