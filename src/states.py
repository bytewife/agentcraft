#! /usr/bin/python3
"""### State data
Contains tools for modifying the state of the blocks in an area given by Simulation.
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"

import http_framework.interfaceUtils
import http_framework.worldLoader

import src.my_utils
import src.movement_backup
import src.pathfinding
import src.scheme_utils
import src.agent
import src.linedrawing
import src.manipulation
import src.chronicle
import src.node
import src.lot
import src.road_segment

from random import choice, random, randint
import names
import math
import numpy as np


class State:
    AGENT_HEADS = []
    TALLEST_BUILDING_HEIGHT = 30
    UNWALKABLE = ['minecraft:water', 'minecraft:lava']
    AGENT_HEIGHT = 2
    AGENT_JUMP = 1
    HEIGHTMAP_OFFSET = -1
    NODE_SIZE = 3
    MAX_SECTOR_PROPAGATION_DEPTH = 150

    def __init__(self, rect, world_slice, precomp_legal_actions=None, blocks_file=None, precomp_pathfinder=None,
                 precomp_sectors=None, precomp_types=None, precomp_nodes=None, precomp_node_pointers=None,
                 max_y_offset=TALLEST_BUILDING_HEIGHT, water_with_adjacent_land=None):
        if world_slice:
            self.rect = rect
            self.world_slice = world_slice
            self.world_y = self.world_x = self.world_z = 0
            self.len_x = self.len_y = self.len_z = 0
            ##### MEMOIZE FEATURES
            self.blocks_arr = []  # 3D Array of all the assets in the state
            self.trees = []
            self.saplings = []
            self.water = []
            self.lava = set()
            self.roads = []
            self.road_nodes = []
            self.road_blocks = set()
            self.road_segs = set()
            self.construction = set()  # nodes where buildings can be placed
            self.lots = set()
            self.blocks_near_land = set()  # blocks adjacent to a non-water
            self.world_x = self.rect[0]
            self.world_z = self.rect[1]
            self.len_x = self.rect[2] - self.rect[0]
            self.len_z = self.rect[3] - self.rect[1]
            self.end_x = self.rect[2]
            self.end_z = self.rect[3]
            self.interface, self.blocks_arr, self.world_y, self.len_y, self.abs_ground_hm = self.gen_blocks_array(
                world_slice)
            self.rel_ground_hm = self.init_rel_ground_hm(self.abs_ground_hm)  # Gen relative heighmap
            self.static_ground_hm = self.gen_static_ground_hm(self.rel_ground_hm)  # Gen unchanging rel heightmap
            self.heightmaps = world_slice.heightmaps
            self.built = set() # Bulding nodes
            self.foreign_built = set() # non-generated Building nodes
            self.road_set = choice(src.my_utils.set_choices)
            self.generated_a_road = False  # prevents buildings blocking in the roads
            self.nodes_dict = {}
            ##### REUSE PRECOMPUTATIONS
            if precomp_nodes is None or precomp_node_pointers is None:
                self.node_pointers = self.init_node_pointers(self.len_x, self.len_z, self.NODE_SIZE)
            else:
                self.nodes_dict = precomp_nodes
                self.node_pointers = precomp_node_pointers
                nodes_in_x = int(self.len_x / self.NODE_SIZE)
                nodes_in_z = int(self.len_z / self.NODE_SIZE)
                self.last_node_pointer_x = nodes_in_x * self.NODE_SIZE - 1  # TODO verify the -1
                self.last_node_pointer_z = nodes_in_z * self.NODE_SIZE - 1
            if precomp_types == None:
                self.types = self.gen_types(self.rel_ground_hm)
            else:
                self.types = precomp_types
            if precomp_legal_actions is None:
                self.legal_actions = src.movement_backup.gen_all_legal_actions(self,
                                                                               self.blocks_arr,
                                                                               vertical_ability=self.AGENT_JUMP,
                                                                               heightmap=self.rel_ground_hm,
                                                                               actor_height=self.AGENT_HEIGHT,
                                                                               unwalkable_blocks=["minecraft:water",
                                                                                                  'minecraft:lava'])
            else:
                self.legal_actions = precomp_legal_actions
            if precomp_pathfinder is None:
                self.pathfinder = src.pathfinding.Pathfinding(self)
            else:
                self.pathfinder = precomp_pathfinder
            if precomp_sectors is None:
                self.sectors = self.pathfinder.create_sectors(self.heightmaps["MOTION_BLOCKING_NO_LEAVES"],
                                                              self.legal_actions)
            else:
                self.sectors = precomp_sectors
            self.prosperity = np.zeros((self.len_x, self.len_z))
            self.traffic = np.zeros((self.len_x, self.len_z))
            self.update_flags = np.zeros((self.len_x, self.len_z))
            self.built_heightmap = {}
            self.exterior_heightmap = {}
            self.generated_building = False
            self.changed_blocks = {}
            self.changed_blocks_xz = set()
            self.total_changed_blocks = {}
            self.total_changed_blocks_xz = set()
            self.phase = 1
            ##### BUILDINGS
            self.build_minimum_phase_1 = max(*[building_pair[1] for building_pair in src.my_utils.STRUCTURES['small']])
            self.build_minimum_phase_2 = max(*[building_pair[1] for building_pair in src.my_utils.STRUCTURES['med']])
            self.build_minimum_phase_3 = max(*[building_pair[1] for building_pair in src.my_utils.STRUCTURES['large']])
            # TODO parametrize these
            self.phase2threshold = 200
            self.phase3threshold = 500
            self.flag_color = choice(src.my_utils.colors)
            #####
            self.traverse_from = np.copy(self.rel_ground_hm)
            self.traverse_update_flags = np.full((len(self.rel_ground_hm), len(self.rel_ground_hm[0])), False,
                                                 dtype=bool)  # Flag that block needs to be updated
            self.hm_update_flags = set()
            self.dont_update_again = set()
            self.water_near_land = list(set(self.water).intersection(self.blocks_near_land))
            self.step_number = 0
            self.last_platform_extension = "minecraft:dirt"
            #### AGENTS
            self.agents = dict()  # holds agent and position
            self.agent_nodes = self.init_agent_nodes()
            self.new_agents = set()  # agents that were just created
            self.max_agents = 10
            self.num_agents = 0
            self.adam = src.agent.Agent(self, 0, 0, self.rel_ground_hm, "Adam, the Original", "")
            self.eve = src.agent.Agent(self, 0, 0, self.rel_ground_hm, "Eve, the Original", "")
        else:  # for testing
            print("State instantiated for testing!")

            def parse_blocks_file(file_name):
                size, blocks = src.scheme_utils.get_schematic_parts(file_name)
                dx, dy, dz = size
                blocks3D = [[[0 for z in range(dz)] for y in range(dy)] for x in range(dx)]
                for x in range(dx):
                    for y in range(dy):
                        for z in range(dz):
                            index = y * (dz) * (dx) + z * (dx) + x
                            inv_y = dy - 1 - y
                            blocks3D[x][inv_y][z] = "minecraft:" + blocks[index]
                return dx, dy, dz, blocks3D

            self.len_x, self.len_y, self.len_z, self.blocks_arr = parse_blocks_file(blocks_file)

    def reset(self):
        """
        Reset values that must be deleted in between initialization attempts
        :param use_heavy:
        :return:
        """
        self.built.clear()
        self.roads.clear()
        self.agents.clear()
        self.new_agents.clear()
        self.construction.clear()
        self.road_nodes = []
        self.road_segs.clear()
        self.nodes_dict = {}
        self.node_pointers = self.init_node_pointers(self.len_x, self.len_z, self.NODE_SIZE)
        self.agent_nodes.clear()
        for pos in self.changed_blocks.keys():
            x, y, z = pos
            self.blocks_arr[x][y][z] = 0
        self.changed_blocks.clear()
        self.total_changed_blocks = {}
        self.total_changed_blocks_xz.clear()
        self.changed_blocks_xz.clear()
        src.chronicle.chronicles = src.chronicle.chronicles_empty.copy()
        self.agent_nodes = self.init_agent_nodes()

    def blocks(self, x, y, z):
        """
        Return lazily loaded blocks
        :param x:
        :param y:
        :param z:
        :return:
        """
        if self.blocks_arr[x][y][z] == 0:
            self.blocks_arr[x][y][z] = self.world_slice.getBlockAt(self.world_x + x, self.world_y + y, self.world_z + z)
        return self.blocks_arr[x][y][z]

    def gen_static_ground_hm(self, a):
        """
        Generate static ground heightmap
        :param a:
        :return:
        """
        hm = np.copy(a)
        for x in range(len(a)):
            for z in range(len(a[0])):
                y = a[x][z] - 1
                while y > 0 and (src.manipulation.is_log(self, x, y, z) or self.blocks(x, y, z) in
                                 src.my_utils.BLOCK_TYPE.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value]):
                    y -= 1
                hm[x][z] = y + 1
        return hm

    def init_agent_nodes(self):
        """
        Empty initialize agent_nodes
        :return:
        """
        result = dict()
        for x in range(int(self.len_x / self.NODE_SIZE)):
            for z in range(int(self.len_z / self.NODE_SIZE)):
                cx = x * 3 + 1
                cz = z * 3 + 1
                result[(cx, cz)] = set()
        return result

    def find_build_spot(self, ax, az, building_file, wood_type, ignore_sector=False, max_y_diff=4, build_tries=25):
        """
        Find a valid building location for given building
        :param ax: 
        :param az: 
        :param building_file: 
        :param wood_type: 
        :param ignore_sector: 
        :param max_y_diff: 
        :param build_tries: 
        :return:
        """
        f = open(building_file, "r")
        size = f.readline()
        f.close()
        x_size, y_size, z_size = [int(n) for n in size.split(' ')]
        i = 0
        # build_tries = 25
        while i < build_tries:
            construction_site = choice(list(self.construction))
            result = self.check_build_spot(construction_site, building_file, x_size, z_size, wood_type,
                                           max_y_diff=max_y_diff)
            if result != None:
                # check if any of the nodes are in built
                if result[1] in self.built:
                    continue
                not_in_built = True
                for node in result[2]:
                    if node in self.built:
                        not_in_built = False
                        break
                # see if found road is in same sector
                if not_in_built:
                    nx, nz = result[0].center
                    if self.sectors[ax][az] == self.sectors[nx][nz] or ignore_sector:  # this seems wrong
                        assert type(result[2]) == set
                        for node in result[2].union({result[1]}):  # this is equal to
                            # src.states.set_state_block(self.state, node.center[0], self.state.rel_ground_hm[node.center[0]][node.center[1]]+10, node.center[1], 'minecraft:gold_block')
                            self.built.add(
                                node)  # add to built in order to avoid roads being placed before buildings placed
                            pass
                        return result
            i += 1
        return False

    def check_build_spot(self, ctrn_node, bld, bld_lenx: int, bld_lenz: int, wood_type: str, max_y_diff: int):
        """
        Validate building location and return its stats if valid
        :param ctrn_node:
        :param bld: building file name
        :param bld_lenx:
        :param bld_lenz:
        :param wood_type:
        :param max_y_diff:
        :return: None if invalid spot, otherwise, a tuple of
        found_road, ctrn_node, found_nodes, ctrn_dir, bld, rot, min_nodes_in_x, min_nodes_in_z, self.built, wood_type
        """
        min_nodes_in_x = math.ceil(bld_lenx / ctrn_node.size)
        min_nodes_in_z = math.ceil(bld_lenz / ctrn_node.size)
        min_tiles = min_nodes_in_x * min_nodes_in_z
        found_ctrn_dir = None
        found_nodes = set()
        # Get rotation based on neighboring road
        found_road = None
        face_dir = None
        for dir in src.movement_backup.cardinals:  # maybe make this cardinal only
            nx = ctrn_node.center[0] + dir[0] * ctrn_node.size
            nz = ctrn_node.center[1] + dir[1] * ctrn_node.size
            if self.out_of_bounds_Node(nx, nz): continue
            neighbor = self.nodes(*self.node_pointers[(nx, nz)])
            if neighbor in self.roads:
                found_road = neighbor
                face_dir = dir
            if neighbor in self.built:
                return None  # Don't put buildings next to each other
        if found_road is None:
            return None
        rot = 0
        if face_dir[0] == 1: rot = 2
        if face_dir[0] == -1: rot = 0
        if face_dir[1] == -1: rot = 1
        if face_dir[1] == 1: rot = 3
        if rot in [1, 3]:
            temp = min_nodes_in_x
            min_nodes_in_x = min_nodes_in_z
            min_nodes_in_z = temp
        # Find site where x and z are reversed. this rotates
        highest_y = self.rel_ground_hm[ctrn_node.center[0]][ctrn_node.center[1]]
        lowest_y = self.rel_ground_hm[ctrn_node.center[0]][ctrn_node.center[1]]
        for dir in src.movement_backup.diagonals:
            if found_ctrn_dir != None:
                break
            tiles = 0
            is_valid = True
            for x in range(0, min_nodes_in_x):
                for z in range(0, min_nodes_in_z):
                    nx = ctrn_node.center[0] + x * ctrn_node.size * dir[0]
                    nz = ctrn_node.center[1] + z * ctrn_node.size * dir[1]
                    if self.out_of_bounds_Node(nx, nz):
                        is_valid = False
                        break
                    ny = self.rel_ground_hm[nx][nz]
                    if ny > highest_y:
                        highest_y = ny
                    elif ny < lowest_y:
                        lowest_y = ny
                    node = self.nodes(nx, nz)
                    # Validate
                    if not node in self.construction or \
                            node in self.roads or \
                            node in self.built or \
                            node.center in self.foreign_built:
                        is_valid = False
                        break
                    for tile in node.get_tiles():
                        if tile in self.water or tile in self.lava:
                            is_valid = False
                            break
                    tiles += 1
                    found_nodes.add(node)
                if is_valid == False:
                    break
            # Check that all tiles were valid
            if tiles == min_tiles:
                # All tiles were valid
                found_ctrn_dir = dir
                break
            else:
                found_nodes.clear()
        max_y_diff = max_y_diff  # was 4, but increased to 5 bc placing the initial building took too long
        for tile in found_road.get_tiles():
            ny = self.rel_ground_hm[tile[0]][tile[1]]
            if ny > highest_y:
                highest_y = ny
            elif ny < lowest_y:
                lowest_y = ny
        if found_ctrn_dir == None or highest_y - lowest_y > max_y_diff:  # If there's not enough space. Return invalid
            return None
        return (
            found_road, ctrn_node, found_nodes, found_ctrn_dir, bld, rot, min_nodes_in_x, min_nodes_in_z, self.built,
            wood_type)

    def get_node_max_height(self, node, hm):
        """
        Get highest y-value in Node
        :param node:
        :param hm:
        :return:
        """
        i = 0
        highest = 0
        for tile in node.get_tiles():
            x = tile[0]
            z = tile[1]
            y = hm[x][z]
            if y > highest:
                highest = y
            i += 1
        return highest

    def add_prosperity(self, x, z, amt):
        # defer to the housing Node's prosperity
        node_pos = self.node_pointers[(x, z)]
        if node_pos is None: return
        self.nodes(x, z).add_prosperity(amt)

    def traverse_up(self, x: int, z: int, max_y: int):
        """
        Return array of y-value going up to max_y
        :param x:
        :param z:
        :param max_y:
        :return:
        """
        start_y = self.rel_ground_hm[x][z]
        result = []
        for y in range(start_y, max_y + 1):
            result.append(y)
        return result

    def set_platform(self, found_nodes_iter=None, wood_type="oak", build_y=None):
        """
        Place scaffold platform extending from build_y downwards
        :param found_nodes_iter:
        :param wood_type:
        :param build_y:
        :param use_scaffolding:
        :return:
        """
        found_nodes = list(found_nodes_iter)
        fill = "minecraft:scaffolding"
        py = build_y - 1
        for node in found_nodes:
            for tile in node.get_tiles():
                tx = tile[0]
                tz = tile[1]
                traverse = self.traverse_up(tx, tz, py - 1)
                block = self.blocks(tx, py, tz)
                if block in src.my_utils.BLOCK_TYPE.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value]:
                    block = self.blocks(tx, self.static_ground_hm[tx][tz] - 1, tz)
                    # Extend with dirt if road block
                    if block in src.my_utils.BLOCK_TYPE.tile_sets[src.my_utils.TYPE.MAJOR_ROAD.value]:
                        fill = "minecraft:dirt"
                        set_state_block(self, tx, self.static_ground_hm[tx][tz] - 1, tz, fill)
                    if len(traverse) > 1:
                        for y in traverse:
                            set_state_block(self, tx, y, tz, fill)
                        block = wood_type + '_planks'
                    elif len(traverse) == 1:
                        set_state_block(self, tx, py - 1, tz, block)
                    set_state_block(self, tx, py, tz, block)
        return True

    def place_building(self,found_road, ctrn_node, found_nodes, ctrn_dir, bld, rot, min_nodes_in_x, min_nodes_in_z, built_arr, wood_type, ignore_road=False):
        """
        Place building via custom schematic file
        :param found_road:
        :param ctrn_node:
        :param found_nodes:
        :param ctrn_dir:
        :param bld:
        :param rot:
        :param min_nodes_in_x:
        :param min_nodes_in_z:
        :param wood_type:
        :return:
        """
        # Get box dimensions
        x1 = ctrn_node.center[0] - ctrn_dir[0]  # to uncenter
        z1 = ctrn_node.center[1] - ctrn_dir[1]
        x2 = ctrn_node.center[0] + ctrn_dir[0] + ctrn_dir[0] * ctrn_node.size * (min_nodes_in_x - 1)
        z2 = ctrn_node.center[1] + ctrn_dir[1] + ctrn_dir[1] * ctrn_node.size * (min_nodes_in_z - 1)
        xf = min(x1, x2)  # since the building is placed is ascending
        zf = min(z1, z2)
        lowest_y = self.get_node_max_height(found_road, self.static_ground_hm)
        radius = math.ceil(ctrn_node.size / 2)
        # Check if in bounds
        for node in found_nodes.union({ctrn_node}):
            for x in range(-radius, radius + 1):
                for z in range(-radius, radius + 1):
                    nx = node.center[0] + x
                    nz = node.center[1] + z
                    if self.out_of_bounds_Node(nx, nz): continue
                    by = self.rel_ground_hm[nx][nz]
        y = lowest_y  # This should be the lowest y in the
        base_y = lowest_y
        front_length = min_nodes_in_x
        use_x = False
        # Determine build orientation by building rotation
        if rot == 1 or rot == 3:
            use_x = True
        if use_x:
            offset = 1 if ctrn_node.center[1] > found_road.center[1] else -1
        else:
            offset = 1 if ctrn_node.center[0] > found_road.center[0] else -1
        front_tiles = []
        front_nodes = []
        highest_y = self.static_ground_hm[ctrn_node.center[0]][
            ctrn_node.center[1]]  # for checking if the diff is too large, and putting it at top if it is
        lowest_y = highest_y
        y_sum = 0
        # Validate nodes in box
        for i in range(front_length - 1, -1, -1):
            front_length = min_nodes_in_z
            nx, nz = ctrn_node.center
            nx += (use_x ^ 1) * self.NODE_SIZE * (rot - 1)
            nz += (use_x ^ 0) * self.NODE_SIZE * (rot - 2)
            nx += i * self.NODE_SIZE * (use_x ^ 0) * ctrn_dir[0]
            nz += i * self.NODE_SIZE * (use_x ^ 1) * ctrn_dir[1]
            for r in range(-1, 2):
                fx = nx + r * (use_x ^ 0) + (use_x ^ 1) * offset
                fz = nz + r * (use_x ^ 1) + (use_x ^ 0) * offset
                front_tiles.append((fx, fz))
                if self.out_of_bounds_Node(fx,
                                           fz):  # TODO: get rid of this and let prior fnuctions deal with it- prolly causes a bug
                    return False, None
                fy = self.static_ground_hm[fx, fz]
                if highest_y < fy:
                    highest_y = fy
                elif lowest_y > fy:
                    lowest_y = fy
                y_sum += fy
            node_ptr = self.node_pointers[(nx, nz)]
            if node_ptr is None: continue
            node = self.nodes(*node_ptr)
            if node in self.roads or node in self.built or node.center in self.water or node in self.foreign_built: continue
            front_nodes.append(node)  # to use for later
        mean_y = round(y_sum / len(front_tiles))
        adjusting_y_diff = 4
        max_y_diff = 6
        if highest_y - lowest_y > max_y_diff:
            return False, None
        if highest_y - lowest_y > adjusting_y_diff:
            mean_y = highest_y
        status, building_heightmap, exterior_heightmap = src.scheme_utils.place_building_in_state(self, bld, xf,
                                                                                                  mean_y, zf,
                                                                                                  rot=rot,
                                                                                                  built_arr=self.built,
                                                                                                  wood_type=wood_type)
        # Check if placement succeeded
        if status == False:
            for node in found_nodes.union({ctrn_node}):
                self.built.remove(node)  # since this was set early in check_build_spot, remove it
            return False, None
        self.set_platform(found_nodes, wood_type, mean_y)
        built_list = list(building_heightmap.keys())
        ext_list = list(exterior_heightmap.keys())
        def update_hm_bld_block(self, x, z):
            if (x, z) in self.built_heightmap:  # ignore buildings
                y = self.built_heightmap[(x, z)] - 1
                self.abs_ground_hm[x][z] = y + self.world_y
                self.rel_ground_hm[x][z] = y + 1
            elif (x, z) in self.exterior_heightmap:
                y = self.exterior_heightmap[(x, z)] - 1
                self.abs_ground_hm[x][z] = y + self.world_y
                self.rel_ground_hm[x][z] = y + 1
            else:  # traverse down to find first non passable block
                y = self.traverse_down_till_block(x, z) + 1  # only call this if needs traversing
                self.abs_ground_hm[x][z] = y + self.world_y - 1
                self.rel_ground_hm[x][z] = y
            curr_height = self.rel_ground_hm[x][z]
            if self.static_ground_hm[x][z] > curr_height:  # don't reduce heightmap ever. this is to avoid bugs rn
                self.static_ground_hm[x][z] = curr_height
            return
        for tile in built_list + ext_list:  # let's see if this stops tiles from being placed in buildings, where there used to be ground
            update_hm_bld_block(self,tile[0], tile[1])
        self.built_heightmap.update(building_heightmap)
        self.exterior_heightmap.update(exterior_heightmap)
        self.create_road(found_road.center, ctrn_node.center, road_type="None", points=None, add_road_type=True)
        for n in front_nodes:
            self.append_road(n.center, src.my_utils.TYPE.MINOR_ROAD.name)
        for node in list(found_nodes):
            if node in self.construction:
                self.construction.remove(node)
            self.built.add(node)
            for tile in node.get_tiles():  # remove trees & saplings if they're in build spot
                if tile in self.trees:
                    self.trees.remove(tile)
                    node.type = node.get_type()  # update Types to remove trees
                if tile in self.saplings:
                    self.saplings.remove(tile)
                    node.type = node.get_type()  # update Types to remove saplings
        return True, mean_y

    def get_nearest_tree(self, x, z, iterations=5):
        return src.movement_backup.find_nearest(self, x, z, self.trees, 10, iterations, 15)

    def init_node_pointers(self, len_x, len_z, node_size):
        """
        Initialize nodes
        Not every block has a node. These will point to None
        :param len_x:
        :param len_z:
        :param node_size:
        :return:
        """
        if len_x < 0 or len_z < 0:
            print("Lengths cannot be <0")
        node_size = 3  # in assets
        nodes_in_x = int(len_x / node_size)
        nodes_in_z = int(len_z / node_size)
        self.last_node_pointer_x = nodes_in_x * node_size - 1  # TODO verify the -1
        self.last_node_pointer_z = nodes_in_z * node_size - 1
        node_pointers = np.full((len_x, len_z), None)
        for x in range(nodes_in_x):
            for z in range(nodes_in_z):
                cx = x * node_size + 1
                cz = z * node_size + 1
                node_pointers[cx][cz] = (cx, cz)  # TODO can lazy load this rather than gen here
                for dir in src.movement_backup.directions:
                    nx = cx + dir[0]
                    nz = cz + dir[1]
                    node_pointers[nx][nz] = (cx, cz)
        return node_pointers

    def get_node_center(self, tx, tz):
        xrem = tx % 3
        zrem = tz % 3
        dx = 1 - xrem
        dz = 1 - zrem
        return tx + dx, tz + dz

    def nodes(self, x, z):
        """
        Return a lazily loaded Node
        :param x:
        :param z:
        :return:
        """
        if (x, z) not in self.nodes_dict.keys():
            node = src.node.Node(self, center=(x, z), types=[src.my_utils.TYPE.BROWN.name], size=self.NODE_SIZE)
            node.adjacent_centers = node.gen_adjacent_centers(self)
            node.neighbors_centers = node.gen_neighbors_centers(self)
            node.local_centers = node.gen_local_centers(self)
            node.range_centers = node.gen_range_centers(self)
            self.nodes_dict[(x, z)] = node
        return self.nodes_dict[(x, z)]

    def gen_blocks_array(self, world_slice, max_y_offset=TALLEST_BUILDING_HEIGHT):
        """
        Initialize blocks array
        :param world_slice:
        :param max_y_offset:
        :return:
        """
        x1, z1, x2, z2 = self.rect
        abs_ground_hm = src.my_utils.get_heightmap(world_slice, "MOTION_BLOCKING_NO_LEAVES", -1)  # inclusive of ground
        def get_y_bounds(hm):
            lowest = hm[0][0]
            highest = hm[0][0]
            for col in hm:
                for block_y in col:
                    if (block_y < lowest):
                        lowest = block_y
                    elif (block_y > highest):
                        highest = block_y
            return lowest, highest
        y1, y2 = get_y_bounds(abs_ground_hm)  # keep range not too large
        y2 += max_y_offset
        world_y = y1
        interface = http_framework.interfaceUtils.Interface(x=self.world_x, y=world_y, z=self.world_z,
                                                            buffering=True, caching=True)
        len_z = abs(z2 - z1)
        len_y = abs(y2 - y1)
        len_x = abs(x2 - x1)
        blocks_arr = [[[0 for z in range(len_z)] for y in range(len_y)] for x in
                      range(len_x)]  # the format of the state isn't the same as the file's.
        xi = 0
        yi = 0
        zi = 0
        http_framework.interfaceUtils.globalWorldSlice = self.world_slice
        http_framework.interfaceUtils.globalDecay = np.zeros((self.len_x, 255, self.len_z), dtype=bool)
        for x in range(x1, x2):
            yi = 0
            for y in range(y1, y2):
                zi = 0
                for z in range(z1, z2):
                    zi += 1
                yi += 1
            xi += 1
        len_y = y2 - y1
        return interface, blocks_arr, world_y, len_y, abs_ground_hm

    def init_rel_ground_hm(self, abs_ground_hm):
        """
        Initialize rel_ground_hm
        :param abs_ground_hm:
        :return:
        """
        result = []
        for x in range(len(abs_ground_hm)):
            result.append([])
            for z in range(len(abs_ground_hm[0])):
                state_adjusted_y = int(abs_ground_hm[x][z]) - self.world_y + 1  # + self.heightmap_offset
                result[x].append(state_adjusted_y)
        return result

    def update_heightmaps(self):
        """
        Update heightmaps for all changed blocks
        :return:
        """
        for pos in list(self.hm_update_flags):
            self.update_heightmaps_single(*pos)

    def update_heightmaps_single(self, x, z):
        """
        Update heightmap for a single block at (x,z)
        :param x:
        :param z:
        :return:
        """
        if (x, z) in self.built_heightmap:  # Building
            y = self.built_heightmap[(x, z)] - 1
            self.abs_ground_hm[x][z] = y + self.world_y
            self.rel_ground_hm[x][z] = y + 1
        elif (x, z) in self.exterior_heightmap:  # Block is in building outer area
            y = self.exterior_heightmap[(x, z)] - 1
            self.abs_ground_hm[x][z] = y + self.world_y
            self.rel_ground_hm[x][z] = y + 1
        else:  # Traverse down to find first non passable block
            y = None
            if self.traverse_update_flags[x][z] == True:
                y = self.traverse_down_till_block(x, z) + 1
                self.traverse_update_flags[x][z] = False
            else:
                y = self.rel_ground_hm[x][z]
            self.abs_ground_hm[x][z] = y + self.world_y - 1
            self.rel_ground_hm[x][z] = y
            self.hm_update_flags.remove((x, z))
        curr_height = self.rel_ground_hm[x][z]
        if self.static_ground_hm[x][z] > curr_height:  # don't reduce heightmap ever. this is to avoid bugs rn
            self.static_ground_hm[x][z] = curr_height

    def traverse_down_till_block(self, x, z):
        """
        Traverse down from y at given (x,z) until solid block reached. Return y-value of block
        :param x:
        :param z:
        :return:
        """
        y = self.traverse_from[x][z] + 1  # don't start from top, but from max_building_height from rel
        while y > 0:
            if self.blocks(x, y, z) not in src.my_utils.BLOCK_TYPE.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value]:
                break
            y -= 1
        return y

    def gen_types(self, heightmap):
        """
        Generate self.types
        :param heightmap:
        :return:
        """
        xlen = self.len_x
        zlen = self.len_z
        if xlen == 0 or zlen == 0:
            print("  Attempt: gen_types has empty lengths.")
        types = [["str" for j in range(zlen)] for i in range(xlen)]
        def add_blocks_near_land(x, z):
            for dir in src.movement_backup.cardinals:
                self.blocks_near_land.add((max(min(x + dir[0], self.len_x), 0), max(min(z + dir[1], self.len_z), 0)))
        for x in range(xlen):
            for z in range(zlen):
                type_name = self.determine_type(x, z, heightmap).name
                if type_name == "WATER":
                    self.water.append((x, z))
                elif type_name == "BROWN":
                    add_blocks_near_land(x, z)
                elif type_name == "GREEN":
                    add_blocks_near_land(x, z)
                elif type_name == "TREE":
                    self.trees.append((x, z))
                    add_blocks_near_land(x, z)
                elif type_name == "ROAD":
                    nptr = self.node_pointers[(x, z)]
                    if nptr != None:
                        node = self.nodes(*nptr)
                        self.roads.append(node)
                        self.road_nodes.add(node)
                elif type_name == "LAVA":
                    self.lava.add((x, z))
                elif type_name == "FOREIGN_BUILT":
                    node_ptr = self.node_pointers[(x, z)]
                    if node_ptr:
                        node = self.nodes(node_ptr)
                        self.foreign_built.add(node)
                types[x][z] = type_name
        return types

    def determine_type(self, x, z, heightmap, yoffset=0):
        """
        Get type of block at (x,z)
        :param x:
        :param z:
        :param heightmap:
        :param yoffset:
        :return:
        """
        block_y = int(heightmap[x][z]) - 1 + yoffset
        block = self.blocks(x, block_y, z)
        for i in range(1, len(src.my_utils.TYPE) + 1):
            if block in src.my_utils.BLOCK_TYPE.tile_sets[i]:
                return src.my_utils.TYPE(i)
        return src.my_utils.TYPE.BROWN

    def step(self, is_rendering=True, use_total_changed_blocks=False):
        """
        Update current State by one timestep
        :param is_rendering:
        :param use_total_changed_blocks:
        :return:
        """
        i = 0
        changed_arr = self.changed_blocks
        changed_arr_xz = self.changed_blocks_xz
        if use_total_changed_blocks:
            changed_arr = self.total_changed_blocks
            changed_arr_xz = self.total_changed_blocks_xz
        n_blocks = len(changed_arr)
        self.old_legal_actions = self.legal_actions.copy()  # needed to update
        for position, block in changed_arr.items():
            x, y, z = position
            if is_rendering == True:
                self.interface.placeBlockBatched(x, y, z, block, n_blocks)
            i += 1
        # Update heightmap
        self.update_heightmaps()  # must wait until all assets are placed
        # Update blocks
        for position in changed_arr_xz:
            x, z = position
            self.update_block_info(x, z)  # Must occur after new assets have been placed.
        changed_arr.clear()
        changed_arr_xz.clear()
        self.update_phase()
        self.step_number += 1

    def update_phase(self):
        """
        Update Phase if corresponding threshold is passed
        :return:
        """
        p = np.sum(self.prosperity)
        if p > self.phase3threshold:
            self.phase = 3
        elif p > self.phase2threshold:
            self.phase = 2

    def update_block_info(self, x, z):
        """
        Update all current-state info for block
        :param x:
        :param z:
        :return:
        """
        for xo in range(-1, 2):
            for zo in range(-1, 2):
                bx = x + xo
                bz = z + zo
                if self.out_of_bounds_2D(bx, bz):
                    continue
                # Update neighbor legal actions
                self.legal_actions[bx][bz] = src.movement_backup.get_legal_actions_from_block(self, self.blocks_arr, bx,
                                                                                              bz,
                                                                                              self.AGENT_JUMP,
                                                                                              self.rel_ground_hm,
                                                                                              self.AGENT_HEIGHT,
                                                                                              self.UNWALKABLE)
        # Update sector
        self.pathfinder.update_sector_for_block(x, z, self.sectors,
                                                sector_sizes=self.pathfinder.sector_sizes,
                                                legal_actions=self.legal_actions,
                                                old_legal_actions=self.old_legal_actions)

    def get_adjacent_block(self, x_origin, y_origin, z_origin, x_off, y_off, z_off):
        x_target = x_origin + x_off
        y_target = y_origin + y_off
        z_target = z_origin + z_off
        if self.out_of_bounds_3D(x_target, y_target, z_target):
            return None
        return self.blocks(x_target, y_target, z_target)

    def get_adjacent_3D(self, x_origin, y_origin, z_origin):
        """
        Return array of blocks adjacent to given (x,y,z) in 3D
        :param x_origin:
        :param y_origin:
        :param z_origin:
        :return:
        """
        adj_blocks = []
        for x_off in range(-1, 2):
            for y_off in range(-1, 2):
                for z_off in range(-1, 2):
                    if x_off == 0 and y_off == 0 and z_off == 0:
                        continue
                    block = self.get_adjacent_block(x_origin, y_origin, z_origin, x_off, y_off, z_off)
                    if block is None:
                        continue
                    adj_blocks.append((block, x_origin + x_off, y_origin + y_off, z_origin + z_off))
        return adj_blocks

    def out_of_bounds_3D(self, x, y, z):
        """
        Check if given (x,y,z) are out of bounds in build area
        :param x:
        :param y:
        :param z:
        :return:
        """
        return x >= self.len_x or y >= self.len_y or z >= self.len_z or x < 0 or y < 0 or z < 0

    def out_of_bounds_2D(self, x, z):
        """
        Check if given (x,z} is out of bounds of the build area's dims
        :param x:
        :param z:
        :return:
        """
        return x < 0 or z < 0 or x >= self.len_x or z >= self.len_z

    def out_of_bounds_Node(self, x, z):
        """
        Check if given (x,z) is out of bounds in Node dimensions
        :param x:
        :param z:
        :return:
        """
        return x < 0 or z < 0 or x > self.last_node_pointer_x or z > self.last_node_pointer_z  # the problem is that some assets don't point to a tile.

    def set_block(self, x, y, z, block_name):
        """
        DEBUG ONLY
        :param x:
        :param y:
        :param z:
        :param block_name:
        :return:
        """
        self.blocks_arr[x][y][z] = block_name
        key = src.my_utils.convert_coords_to_key(x, y, z)
        self.changed_blocks[key] = block_name

    def set_type_building(self, nodes):
        for node in nodes:
            if not node in self.built:
                if src.my_utils.TYPE.GREEN.name in node.get_type() or \
                        src.my_utils.TYPE.BROWN.name in node.type or \
                        src.my_utils.TYPE.TREE.name in node.type:
                    node.clear_type(self)
                    node.add_mask_type(src.my_utils.TYPE.CONSTRUCTION.name)
                    self.construction.add(node)

    def set_type_road(self, node_points, road_type):
        for point in node_points:
            node = self.nodes(*self.node_pointers[point])
            if src.my_utils.TYPE.WATER.name in node.get_type():
                node.clear_type(self)
                node.add_mask_type(
                    src.my_utils.TYPE.BRIDGE.name)  # we don't use add_type. instead we give each tile a type
            else:
                node.clear_type(self)
                node.add_mask_type(road_type)
            for road in self.roads:
                node.add_neighbor(road)
                road.add_neighbor(node)
            if node in self.construction:
                self.construction.discard(node)
            self.roads.append(node)  # put node in roads array
            node.action_cost = 50  # src.states.State.Node.ACTION_COSTS[src.my_utils.TYPE.MINOR_ROAD.name]

    def create_well(self, sx, sz, len_x, len_z):
        """
        Place water well
        :param sx:
        :param sz:
        :param len_x:
        :param len_z:
        :return:
        """
        if len_x < 3 or len_z < 3:
            print("Error: well needs to be at least 3x3")
            return False, -1, []
        height = 2
        well_nodes = set()
        if self.out_of_bounds_Node(sx - 6, sz - 6) or self.out_of_bounds_Node(sx + len_x, sz + len_z):
            return False, -1, []
        else:
            well_tiles = []
            highest_y = self.static_ground_hm[sx][sz] + 1
            for x in range(sx, sx + len_x + 1):
                for z in range(sz, sz + len_z + 1):
                    if highest_y < self.static_ground_hm[x][z]:
                        highest_y = self.static_ground_hm[x][z]
            if highest_y + height > self.len_y:
                return False, -1, []
            # Create water
            for x in range(sx, sx + len_x):
                for z in range(sz, sz + len_z):
                    if (x == sx or x == sx + len_x - 1) and \
                            (z == sz or z == sz + len_z - 1):
                        src.states.set_state_block(self, x, highest_y, z, 'minecraft:air')
                    elif x == sx or x == sx + len_x - 1 or \
                            z == sz or z == sz + len_z - 1:
                        src.states.set_state_block(self, x, highest_y, z, 'minecraft:barrel[facing=up]')
                    else:
                        well_tiles.append((x, z))
                        src.states.set_state_block(self, x, highest_y, z, 'minecraft:water')
                    src.manipulation.flood_kill_logs(self, x, highest_y + 2, z)
                    src.states.set_state_block(self, x, highest_y - 1, z, 'minecraft:barrel[facing=up]')
                    src.states.set_state_block(self, x, highest_y + 1, z, 'minecraft:air')
                    src.states.set_state_block(self, x, highest_y + 2, z, 'minecraft:air')
                    self.built.add(self.nodes(*self.node_pointers[(x, z)]))
                    well_nodes.add(self.nodes(*self.node_pointers[(x, z)]))
        return well_nodes, highest_y, well_tiles

    def init_main_st(self, viable_water_choices, attempt):
        """
        Initialize the starting road + building
        Return
        (True, old_water, p1, agent_a) on success
        (False, [], [], None)          on failure
        :param viable_water_choices:
        :param attempt:
        :return:
        """
        well_tiles = []
        water_choices = viable_water_choices
        if len(self.water) <= 10:  # or create_well:
            sx = randint(0, self.last_node_pointer_x)
            sz = randint(0, self.last_node_pointer_z)
            result, y, well_tiles = self.create_well(sx, sz, 4, 4)
            while result is False:
                sx = randint(0, self.last_node_pointer_x)
                sz = randint(0, self.last_node_pointer_z)
                result, y, well_tiles = self.create_well(sx, sz, 4, 4)
            if result == False:
                print("could not build well")
                return False, [], [], None
            well_y = y - 1
            if well_y >= 0:
                self.set_platform(found_nodes_iter=result, build_y=well_y)
            water_choices = well_tiles
        old_water = self.water.copy()
        self.water = self.water + well_tiles
        rand_index = randint(0, len(water_choices) - 1)
        x1, y1 = water_choices[rand_index]
        n_pos = self.node_pointers[(x1, y1)]
        water_checks = 100
        def find_other_water(self, water, n_pos, water_checks, rand_index):
            i = 0
            pos = n_pos
            rand_index = rand_index
            while pos == None:
                if rand_index in water:
                    water.remove(rand_index)
                if i > water_checks:
                    return False
                rand_index = randint(0, len(water) - 1)
                x1, y1 = water[rand_index]
                pos = self.node_pointers[(x1, y1)]
                i += 1
            return n_pos, rand_index
        n_pos, rand_index = find_other_water(self, water_choices, n_pos, water_checks, rand_index)
        if n_pos == False or n_pos == None:
            print(f"  Attempt {attempt}: could not find suitable water source. Trying again~")
            self.water = old_water
            return False, [], [], None
        n = self.nodes(*n_pos)
        loc = n.local()
        ran = n.range()
        n1_options = list(set(ran) - set(loc))  # Don't put water right next to water, depending on range
        if len(n1_options) < 1:
            print(f"  Attempt {attempt}: could not find any valid starting road options. Trying again~")
            self.water = old_water
            return False, [], [], None
        n1 = np.random.choice(n1_options, replace=False)  # Pick random point of the above
        def find_valid_start(self, n1, n1_options, water_checks):
            i = 0
            result = n1
            def is_safe_node(self, node):
                return src.my_utils.TYPE.WATER.name not in node.type and src.my_utils.TYPE.LAVA.name not in node.type and src.my_utils.TYPE.FOREIGN_BUILT.name not in node.type
            while not is_safe_node(self, result):  # generate and test until n1 isn't water
                # n1 = np.random.choice(n1_options, replace=False)  # too slow?
                result = n1_options.pop()
                if i >= water_checks or len(n1_options) > 0:
                    return False
                i += 1
            return result
        n1 = find_valid_start(self, n1, n1_options, water_checks)
        if n1 == False:
            print(f"  Attempt {attempt}: could not find valid starting road option. Trying again~")
            self.water = old_water
            return False, [], [], None
        n2_options = list(set(n1.range()) - set(
            n1.local()))  # the length of the main road is the difference between the local and the range
        if len(n2_options) < 1:
            print(f"  Attempt {attempt}: could not find ending road options. Trying again~")
            self.water = old_water
            return False, [], [], None
        n2 = np.random.choice(n2_options, replace=False)  # n2 is based off of n1's range, - local to make it farther
        points = src.linedrawing.get_line((n1.center[0], n1.center[1]), (n2.center[0], n2.center[1]))
        limit = 200
        def find_other_paths(self, node1, node2, n2_options, points, limit):
            """
            Find a new path using n2_options as alternative ends
            :param node1:
            :param node2:
            :param n2_options:
            :param points:
            :param limit:
            :return:
            """
            find_new_n2 = True
            i = 0
            n1 = node1
            n2 = node2
            while find_new_n2:
                if i > limit:
                    return False
                find_new_n2 = False

                def is_valid_path_block(block):
                    return block not in src.my_utils.BLOCK_TYPE.tile_sets[
                        src.my_utils.TYPE.WATER.value] and block not in \
                           src.my_utils.BLOCK_TYPE.tile_sets[src.my_utils.TYPE.LAVA.value] and block not in \
                           src.my_utils.BLOCK_TYPE.tile_sets[src.my_utils.TYPE.FOREIGN_BUILT.value]

                for p in points:
                    x = self.node_pointers[p][0]
                    z = self.node_pointers[p][1]
                    y = self.rel_ground_hm[x][z] - 1
                    b = self.blocks(x, y, z)
                    if not is_valid_path_block(b):
                        # get new path
                        if len(n2_options) < 1:
                            return False
                        n2 = n2_options.pop()
                        points = src.linedrawing.get_line((n1.center[0], n1.center[1]), (n2.center[0], n2.center[1]))
                        find_new_n2 = True
                        i += 1
                        break
            return points
        points = find_other_paths(self, n1, n2, n2_options, points, limit)
        if points == False:
            print(f"  Attempt {attempt}: could not find ending road options. Trying again~")
            self.water = old_water
            return False, [], [], None
        points = self.points_to_nodes(points)  # points is the path of nodes from the chosen
        if points == False:
            print(f"  Attempt {attempt}: road points didn't stay in bounds! Trying again~")
            self.water = old_water
            return False, [], [], None
        (x1, y1) = points[0]
        (x2, y2) = points[len(points) - 1]
        self.set_type_road(points,
                           src.my_utils.TYPE.MAJOR_ROAD.name)  # TODO check if the fact that this leads to repeats causes issue
        middle_nodes = []
        if len(points) > 2:
            middle_nodes = points[1:len(points) - 1]
        self.road_segs.add(
            src.road_segment.RoadSegment(self.nodes(x1, y1), self.nodes(x2, y2), middle_nodes, src.my_utils.TYPE.MAJOR_ROAD.name,
                        self.road_segs, self))
        status = self.init_construction(points)
        if status == False:
            print(f"  Attempt {attempt}: tried to build road outside of bounds! Trying again~")
            self.water = old_water
            return False, [], [], None
        p1 = (x1, y1)
        p2 = (x2, y2)
        # self.init_lots(*p1, *p2)  # main street is a lot
        if self.create_road(node_pos1=p1, node_pos2=p2, road_type=src.my_utils.TYPE.MAJOR_ROAD.name) == False:
            print(f"  Attempt {attempt}: Main street wasn't valid! Trying again~")
            self.water = old_water
            return False, [], [], None
        if self.sectors[x1, y1] != self.sectors[x2][y2]:
            p1 = p2  # make sure agents spawn in same sector
        # add starter agent 1
        head = choice(State.AGENT_HEADS)
        agent_a = src.agent.Agent(self, *p1, walkable_heightmap=self.rel_ground_hm,
                                  name=names.get_first_name(), parent_1=self.adam, parent_2=self.eve, head=head)
        self.add_agent(agent_a)
        agent_a.is_child_bearing = True
        # add starter agent 2
        head = choice(State.AGENT_HEADS)
        agent_b = src.agent.Agent(self, *p1, walkable_heightmap=self.rel_ground_hm,
                                  name=names.get_first_name(), parent_1=self.adam, parent_2=self.eve, head=head)
        self.add_agent(agent_b)
        agent_b.is_child_bearing = False
        # add child
        head = choice(State.AGENT_HEADS)
        child = src.agent.Agent(self, *p2, walkable_heightmap=self.rel_ground_hm,
                                name=names.get_first_name(), parent_1=agent_a, parent_2=agent_b, head=head)
        self.add_agent(child)
        agent_a.mutual_friends.add(child)
        agent_b.mutual_friends.add(child)
        child.mutual_friends.add(agent_a)
        child.mutual_friends.add(agent_b)
        # Set lovers
        agent_a.set_lover(agent_b)
        agent_b.set_lover(agent_a)
        return True, old_water, p1, agent_a

    def init_construction(self, points):
        """
        Initialize self.construction with given points
        :param points:
        :return:
        """
        for (x, y) in points:
            if self.out_of_bounds_Node(x, y):
                return False
            adjacent = self.nodes(x, y).range()  # this is where we increase building range
            adjacent = [s for n in adjacent for s in
                        n.adjacent()]  # every node in the road builds buildings around them
            for pt in adjacent:
                if pt not in points:
                    self.set_type_building([self.nodes(pt.center[0], pt.center[1])])
        return True

    def add_agent(self, agent):
        self.new_agents.add(agent)  # to be handled by update_agents
        ax = agent.x
        az = agent.z
        self.agent_nodes[self.node_pointers[(ax, az)]].add(agent)
        agent.set_motive(agent.Motive.LOGGING)

    def update_agents(self, is_rendering=True):
        """
        Update all agents 1 timeste.
        :param is_rendering:
        :return:
        """
        agents = self.agents.keys()
        self.num_agents = len(agents)
        for agent in agents:
            # Update resources
            agent.unshared_resources['rest'] += agent.rest_decay
            agent.unshared_resources['water'] += agent.water_decay
            agent.unshared_resources['happiness'] += agent.happiness_decay
            # Agents move forward
            agent.follow_path(state=self, walkable_heightmap=self.rel_ground_hm)
            agent.socialize(agent.found_and_moving_to_socialization)
            if is_rendering:
                agent.render()
        # Handle new agents
        new_agents = self.new_agents.copy()
        for new_agent in new_agents:  # because error occurs if dict changes during iteration
            self.agents[new_agent] = (new_agent.x, new_agent.y, new_agent.z)
            self.new_agents.remove(new_agent)

    def init_lots(self, x1, y1, x2, y2):
        (mx, my) = (int(x1 + x2) // 2, int(y1 + y2) // 2)  # middle
        self.add_lot([(mx - 25, my - 25), (mx + 25, my + 25)])

    def add_lot(self, points):
        lot = src.lot.Lot(self, points)
        if lot is not None:
            self.lots.add(lot)
            return True
        return False

    def points_to_nodes(self, points):
        nodes = []
        for point in points:
            if self.out_of_bounds_Node(point[0], point[1]):
                return False
            node = self.node_pointers[point]  # node coords
            if node not in nodes:
                nodes.append(node)
        return nodes

    def create_road(self, node_pos1, node_pos2, road_type, points=None, correction=5, inner_block_rate=1.0,
                    outer_block_rate=0.9, add_road_type=True, use_bend=False, cap_dist=30):
        """
        Create a new realistic road with constraints
        :param node_pos1:
        :param node_pos2:
        :param road_type:
        :param points:
        :param correction:
        :param inner_block_rate:
        :param outer_block_rate:
        :param add_road_type:
        :param use_bend:
        :param cap_dist:
        :return:
        """
        # Check road constraints
        if math.dist(node_pos1, node_pos2) > cap_dist:
            return False
        water_set = set(self.water)
        built_set = set(self.built)
        def is_valid(state, pos):
            """
            Check coordinate is valid for road
            :param state:
            :param pos:
            :return:
            """
            nonlocal water_set
            nonlocal tile_coords
            nonlocal built_set
            return pos not in tile_coords and pos not in water_set and pos not in state.foreign_built  # and pos not in built_set
        def is_walkable(state, path):
            """
            Check agent can walk across path
            :param state:
            :param path:
            :return:
            """
            last_y = state.rel_ground_hm[path[0][0]][path[0][1]]
            for i in range(1, len(path)):
                y = state.rel_ground_hm[path[i][0]][path[i][1]]
                dy = abs(last_y - y)
                if dy > state.AGENT_JUMP:
                    return False
                last_y = y
            return True
        if points == None:
            block_path = src.linedrawing.get_line(node_pos1, node_pos2)  # inclusive
        else:
            block_path = points
        if use_bend:
            found_road = False
            tile_coords = {tilepos for node in self.built for tilepos in node.get_tiles()}
            if any(not is_valid(self, tile) for tile in block_path) or not is_walkable(self, block_path):
                built_node_coords = [node.center for node in self.built]  # returns building node coords
                built_diags = [(node[0] + dir[0] * self.NODE_SIZE, node[1] + dir[1] * self.NODE_SIZE)
                               for node in built_node_coords for dir in src.movement_backup.diagonals if
                               is_valid(self, (node[0] + dir[0] * self.NODE_SIZE, node[1] + dir[1] * self.NODE_SIZE))]
                nearest_builts = src.movement_backup.find_nearest(self, *node_pos1, built_diags, 5, 30, 10)
                closed = set()
                found_bend = False
                for built in nearest_builts:
                    if found_bend == True: break
                    for diag in src.movement_backup.diagonals:
                        nx = self.NODE_SIZE * diag[0] + built[0]
                        nz = self.NODE_SIZE * diag[1] + built[1]
                        if (nx, nz) in closed: continue
                        closed.add((nx, nz))
                        if self.out_of_bounds_Node(nx, nz): continue
                        p1_to_diag = src.linedrawing.get_line(node_pos1,
                                                              (nx, nz))  # TODO add aux to p1 so it checks neigrboars
                        if any(not is_valid(self, tile) for tile in p1_to_diag) or not is_walkable(self,
                                                                                                   p1_to_diag): continue
                        closest_point, p2_to_diag = self.get_closest_point(node=self.nodes(nx, nz),
                                                                           lots=[],
                                                                           possible_targets=self.roads,
                                                                           road_type=road_type,
                                                                           state=self,
                                                                           leave_lot=False,
                                                                           correction=correction)
                        if p2_to_diag is None: continue  # if none found, try again
                        # if building is in path. try again
                        if any(not is_valid(self, tile) for tile in p2_to_diag) or not is_walkable(self, p2_to_diag):
                            dist = cap_dist  # CAPPED #int(len(p2_to_diag)/2)
                            steps = 60
                            step_amt = 360 / steps
                            status = False
                            raycast_path = None
                            for i in range(steps):
                                end_x = int(math.cos(math.radians(i * step_amt)) * dist) + nx  # nx and nz are the satrt
                                end_z = int(math.sin(math.radians(i * step_amt)) * dist) + nz
                                if self.out_of_bounds_Node(end_x, end_z): continue
                                status, raycast_path = self.nodes_raycast(start=(nx, nz), end=(end_x, end_z),
                                                                          target=self.roads,
                                                                          breaks_list=[])
                                if status is True: break
                            if status is False: continue
                            if any(not is_valid(self, tile) for tile in raycast_path) or not is_walkable(self,
                                                                                                         raycast_path): continue
                            p2_to_diag = raycast_path
                            found_road = True
                        else:
                            found_road = True
                        block_path = p1_to_diag + p2_to_diag  # concat two, building-free roads
                        found_bend = True
                        break
            else:
                found_road = True
            if not found_road:
                return False
        if not is_walkable(self, block_path):
            return False
        # Add road segnmets
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
            node_path.append(end)  # end
        check1 = check2 = True
        if check1:
            start = self.nodes(*node_pos1)
            for rs in self.road_segs:
                if node_pos1 in rs.nodes:  # if the road is in roads already, split it off
                    rs.split(start, self.road_segs, self.road_nodes, state=self)  # split RoadSegment
                    break
        if check2:
            end = self.nodes(*node_pos2)
            for rs in self.road_segs:
                if node_pos2 in rs.nodes:
                    rs.split(end, self.road_segs, self.road_nodes, state=self)
                    break
        if add_road_type == True:  # allows us to ignore the small paths from roads to buildings
            road_segment = src.road_segment.RoadSegment(self.nodes(*node_pos1), self.nodes(*node_pos2), middle_nodes, road_type,
                                       self.road_segs, state=self)
            self.road_segs.add(road_segment)

        # BUILD MAIN ROAD
        def set_blocks_for_path(self, path, rate):
            blocks_ordered = []
            blocks_set = set()
            static_temp = self.rel_ground_hm.copy()
            for x in range(len(static_temp)):
                for z in range(len(static_temp[0])):
                    static_y = self.static_ground_hm[x][z]
                    if static_temp[x][z] > static_y:
                        static_temp[x][z] = static_y
            length = len(path)
            up_slab_next = False
            up_stairs_next = False
            next_facing = False
            down_stairs_capping = False
            is_diagonal = False
            for i in range(length):
                x = path[i][0]
                z = path[i][1]
                y = int(static_temp[x][z]) - 1
                if self.blocks(x, y, z) == "minecraft:water":
                    continue
                if src.manipulation.is_log(self, x, y + 1, z):
                    src.manipulation.flood_kill_logs(self, x, y + 1, z)
                    if (x, z) in self.trees:  # When sniped new tree
                        self.trees.remove((x, z))
                if src.manipulation.is_sapling(self, x, y + 1, z):
                    set_state_block(self, x, y + 1, z, "minecraft:air")
                    if (x, z) in self.saplings:  # Hhen sniped by new sapling
                        self.saplings.remove((x, z))
                if random() < rate:
                    check_next_road = True
                    check_next_next_road = True
                    if i >= length - 2:
                        check_next_road = False
                        check_next_next_road = False
                    elif i >= length - 1:
                        check_next_road = False
                    next_road_y = 0
                    next_next_road_y = 0
                    if check_next_road:
                        next_road_y = static_temp[path[i + 1][0]][path[i + 1][1]] - 1
                    if check_next_next_road:
                        nnx = path[i + 2][0]
                        nnz = path[i + 2][1]
                        next_next_road_y = static_temp[nnx][nnz] - 1
                    ndy = next_road_y - y
                    nndy = next_next_road_y - next_road_y
                    px = x  # placement x
                    py = y
                    pz = z
                    if (px, pz) in self.road_blocks or (
                            py - 1 >= 0 and self.blocks(px, py - 1, pz) in src.my_utils.BLOCK_TYPE.tile_sets[
                        src.my_utils.TYPE.MAJOR_ROAD.value]): continue  # might not work well.
                    block_type = 0
                    facing_data = False
                    block = choice(self.road_set[0])
                    # TODO make sure these arent overriden
                    if up_slab_next or up_stairs_next:
                        if up_slab_next:
                            up_slab_next = False
                            block = choice(self.road_set[1])
                            block_type = 1
                        elif up_stairs_next:
                            if next_facing is not None:
                                facing_data = next_facing
                                block = choice(self.road_set[2]) + """[facing={facing}]""".format(facing=facing_data)
                                block_type = 2
                            else:
                                block = choice(self.road_set[0])
                                block_type = 1  # slab to make it smooth nonetheless
                                is_diagonal = True
                            up_stairs_next = False
                        if ndy > 0 and nndy == 0:  # Slab above
                            up_slab_next = True
                            pass
                        elif ndy > 0 and nndy > 0:  # Slope 1
                            dx = path[i + 2][0] - path[i + 1][0]
                            dz = path[i + 2][1] - path[i + 1][1]
                            next_facing = None
                            up_stairs_next = True
                            if dx > 0 and dz == 0:
                                next_facing = "east"
                            elif dx < 0 and dz == 0:
                                next_facing = "west"
                            elif dz > 0 and dx == 0:
                                next_facing = "south"
                            elif dz < 0 and dx == 0:
                                next_facing = "north"
                            else:
                                pass
                    else:
                        if check_next_next_road:
                            if ndy == 0:
                                pass
                            elif ndy > 0 and nndy == 0:  # slab above
                                up_slab_next = True
                                pass
                            elif ndy < 0 and nndy < 0:  # slope -1
                                dx = path[i + 1][0] - path[i][0]
                                dz = path[i + 1][1] - path[i][1]
                                facing = None
                                down_stairs_capping = True
                                if dx > 0 and dz == 0:
                                    facing = "west"
                                elif dx < 0 and dz == 0:
                                    facing = "east"
                                elif dz > 0 and dx == 0:
                                    facing = "north"
                                elif dz < 0 and dx == 0:
                                    facing = "south"
                                else:
                                    pass
                                if facing is not None:
                                    facing_data = facing
                                    block = choice(self.road_set[2]) + """[facing={facing}]""".format(
                                        facing=facing_data)
                                    block_type = 2
                                else:
                                    block = choice(self.road_set[0])
                                    block_type = 1
                                    is_diagonal = True
                            elif down_stairs_capping:  # slope -1
                                down_stairs_capping = False
                                dx = path[i + 1][0] - path[i][0]
                                dz = path[i + 1][1] - path[i][1]
                                facing = None
                                if dx > 0 and dz == 0:
                                    facing = "west"  # west = (1,0)
                                elif dx < 0 and dz == 0:
                                    facing = "east"  # east = (-1,0)
                                elif dz > 0 and dx == 0:
                                    facing = "north"
                                elif dz < 0 and dx == 0:
                                    facing = "south"
                                else:
                                    pass
                                if facing is not None:
                                    facing_data = facing
                                    block = choice(self.road_set[2]) + """[facing={facing}]""".format(
                                        facing=facing_data)
                                    block_type = 2
                                else:
                                    block = choice(self.road_set[0])
                                    block_type = 1
                                    is_diagonal = True
                            elif ndy < 0 and nndy == 0:  # slab below (in place)
                                block = choice(self.road_set[1])
                                block_type = 1
                            elif ndy > 0 and nndy > 0:  # slope 1
                                dx = path[i + 2][0] - path[i + 1][0]
                                dz = path[i + 2][1] - path[i + 1][1]
                                next_facing = None
                                up_stairs_next = True
                                if dx > 0 and dz == 0:
                                    next_facing = "east"
                                elif dx < 0 and dz == 0:
                                    next_facing = "west"
                                elif dz > 0 and dx == 0:
                                    next_facing = "south"
                                elif dz < 0 and dx == 0:
                                    next_facing = "north"
                                else:
                                    pass
                            elif ndy < 0 and nndy > 0:
                                pass
                            elif ndy > 0 and nndy < 0:
                                pass
                        elif check_next_road:
                            if ndy > 0:
                                px = path[i + 1][0]
                                pz = path[i + 1][1]
                                block = choice(self.road_set[1])
                                block_type = 1
                            elif ndy < 0:
                                block = choice(self.road_set[1])
                                block_type = 1
                    static_temp[px][pz] = py + 1
                    if not self.out_of_bounds_3D(px, py + 1, pz):
                        if 'snow' in self.blocks(px, py + 1, pz):
                            set_state_block(self, px, py + 1, pz, 'minecraft:air')
                    set_state_block(self, px, py, pz, block)
                    if src.manipulation.is_leaf(self.blocks(x, y + 2, z)):
                        src.manipulation.flood_kill_leaves(self, x, y + 2, z, 10)
                    is_slab_or_stairs = block_type > 0
                    blocks_set.add((px, pz, is_slab_or_stairs))
                    blocks_ordered.append((block_type, px, py, pz, facing_data, is_diagonal))
                    facing_data = False
                    is_diagonal = False
                    if block_type == 1:
                        self.road_blocks.add((px, pz))
            return blocks_ordered, blocks_set

        ## BUILD AUX ROADS
        def set_blocks_for_path_aux(self, rate, blocks_ordered, main_path_set):
            """
            Build auxillary road (i.e. expanding beyond a single-block width line
            :param self:
            :param rate:
            :param blocks_ordered:
            :param main_path_set:
            :return:
            """

            def set_scaffold_single(self, tx, build_y, tz):
                """
                Set scaffold for a simple block
                :param tx:
                :param build_y:
                :param tz:
                :return:
                """
                py = build_y - 1
                traverse = self.traverse_up(tx, tz, py - 1)
                block = self.blocks(tx, py, tz)
                if block in src.my_utils.BLOCK_TYPE.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value] or block in \
                        src.my_utils.ROAD_SETS['default_slabs']:
                    block = self.blocks(tx, self.static_ground_hm[tx][tz] - 1, tz)
                    fill = block
                    if len(traverse) > 0:
                        for y in traverse:
                            set_state_block(self, tx, y, tz, fill)
                    set_state_block(self, tx, py, tz, fill)
                return True

            def add_aux_block(self, x, y, z, offx, offz, type, facing, is_diagonal_stairs, dx, dz):
                """
                Place auxillary road block depending on context
                :param self:
                :param x:
                :param y:
                :param z:
                :param offx:
                :param offz:
                :param type:
                :param facing:
                :param is_diagonal_stairs:
                :param dx:
                :param dz:
                :return: [x,z]
                """
                nx = x + offx
                nz = z + offz
                if (nx, nz) in self.road_blocks or self.blocks(nx, y - 1, nz) in src.my_utils.BLOCK_TYPE.tile_sets[
                    src.my_utils.TYPE.MAJOR_ROAD.value]: return False  # might not work well.
                nonlocal main_path_set
                # Validation checks
                if src.manipulation.is_log(self, nx, y + 1, nz):
                    src.manipulation.flood_kill_logs(self, nx, y + 1, nz)
                    if (nx, nz) in self.trees:  # Sniped by new tree
                        self.trees.remove((nx, nz))
                if src.manipulation.is_sapling(self, nx, y + 1, nz):
                    set_state_block(self, nx, y + 1, nz, "minecraft:air")
                    if (nx, nz) in self.saplings:  # Sniped by new sapling
                        self.saplings.remove((nx, nz))
                # No repeats
                if (nx, nz, 1) not in main_path_set and random() < rate:  # Prioritize slabs
                    if self.blocks(nx, y + 1, nz) in src.my_utils.BLOCK_TYPE.tile_sets[
                        src.my_utils.TYPE.GREEN.value].union(
                        src.my_utils.BLOCK_TYPE.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value]) and \
                            self.node_pointers[(nx, nz)] is not None and self.nodes(*self.node_pointers[(nx, nz)]) not in self.built:
                        set_scaffold_single(self, nx, y, nz)
                        set_state_block(self, nx, y + 1, nz, "minecraft:air")
                    if (nx, nz) in self.exterior_heightmap:
                        set_scaffold_single(self, nx, y, nz)
                        set_state_block(self, nx, y, nz, choice(self.road_set[0]))
                    else:
                        if facing:
                            if (facing[0] in ['e', 'w'] and offx == 0) or (facing[0] in ['n', 's'] and offz == 0):
                                set_scaffold_single(self, nx, y, nz)
                                set_state_block(self, nx, y, nz,
                                                choice(self.road_set[type]) + """[facing={facing}]""".format(
                                                    facing=facing))
                        else:  # Correct
                            if dx is not None and (
                                    is_diagonal_stairs and dx == -offx or is_diagonal_stairs and dz == -offz):
                                type = 0
                            set_scaffold_single(self, nx, y, nz)
                            set_state_block(self, nx, y, nz, choice(self.road_set[type]))
                    is_slab_or_stairs = type > 0
                    main_path_set.add((x + offx, z + offz, is_slab_or_stairs))
                    if type == 1:
                        self.road_blocks.add((nx, nz))

            path_len = len(blocks_ordered)
            for i in range(path_len):
                type, x, y, z, facing, is_diagonal = blocks_ordered[i]
                dx = dz = None
                if i + 1 < path_len:
                    ntype, nx, ny, nz, nfacing, nis_diagonal = blocks_ordered[i + 1]
                    dx = nx - x
                    dz = nz - z
                add_aux_block(self, x, y, z, 1, 0, type, facing, is_diagonal, dx, dz)
                add_aux_block(self, x, y, z, -1, 0, type, facing, is_diagonal, dx, dz)
                add_aux_block(self, x, y, z, 0, 1, type, facing, is_diagonal, dx, dz)
                add_aux_block(self, x, y, z, 0, -1, type, facing, is_diagonal, dx, dz)

        blocks_ordered, blocks_set = set_blocks_for_path(self, block_path, inner_block_rate)
        for card in src.movement_backup.cardinals:
            aux_path = []
            for block in block_path:
                # Clamp
                x = max(min(block[0] + card[0], self.last_node_pointer_x), 0)
                z = max(min(block[1] + card[1], self.last_node_pointer_z), 0)
                if abs(self.rel_ground_hm[x][z] - self.rel_ground_hm[block[0]][block[1]]) > 1: continue
                if (x, z) not in blocks_set:  # to avoid overlapping road blocks
                    aux_path.append((x, z))
        set_blocks_for_path_aux(self, outer_block_rate, blocks_ordered, blocks_set)
        self.road_nodes.append(self.nodes(*self.node_pointers[node_pos1]))  # should these even go here first?
        self.road_nodes.append(self.nodes(*self.node_pointers[node_pos2]))
        if add_road_type:
            self.set_type_road(node_path, road_type)
        return [node_pos1, node_pos2]

    def nodes_raycast(self, start, end, target, breaks_list):
        """
        Raycast from start node to end node, return either
        (True, path) if valid
        (False, None) if invalid
        :param start:
        :param end:
        :param target:
        :param breaks_list:
        :return:
        """
        max_path = src.linedrawing.get_line(start, end)
        result_path = []
        for tile in max_path:
            node_ptr = self.node_pointers[(tile)]
            if node_ptr is None: continue
            node = self.nodes(*node_ptr)
            for _break in breaks_list:
                if node in _break: return False, None
            if node in target:
                result_path.append(tile)
                return True, result_path
            result_path.append(tile)
        return False, None

    def append_road(self, point, road_type, correction=5, bend_if_needed=False):
        """
        Build road from point that connects to already-created roads
        :param point:
        :param road_type:
        :param correction:
        :param bend_if_needed:
        :return:
        """
        point = self.node_pointers[point]
        node = self.nodes(*point)
        if point is None or node is None:
            print("tried to build road outside of Node bounds!")
            return False
        closest_point, path_points = self.get_closest_point(node=self.nodes(*self.node_pointers[point]),
                                                            # get closest point to any road
                                                            lots=[],
                                                            possible_targets=self.roads,
                                                            road_type=road_type,
                                                            state=self,
                                                            leave_lot=False,
                                                            correction=correction)
        if closest_point == None:
            return False
        (x2, y2) = closest_point
        closest_point = self.get_point_to_close_gap_minor(*point,
                                                          path_points)  # connects 2nd end of minor roads to the nearest major or minor road. I think it's a single point
        if closest_point is not None:
            point = closest_point
            path_points.extend(src.linedrawing.get_line((x2, y2),
                                                        point))  # append to the points list the same thing in reverse? or is this a diff line?
        status = self.create_road(point, (x2, y2), road_type=road_type, points=path_points,
                                  use_bend=bend_if_needed)  # , only_place_if_walkable=only_place_if_walkable, dont_rebuild)
        if status == False:
            return False
        return True

    def get_point_to_close_gap_minor(self, x1, z1, points):
        (x_, z_) = points[1]
        x = x1 - x_
        z = z1 - z_
        (x2, z2) = (x1 + x, z1 + z)
        while True:
            if x2 >= self.last_node_pointer_x or z2 >= self.last_node_pointer_z or x2 < 0 or z2 < 0:
                break
            landtype = self.nodes(*self.node_pointers[(x2, z2)]).get_type()
            if src.my_utils.TYPE.GREEN.name in landtype or src.my_utils.TYPE.TREE.name in landtype or src.my_utils.TYPE.WATER.name in landtype:
                break
            if src.my_utils.TYPE.MAJOR_ROAD.name in landtype or src.my_utils.TYPE.MINOR_ROAD.name in landtype:  # and src.my_utils.TYPE.BYPASS.name not in landtype:
                return (x2, z2)
            (x2, z2) = (x2 + x, z2 + z)
        return None

    def get_point_to_close_gap_major(self, node, x1, z1, points):
        if node.lot is None:
            return None
        (x_, z_) = points[1]
        x = x1 - x_
        z = z1 - z_
        (x2, z2) = (x1 + x, z1 + z)
        border = node.lot.border
        while True:
            if x2 >= self.last_node_pointer_x or z2 >= self.last_node_pointer_z or x2 < 0 or z2 < 0:
                break
            landtype = self.nodes(*self.node_pointers[(x2, z2)]).get_type()
            if src.my_utils.TYPE.WATER.name in landtype:
                break
            if (x2, z2) in border:
                return (x2, z2)
            (x2, z2) = (x2 + x, z2 + z)
        return None

    def get_closest_point(self, node, lots, possible_targets, road_type, state, leave_lot, correction=5):
        x, z = node.center
        nodes = possible_targets
        dists = [math.hypot(n.center[0] - x, n.center[1] - z) for n in nodes]
        node2 = nodes[dists.index(min(dists))]
        (x2, z2) = (node2.center[0], node2.center[1])
        xthr = zthr = 2  # TODO tweak these
        if node.lot is None:
            if True:
                if node2.lot is not None:
                    x = max(min(x, self.last_node_pointer_x), 0)
                    z = max(min(z, self.last_node_pointer_z), 0)
                if abs(x2 - x) > xthr and abs(z2 - z) > zthr:
                    if not state.add_lot([(x2, z2), (x, z)]):
                        print("leave_lot = {} add lot failed".format(leave_lot))
                        return None, None
        points = src.linedrawing.get_line((x, z), (node2.center[0], node2.center[1]))
        if len(points) <= 2:
            return None, None
        if not leave_lot:
            for (i, j) in points:
                if src.my_utils.TYPE.WATER.name in self.nodes(*self.node_pointers[(i, j)]).mask_type:
                    return None, None
        closest_point = (node2.center[0], node2.center[1])
        return closest_point, points

    def apply_local_prosperity(self, x, z, value):
        self.prosperity[x][z] += value

def set_state_block(state, x, y, z, block_name):
    """
    Store the block_name at position (x,y,z) to be updated/rendered at the next timestep in given state.
    :param state:
    :param x:
    :param y:
    :param z:
    :param block_name:
    :return:
    """
    if state.out_of_bounds_Node(x, z) or y >= state.len_y: return False
    state.traverse_from[x][z] = max(y, state.traverse_from[x][z])
    state.traverse_update_flags[x][z] = True
    state.hm_update_flags.add((x, z))
    state.blocks_arr[x][y][z] = block_name
    state.changed_blocks_xz.add((x, z))
    state.total_changed_blocks_xz.add((x, z))
    state.changed_blocks[(x, y, z)] = block_name
    state.total_changed_blocks[(x, y, z)] = block_name
    return True

