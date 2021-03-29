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
    road_segs = []
    built = set()

    ## Create surface grid
    def __init__(self, world_slice=None, blocks_file=None, max_y_offset=tallest_building_height):
        if not world_slice is None:
            self.blocks, self.world_y, self.len_y, self.abs_ground_hm = self.gen_blocks_array(world_slice)
            self.rel_ground_hm = self.gen_rel_ground_hm(self.abs_ground_hm)  # a heightmap based on the state's y values. -1
            self.heightmaps = world_slice.heightmaps
            self.types = self.gen_types("MOTION_BLOCKING_NO_LEAVES")  # 2D array. Exclude leaves because it would be hard to determine tree positions
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
        nodes = {}  # contains coord pointing to data struct
        node_pointers = np.full((len_x,len_z), None)
        for x in range(nodes_in_x):
            for z in range(nodes_in_z):
                cx = x*node_size+1
                cz = z*node_size+1
                node = self.Node(center=(cx, cz), types=[src.my_utils.Type.BROWN.name])  # TODO change type
                nodes[(cx, cz)] = node
                node_pointers[cx][cz] = (cx, cz)
                for dir in src.movement.directions:
                    nx = cx + dir[0]
                    nz = cz + dir[1]
                    node_pointers[nx][nz] = (cx, cz)

        return nodes, node_pointers


    class Node:

        def __init__(self, center, types):
            self.center = center
            self.size = 3
            self.local_prosperity = 0  # sum of all of its blocks
            self.type = set()
            self.type.update(types)
            self.neighbors = set()
            self.lot = None

        def add_type(self, type):
            self.type.add(type)


        def clear_type(self, built_arr):
            if self in built_arr:
                built_arr.discard(self)
            # if src.my_utils.BUILDING.name
            self.type.clear()


        def add_neighbor(self, node):
            self.neighbors.add(node)



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
        #         new_type = "FOREST"
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


    def gen_types(self, heightmap_name):
        types = []
        for x in range(len(self.blocks)):
            types.append([])
            for z in range(len(self.blocks[0][0])):
                type = self.determine_type(x, z, heightmap_name)
                if type == "TREE":
                    self.trees.append((x, z))
                types[x].append(type)
        print("done initializing types")
        return types


    def determine_type(self, x, z, heightmap_name="MOTION_BLOCKING_NO_LEAVES"):
        block_y = self.heightmaps[heightmap_name][x][z] - self.world_y + self.heightmap_offset
        block = self.blocks[x][block_y][z]
        for i in range(1, len(src.my_utils.Type)+1):
            if block in src.my_utils.Type_Tiles.tile_sets[i]:
                return src.my_utils.Type(i).name
        return src.my_utils.Type.AIR.name



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


    def set_block(self, x, y, z, block_name):
        self.blocks[x][y][z] = block_name
        key = src.my_utils.convert_coords_to_key(x, y, z)
        self.changed_blocks[key] = block_name


    def set_type_road(self, node_points, road_type):
        for point in node_points:
            print(self.nodes)
            node = self.nodes[point]
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


    def append_road(self, point, road_type):
        # self.roads.append((point1))
        self.roads.append(self.nodes[self.node_pointers[point]])
        block_path = src.linedrawing.get_line(point)  # inclusive
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
                (point[0] + card[0], point[1] + card[1]),
                (point2[0] + card[0], point2[1] + card[1]),
            )
            block_path.extend(aux1)
        # render
        road_segment = RoadSegment(point, point2, middle_nodes, road_type, self.road_segs)
        for block in block_path:
            x = block[0]
            z = block[1]
            y = int(self.rel_ground_hm[x][z]) - 1
            set_state_block(self, x, y, z, "minecraft:blue_concrete")
        self.set_type_road(node_path, src.my_utils.Type.MAJOR_ROAD.name)


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
        closest_point = (node2.center[1], node2.center[1])
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

