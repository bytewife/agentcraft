#! /usr/bin/python3
"""### State data
Contains tools for modifying the state of the blocks in an area given by Simulation.
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"


import math
from math import floor

import http_framework.interfaceUtils
import http_framework.worldLoader
import src.my_utils
import src.movement
import src.pathfinding
import src.scheme_utils
import src.agent
import math
import numpy as np
from random import choice, random, randint
from scipy.interpolate import interp1d
import src.linedrawing
import src.manipulation
import names
import src.chronicle

class State:

    agent_heads = []
    tallest_building_height = 30

    unwalkable_blocks = ['minecraft:water', 'minecraft:lava']
    agent_height = 2
    agent_jump_ability = 1
    heightmap_offset = -1
    node_size = 3
    MAX_SECTOR_PROPAGATION_DEPTH = 150

    ## Create surface grid
    def __init__(self, rect, world_slice, precomp_legal_actions=None, blocks_file=None, precomp_pathfinder=None, precomp_sectors=None, precomp_types=None, precomp_nodes=None, precomp_node_pointers=None,max_y_offset=tallest_building_height, water_with_adjacent_land=None):
        if world_slice:
            self.rect = rect
            self.world_slice = world_slice

            self.world_y = 0
            self.world_x = 0
            self.world_z = 0
            self.len_x = 0
            self.len_y = 0
            self.len_z = 0
            self.blocks_arr = []  # 3D Array of all the assets in the state
            self.trees = []
            self.saplings = []
            self.water = []  # tile positions
            self.lava = set()  # tile positions
            self.road_nodes = []
            self.roads = []
            self.road_tiles = set()
            self.road_segs = set()
            self.construction = set()  # nodes where buildings can be placed
            self.lots = set()
            self.world_x = self.rect[0]
            self.world_z = self.rect[1]
            self.len_x = self.rect[2] - self.rect[0]
            self.len_z = self.rect[3] - self.rect[1]
            self.end_x = self.rect[2]
            self.end_z = self.rect[3]
            self.tiles_with_land_neighbors = set()

            self.interface, self.blocks_arr, self.world_y, self.len_y, self.abs_ground_hm = self.gen_blocks_array(world_slice)

            self.rel_ground_hm = self.gen_rel_ground_hm(self.abs_ground_hm)  # a heightmap based on the state's y values. -1
            self.static_ground_hm = self.gen_static_ground_hm(self.rel_ground_hm)  # use this for placing roads
            self.heightmaps = world_slice.heightmaps
            self.built = set()
            self.foreign_built = set()
            self.road_set = choice(src.my_utils.set_choices)
            self.generated_a_road = False  # prevents buildings blocking in the roads

            if precomp_nodes is None or precomp_node_pointers is None:
                self.nodes_dict, self.node_pointers = self.gen_nodes(self.len_x, self.len_z, self.node_size)
            else:
                self.nodes_dict = precomp_nodes
                self.node_pointers = precomp_node_pointers
                nodes_in_x = int(self.len_x / self.node_size)
                nodes_in_z = int(self.len_z / self.node_size)
                self.last_node_pointer_x = nodes_in_x * self.node_size - 1  # TODO verify the -1
                self.last_node_pointer_z = nodes_in_z * self.node_size - 1

            if precomp_types == None:
                self.types = self.gen_types(self.rel_ground_hm)  # 2D array. Exclude leaves because it would be hard to determine tree positions
            else:
                self.types = precomp_types


            if precomp_legal_actions is None:
                self.legal_actions = src.movement.gen_all_legal_actions(self,
                    self.blocks_arr, vertical_ability=self.agent_jump_ability, heightmap=self.rel_ground_hm,
                    actor_height=self.agent_height, unwalkable_blocks=["minecraft:water", 'minecraft:lava']
                )
            else:
                self.legal_actions = precomp_legal_actions

            if precomp_pathfinder is None:
                self.pathfinder = src.pathfinding.Pathfinding(self)
            else:
                self.pathfinder = precomp_pathfinder

            if precomp_sectors is None:
                self.sectors = self.pathfinder.create_sectors(self.heightmaps["MOTION_BLOCKING_NO_LEAVES"],
                                                self.legal_actions)  # add tihs into State
            else:
                self.sectors = precomp_sectors


            self.prosperity = np.zeros((self.len_x, self.len_z))
            self.traffic = np.zeros((self.len_x, self.len_z))
            self.updateFlags = np.zeros((self.len_x, self.len_z))
            self.built_heightmap = {}
            self.exterior_heightmap = {}
            self.generated_building = False
            self.changed_blocks = {}
            self.changed_blocks_xz = set()
            self.total_changed_blocks = {}
            self.total_changed_blocks_xz = set()
            self.phase = 1
            self.bends = 0
            self.semibends = 0
            self.bendcount = 0
            self.agents = dict()  # holds agent and position
            self.agents_in_nodes = self.init_agents_in_nodes()
            self.new_agents = set()  # agents that were just created
            self.max_agents = 20
            self.build_minimum_phase_1 = max(*[building_pair[1] for building_pair in src.my_utils.STRUCTURES['small']])
            self.build_minimum_phase_2 = max(*[building_pair[1] for building_pair in src.my_utils.STRUCTURES['med']])
            self.build_minimum_phase_3 = max(*[building_pair[1] for building_pair in src.my_utils.STRUCTURES['large']])
            # TODO parametrize these
            self.phase2threshold = 200
            self.phase3threshold = 500
            self.traverse_from = np.copy(self.rel_ground_hm)
            # self.traverse_update_flags = np.zeros(len(self.rel_ground_hm), len(self.rel_ground_hm[0])))
            self.traverse_update_flags = np.full((len(self.rel_ground_hm), len(self.rel_ground_hm[0])), False, dtype=bool)
            self.heightmap_tiles_to_update = set()
            self.dont_update_again = set()
            self.water_with_adjacent_land = list(set(self.water).intersection(self.tiles_with_land_neighbors))
            self.flag_color = choice(src.my_utils.colors)
            self.step_number = 0
            self.last_platform_extension = "minecraft:dirt"

            self.adam = src.agent.Agent(self,0,0, self.rel_ground_hm, "Adam, the Original", "")
            self.eve = src.agent.Agent(self, 0, 0, self.rel_ground_hm, "Eve, the Original", "")

            # print(self.types)
            # print(self.nodes[self.node_pointers[(5,5)]].get_type())
            # print('nodes is '+str(len(self.nodes)))
            # print('traffic is '+str(len(self.traffic)))

            for water in self.water:
                # src.states.set_state_block(self, water[0], self.rel_ground_hm[water[0]][water[1]], water[1], 'minecraft:iron_block')
                pass


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
            self.len_x, self.len_y, self.len_z, self.blocks_arr = parse_blocks_file(blocks_file)

    def reset_for_restart(self, use_heavy=True):
        self.built.clear()
        self.roads.clear()
        self.agents.clear()
        self.new_agents.clear()
        self.construction.clear()
        self.road_nodes = []
        self.road_segs.clear()
        self.nodes_dict = {}
        self.nodes_dict, self.node_pointers = self.gen_nodes(self.len_x, self.len_z, self.node_size)
        self.agents_in_nodes.clear()
        for pos in self.changed_blocks.keys():
            x,y,z = pos
            self.blocks_arr[x][y][z] = 0
        self.changed_blocks.clear()
        self.total_changed_blocks = {}
        self.total_changed_blocks_xz.clear()
        self.changed_blocks_xz.clear()
        src.chronicle.chronicles = src.chronicle.chronicles_empty.copy()
        if use_heavy:
            self.agents_in_nodes = self.init_agents_in_nodes()

    def blocks(self, x, y, z):
        if self.blocks_arr[x][y][z] == 0:
            self.blocks_arr[x][y][z] = self.world_slice.getBlockAt(self.world_x+x, self.world_y+y, self.world_z+z)#, self.world_x, self.world_y, self.world_z)
        return self.blocks_arr[x][y][z]


    def gen_static_ground_hm(self, a):
        hm = np.copy(a)
        for x in range(len(a)):
            for z in range(len(a[0])):
                y = a[x][z] - 1
                while y > 0 and (src.manipulation.is_log(self,x,y,z) or self.blocks(x,y,z) in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value]):
                    y-=1
                hm[x][z] = y+1
        return hm

    def init_agents_in_nodes(self):
        result = dict()
        for x in range(int(self.len_x / self.node_size)):
            for z in range(int(self.len_z / self.node_size)):
                cx = x*3+1
                cz = z*3+1
                result[(cx,cz)] = set()
        return result

    def find_build_location(self, agentx, agentz, building_file, wood_type, ignore_sector=False, max_y_diff=4, build_tries=25):
        f = open(building_file, "r")
        size = f.readline()
        f.close()
        x_size, y_size, z_size = [int(n) for n in size.split(' ')]
        i = 0
        # build_tries = 25
        while i < build_tries:
            construction_site = choice(list(self.construction))
            result = self.check_build_spot(construction_site, building_file, x_size, z_size, wood_type, max_y_diff=max_y_diff)
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
                    if self.sectors[agentx][agentz] == self.sectors[nx][nz] or ignore_sector:  # this seems wrong
                        assert type(result[2]) == set
                        for node in result[2].union({result[1]}):  # this is equal to
                            # src.states.set_state_block(self.state, node.center[0], self.state.rel_ground_hm[node.center[0]][node.center[1]]+10, node.center[1], 'minecraft:gold_block')
                            self.built.add(
                                node)  # add to built in order to avoid roads being placed before buildings placed
                            pass
                        return result
            i += 1
        return False


    def check_build_spot(self, ctrn_node, bld, bld_lenx, bld_lenz, wood_type, max_y_diff):
        # check if theres adequate space by getting nodes, and move the building to center it if theres extra space
        # if not ctrn_node in self.construction: return
        # for every orientation of this node+neighbors whose lenx and lenz are the min space required to place building at
        min_nodes_in_x = math.ceil(bld_lenx / ctrn_node.size)
        min_nodes_in_z = math.ceil(bld_lenz / ctrn_node.size)
        min_tiles = min_nodes_in_x * min_nodes_in_z
        found_ctrn_dir = None
        found_nodes = set()
        # get rotation based on neighboring road
        found_road = None
        face_dir = None
        for dir in src.movement.cardinals:  # maybe make this cardinal only
            nx = ctrn_node.center[0] + dir[0] * ctrn_node.size
            nz = ctrn_node.center[1] + dir[1] * ctrn_node.size
            if self.out_of_bounds_Node(nx, nz): continue
            np = (nx, nz)
            neighbor = self.nodes(*self.node_pointers[np])
            if neighbor in self.roads:
                found_road = neighbor
                face_dir = dir
            if neighbor in self.built:
                return None  # don't put buildings right next to each other
        if found_road == None:
            return None
        rot = 0
        if face_dir[0] == 1: rot = 2
        if face_dir[0] == -1: rot = 0
        if face_dir[1] == -1: rot = 1
        if face_dir[1] == 1: rot = 3
        # self.set_block(ctrn_node.center[0], 17, ctrn_node.center[1],"minecraft:emerald_block")
        if rot in [1, 3]:
            temp = min_nodes_in_x
            min_nodes_in_x = min_nodes_in_z
            min_nodes_in_z = temp
        ## find site where x and z are reversed. this rotates
        highest_y = self.rel_ground_hm[ctrn_node.center[0]][ctrn_node.center[1]]
        lowest_y = self.rel_ground_hm[ctrn_node.center[0]][ctrn_node.center[1]]
        for dir in src.movement.diagonals:
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
                    if ny > highest_y: highest_y = ny
                    elif ny < lowest_y: lowest_y = ny
                    node = self.nodes(nx, nz)
                    if not node in self.construction:
                        is_valid = False
                        break
                    if node in self.roads:
                        is_valid = False
                        break
                    if node in self.built:
                        is_valid = False
                        break
                    if node.center in self.foreign_built:
                        is_valid = False
                        break
                    obstacle_found = False
                    for tile in node.get_tiles():
                        # src.states.set_state_block(self.state, tile[0], self.state.rel_ground_hm[tile[0]][tile[1]] + 3, tile[1], 'minecraft:netherite')
                        if tile in self.water or tile in self.lava:
                            obstacle_found = True
                            break
                    if obstacle_found == True:
                        is_valid = False
                        break
                    tiles += 1
                    found_nodes.add(node)
                if is_valid == False:
                    break
            if tiles == min_tiles:  # found a spot!
                found_ctrn_dir = dir
                break
            else:
                found_nodes.clear()

        max_y_diff = max_y_diff  # was 4, but increased to 5 bc placing the initial building took too long
        for tile in found_road.get_tiles():
            ny = self.rel_ground_hm[tile[0]][tile[1]]
            if ny > highest_y: highest_y = ny
            elif ny < lowest_y: lowest_y = ny
        if found_ctrn_dir == None or highest_y - lowest_y > max_y_diff:  # if there's not enough space, return
            return None

        ctrn_dir = found_ctrn_dir
        return (
        found_road, ctrn_node, found_nodes, ctrn_dir, bld, rot, min_nodes_in_x, min_nodes_in_z, self.built,
        wood_type)


    def get_highest_height_in_node(self, node, hm):
        i = 0
        highest_tile = 0
        for tile in node.get_tiles():
            x = tile[0]
            z = tile[1]
            y = hm[x][z]
            if y > highest_tile:
                highest_tile = y
            i+=1
        return highest_tile


    def add_prosperity_from_tile(self, x, z, amt):
        # defer to the housing Node's prosperity
        node_loc = self.node_pointers[(x,z)]
        if node_loc is None: return
        self.nodes(x,z).add_prosperity_to_node(amt)

    def traverse_up(self, x, z, max_y):
        start_y = self.rel_ground_hm[x][z]
        result = []
        for y in range(start_y, max_y+1):
            # TODO do air check here
            result.append(y)
        return result

    def place_platform(self, found_road=None, ctrn_node=None, found_nodes_iter=None, ctrn_dir=None, bld=None, rot=None, min_nodes_in_x=None, min_nodes_in_z=None, built_arr=None, wood_type="oak", build_y=None, use_scaffolding=True):
        # py = self.static_ground_hm[found_road.center[0]][found_road.center[1]] - 1
        # py = self.get_highest_height_in_node(found_road,self.static_ground_hm) - 1
        found_nodes = list(found_nodes_iter)
        fill = "minecraft:scaffolding"
        py = build_y - 1
        for node in found_nodes:
            for tile in node.get_tiles():
                tx = tile[0]
                tz = tile[1]
                traverse = self.traverse_up(tx, tz, py-1)
                block = self.blocks(tx,py,tz)

                if block in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value]:
                    # block = self.blocks[tx][self.static_ground_hm[tx][tz]-1][tz]
                    # print("block is "+str(block))
                    block = self.blocks(tx,self.static_ground_hm[tx][tz] - 1,tz)
                    if block in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.MAJOR_ROAD.value]:
                        block = "minecraft:dirt"
                        set_state_block(self, tx, self.static_ground_hm[tx][tz] - 1, tz, block)
                    if not use_scaffolding:
                        fill = block
                    if len(traverse) > 1:
                        for y in traverse:
                            set_state_block(self, tx, y, tz, fill)
                        block = wood_type + '_planks'
                    elif len(traverse) == 1:
                        set_state_block(self, tx, py-1, tz, block)
                        # block = self.last + '_planks'
                    set_state_block(self,tx, py, tz, block)
        return True

    def place_scaffold_block(self, tx, build_y, tz):
        # py = self.static_ground_hm[found_road.center[0]][found_road.center[1]] - 1
        # py = self.get_highest_height_in_node(found_road,self.static_ground_hm) - 1
        # fill = "minecraft:scaffolding"
        py = build_y - 1
        traverse = self.traverse_up(tx, tz, py-1)
        block = self.blocks(tx,py,tz)
        if block in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value] or block in src.my_utils.ROAD_SETS['default_slabs']:
            # block = self.blocks[tx][self.static_ground_hm[tx][tz]-1][tz]
            # print("block is "+str(block))
            block = self.blocks(tx,self.static_ground_hm[tx][tz] - 1,tz)
            fill = block
            # fill = "minecraft:diamond_block"
            if len(traverse) > 0:
                for y in traverse:
                    set_state_block(self, tx, y, tz, fill)
                # block = wood_type + '_planks'
                # block = self.last + '_planks'
            set_state_block(self,tx, py, tz, fill)
        return True

    def place_schematic(self,found_road, ctrn_node, found_nodes, ctrn_dir, bld, rot, min_nodes_in_x, min_nodes_in_z, built_arr, wood_type, ignore_road=False):
        x1 = ctrn_node.center[0] - ctrn_dir[0]  # to uncenter
        z1 = ctrn_node.center[1] - ctrn_dir[1]
        x2 = ctrn_node.center[0] + ctrn_dir[0] + ctrn_dir[0] * ctrn_node.size * (min_nodes_in_x - 1)
        z2 = ctrn_node.center[1] + ctrn_dir[1] + ctrn_dir[1] * ctrn_node.size * (min_nodes_in_z - 1)
        xf = min(x1, x2)  # since the building is placed is ascending
        zf = min(z1, z2)
        # find lowest y
        # lowest_y = self.rel_ground_hm[ctrn_node.center[0]][ctrn_node.center[1]]
        # lowest_y = self.static_ground_hm[found_road.center[0]][found_road.center[1]]
        lowest_y = self.get_highest_height_in_node(found_road, self.static_ground_hm)
        radius = math.ceil(ctrn_node.size / 2)
        for node in found_nodes.union({ctrn_node}):
            for x in range(-radius, radius + 1):
                for z in range(-radius, radius + 1):
                    nx = node.center[0] + x
                    nz = node.center[1] + z
                    if self.out_of_bounds_Node(nx, nz): continue
                    by = self.rel_ground_hm[nx][nz]
                    if by < lowest_y:
                        pass
                        # lowest_y = by
        y = lowest_y  # This should be the lowest y in the
        # base_y = lowest_y + 1
        base_y = lowest_y

        ### Front
        front_length = min_nodes_in_x
        use_x = False
        if rot == 1 or rot == 3:
            use_x = True
        if use_x:
            offset = 1 if ctrn_node.center[1] > found_road.center[1] else -1
        else:
            offset = 1 if ctrn_node.center[0] > found_road.center[0] else -1
        front_tiles = []
        front_nodes = []
        highest_y = self.static_ground_hm[ctrn_node.center[0]][ctrn_node.center[1]] # for checking if the diff is too large, and putting it at top if it is
        lowest_y = highest_y
        y_sum = 0
        for i in range(front_length-1, -1, -1):
            front_length = min_nodes_in_z
            nx, nz = ctrn_node.center
            nx += (use_x ^ 1) * self.node_size * (rot - 1)
            nz += (use_x ^ 0) * self.node_size * (rot - 2)
            nx += i * self.node_size * (use_x ^ 0) * ctrn_dir[0]
            nz += i * self.node_size * (use_x ^ 1) * ctrn_dir[1]
            for r in range(-1, 2):
                # set_state_block(self, nx + r * (use_x ^ 0) + (use_x ^ 1) * offset, 20, nz + r * (use_x ^ 1) + (use_x ^ 0) * offset, "minecraft:gold_block")
                fx = nx + r * (use_x ^ 0) + (use_x ^ 1) * offset
                fz = nz + r * (use_x ^ 1) + (use_x ^ 0) * offset
                front_tiles.append((fx, fz))
                if self.out_of_bounds_Node(fx, fz):  # TODO: get rid of this and let prior fnuctions deal with it- prolly causes a bug
                    return False, None
                fy = self.static_ground_hm[fx,fz]
                if highest_y < fy:
                    highest_y = fy
                elif lowest_y > fy:
                    lowest_y = fy
                y_sum+=fy
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
        # mean_y = round(sum([self.static_ground_hm[t[0],t[1]] for t in front_tiles]) / len(front_tiles))

        status, building_heightmap, exterior_heightmap = src.scheme_utils.place_schematic_in_state(self, bld, xf,
                                                                                                   mean_y, zf,
                                                                                                   rot=rot,
                                                                                                   built_arr=self.built,
                                                                                                   wood_type=wood_type)
        if status == False:
            for node in found_nodes.union({ctrn_node}):
                self.built.remove(node)  # since this was set early in check_build_spot, remove it
            return False, None

        # src.states.set_state_block(self,found_road.center[0], 20, found_road.center[1], "minecraft:diamond_block")
        self.place_platform(found_road, ctrn_node, found_nodes, ctrn_dir, bld, rot, min_nodes_in_x, min_nodes_in_z, built_arr, wood_type, mean_y)

        built_list = list(building_heightmap.keys())
        ext_list = list(exterior_heightmap.keys())
        for tile in built_list+ext_list:  # let's see if this stops tiles from being placed in buildings, where there used to be ground
            self.update_heightmaps_for_block(tile[0], tile[1])

        self.built_heightmap.update(building_heightmap)
        self.exterior_heightmap.update(exterior_heightmap)
        # build road from the road to the building
        self.create_road(found_road.center, ctrn_node.center, road_type="None", points=None, leave_lot=False,
                               add_as_road_type=True, only_place_if_walkable=True, )
                                # add_as_road_type = False, only_place_if_walkable = True, )
        xmid = int((x2 + x1) / 2)
        zmid = int((z2 + z1) / 2)
        distmax = math.dist((ctrn_node.center[0] - ctrn_dir[0], ctrn_node.center[1] - ctrn_dir[1]), (xmid, zmid))
        # build construction site ground - foundation
        for n in found_nodes:
            # for each of the nodes' tiles, generate random, based on dist. Also, add it to built.
            for dir in src.movement.idirections:
                x = n.center[0] + dir[0]
                z = n.center[1] + dir[1]
                # add to built
                y = int(self.static_ground_hm[x][z]) - 1
                inv_chance = math.dist((x, z), (xmid, zmid)) / distmax  # clamp to 0-1
                if inv_chance == 1.0:  # stylistic choice: don't let corners be placed
                    continue
                attenuate = 0.8
                if random() > inv_chance * attenuate and y < base_y:
                    block = choice(src.my_utils.ROAD_SETS['default'])
                    # src.states.set_state_block(self, x, y, z, block)
        y = self.rel_ground_hm[xf][zf] + 5
        # extend road to fill building front

        for n in front_nodes:
            self.append_road(n.center, src.my_utils.TYPE.MINOR_ROAD.name, dont_rebuild=False)
            # if n not in self.roads:
            #     self.append_road(n.center, src.my_utils.TYPE.MINOR_ROAD.name)

        # debug
        # for n in found_nodes:
        #     x = n.center[0]
        #     z = n.center[1]
        #     y = self.state.rel_ground_hm[x][z] + 20
        #     src.states.set_state_block(self.state, x, y, z, "minecraft:iron_block")
        ## remove nodes from construction
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


    def get_nearest_tree(self,x,z, iterations=5):
        return src.movement.find_nearest(self, x,z,self.trees, 10, iterations, 15)


    # note: not every block has a node. These will point to None
    def gen_nodes(self, len_x, len_z, node_size):
        if len_x < 0 or len_z < 0:
            print("Lengths cannot be <0")
        node_size = 3  # in assets
        nodes_in_x = int(len_x / node_size)
        nodes_in_z = int(len_z / node_size)
        node_count = nodes_in_x * nodes_in_z
        self.last_node_pointer_x = nodes_in_x * node_size - 1  # TODO verify the -1
        self.last_node_pointer_z = nodes_in_z * node_size - 1
        nodes = {}  # contains coord pointing to data struct
        node_pointers = np.full((len_x,len_z), None)
        for x in range(nodes_in_x):
            for z in range(nodes_in_z):
                cx = x*node_size+1
                cz = z*node_size+1
                # node = self.Node(self, center=(cx, cz), types=[src.my_utils.TYPE.BROWN.name], size=self.node_size)  # TODO change type
                # nodes[(cx, cz)] = node
                node_pointers[cx][cz] = (cx, cz)  # TODO can lazy load this rather than gen here
                for dir in src.movement.directions:
                    nx = cx + dir[0]
                    nz = cz + dir[1]
                    node_pointers[nx][nz] = (cx, cz)
        # for node in nodes.values():  # TODO lazy load this too
            # node.adjacent = node.gen_adjacent(nodes, node_pointers, self)
            # node.neighbors = node.gen_neighbors(nodes, node_pointers, self)
            # # node = node.gen_local()
            # node.local = node.gen_local(nodes, node_pointers, self)
            # node.range, node.water_resources, node.resource_neighbors = node.gen_range(nodes, node_pointers, self)
        return nodes, node_pointers

    def get_node_center(self, tx, tz):
        xrem = tx % 3
        zrem = tz % 3
        dx = 1 - xrem
        dz = 1 - zrem
        return tx+dx,tz+dz

    # given pos of node
    def nodes(self,x,z):
        if (x,z) not in self.nodes_dict.keys():
            # get center from pos
            node = self.Node(self, center=(x, z), types=[src.my_utils.TYPE.BROWN.name], size=self.node_size)
            # this order is important to retain
            node.adjacent_centers = node.gen_adjacent_centers(self)
            node.neighbors_centers = node.gen_neighbors_centers(self)
            node.local_centers = node.gen_local_centers(self)
            node.range_centers = node.gen_range_centers(self)
            self.nodes_dict[(x,z)] = node
        return self.nodes_dict[(x,z)]


    class Node:

        ACTION_COSTS = {
            # src.my_utils.TYPE.MINOR_ROAD.name: 50,
            # src.my_utils.TYPE.MAJOR_ROAD.name: 50,
            # src.my_utils.TYPE.BUILT.name: 50,
        }
        locality_radius = 3
        range_radius = 4
        neighborhood_radius = 1
        adjacent_radius = 1

        # local = set()
        def __init__(self, state, center, types, size):
            self.center = center
            self.size = size
            # self.local_prosperity = 0  # sum of all of its assets
            self.mask_type = set()
            self.mask_type.update(types)
            self.lot = None
            self.state = state
            self.action_cost = 100
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
            # self.type = set()  # to cache type()

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
                    # node = self.state.nodes(*state.node_pointers[(x, z)])
                    if node.type == None:
                        node.get_type()
                    if "WATER" in node.type:
                        continue
                    # if "TREE" in node.type \
                    #         or "GREEN" in node.type \
                    #         or "CONSTRUCTION" in node.type:
                    #         self.resource_neighbors.append(node)
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
                    # node = self.state.nodes(*self.state.node_pointers[(x, z)])
                    if src.my_utils.TYPE.WATER.name in node.get_type():
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
                    tiles.append((nx,nz))
            return tiles


        def get_tiles(self):
            return self.tiles


        # the tiles' types + mask_type (like building or roads
        def get_type(self):
            if self in self.state.built:
                self.add_mask_type(src.my_utils.TYPE.BUILT.name)
            self.type = set()
            for tile_pos in self.get_tiles():
                # tx, tz = tile_pos
                # if self.state.out_of_bounds_Node(tx, tz): continue
                # print(tile_pos)
                self.type.add(self.state.types[tile_pos[0]][tile_pos[1]])  # each block has a single type
            # for t in self.mask_type:
            #     all_types.add(t)
            self.type.update(self.mask_type)
            return self.type


        def add_prosperity_to_node(self, amt):
            self.state.prosperity[self.center[0]][self.center[1]] += amt
            self.state.updateFlags[self.center[0]][self.center[1]] = 1


        def prosperity(self):
            return self.state.prosperity[self.center[0]][self.center[1]]


        def traffic(self):
            if not self.state.out_of_bounds_Node(self.center[0], self.center[1]):  # let's get rid of this check later
                return self.state.traffic[self.center[0]][self.center[1]]


        def add_mask_type(self, type):
            self.mask_type.add(type)


        def clear_type(self, state):
            if self in state.construction:
                state.construction.discard(self)
            self.mask_type.clear()


        # def gen_adjacent(self, state):
        #     adj = set()
        #     for dir in src.movement.directions:
        #         pos = (self.center[0] + dir[0]*self.size, self.center[1] + dir[1]*self.size)
        #         if state.out_of_bounds_Node(*pos): continue
        #         node = state.nodes(*state.node_pointers[pos])
        #         adj.add(node)
        #     return adj

        def gen_adjacent_centers(self, state):
            adj = set()
            for dir in src.movement.directions:
                pos = (self.center[0] + dir[0]*self.size, self.center[1] + dir[1]*self.size)
                if state.out_of_bounds_Node(*pos): continue
                adj.add(pos)
            return adj


        def add_neighbor(self, node):
            self.neighbors_cached.add(node)
            self.neighbors_centers.add(node.center)


        def gen_neighbors_centers(self, state):
            neighbors = self.adjacent_centers.copy()
            i = 0
            for r in range(2,state.Node.neighborhood_radius+1):
                for ox in range(-r, r+1, 2*r):  # rings only
                    for oz in range(-r, r+1):
                        if ox == 0 and oz == 0: continue
                        x = (self.center[0])+ox*self.size
                        z = (self.center[1])+oz*self.size
                        if state.out_of_bounds_Node(x, z):
                            continue
                        # node = state.nodes(*state.node_pointers[(x, z)])
                        neighbors.add((x,z))
                for ox in range(-r+1, r):
                    for oz in range(-r, r + 1, 2*r):
                        if ox == 0 and oz == 0: continue
                        x = (self.center[0]) + ox * self.size
                        z = (self.center[1]) + oz * self.size
                        if state.out_of_bounds_Node(x, z):
                            continue
                        # node = state.nodes(*state.node_pointers[(x, z)])
                        neighbors.add((x, z))
            return neighbors


        # get local nodes
        def gen_local_centers(self, state):
            local = self.neighbors_centers.copy()
            for r in range(state.Node.neighborhood_radius+1, state.Node.locality_radius + 1):
                for ox in range(-r, r + 1, 2*r):
                    for oz in range(-r, r + 1):
                        x = (self.center[0]) + ox * self.size
                        z = (self.center[1]) + oz * self.size
                        # node = state.nodes(*state.node_pointers[(x, z)])
                        # if src.my_utils.TYPE.WATER.name in node.get_type():
                        #     continue
                        local.add((min(max(1, x), state.last_node_pointer_x),min(max(1, z), state.last_node_pointer_z)))
                for ox in range(-r+1, r):
                    for oz in range(-r, r + 1, 2*r):
                        x = (self.center[0]) + ox * self.size
                        z = (self.center[1]) + oz * self.size
                        # node = state.nodes(*state.node_pointers[(x, z)])
                        # if src.my_utils.TYPE.WATER.name in node.get_type():
                        #     continue
                        local.add((min(max(1, x), state.last_node_pointer_x), min(max(1, z), state.last_node_pointer_z)))
            return local


        def gen_range_centers(self, state):
            local = self.local_centers.copy()
            local.add(self.center)
            for r in range(state.Node.locality_radius+1, state.Node.range_radius + 1):
                for ox in range(-r, r + 1, 2*r):
                    for oz in range(-r, r + 1):
                        # if ox == 0 and oz == 0: continue
                        x = (self.center[0]) + ox * self.size
                        z = (self.center[1]) + oz * self.size
                        local.add((min(max(1, x), state.last_node_pointer_x),min(max(1, z), state.last_node_pointer_z)))
                for ox in range(-r+1, r):
                    for oz in range(-r, r + 1, 2*r):
                        # if ox == 0 and oz == 0: continue
                        x = (self.center[0]) + ox * self.size
                        z = (self.center[1]) + oz * self.size
                        local.add((min(max(1, x), state.last_node_pointer_x), min(max(1, z), state.last_node_pointer_z)))
            return local


        def get_locals_positions(self):
            arr = []
            for node in self.local:
                arr.append(node.center)
            return arr


        def get_neighbors_positions(self):
            return self.neighbors_centers

        def get_ranges_positions(self):
            return self.range_centers


        def get_lot(self):
            # finds enclosed green areas
            lot = set([self])
            new_neighbors = set()
            for i in range(5):
                new_neighbors = set([e for n in lot for e in n.adjacent() if e not in lot and (
                        src.my_utils.TYPE.GREEN.name in e.mask_type or src.my_utils.TYPE.TREE.name in e.mask_type or src.my_utils.TYPE.CONSTRUCTION.name in e.mask_type)])
                accept = set([n for n in new_neighbors if src.my_utils.TYPE.CONSTRUCTION.name not in n.mask_type])
                if len(new_neighbors) == 0:
                    break
                lot.update(accept)
            if len([n for n in new_neighbors if src.my_utils.TYPE.CONSTRUCTION.name not in n.mask_type]) == 0:  # neighbors except self
                return lot
            else:
                return None

    # def calc_local_prosperity(self, node_center):
    #     x = node_center[0]
    #     z = node_center[1]
    #     local_p = self.prosperity[x][z]
    #     for dir in src.movement.directions:
    #         local_p += self.prosperity[x + dir[0]][z + dir[1]]
    #     return local_p


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
        x1, z1, x2, z2 = self.rect
        abs_ground_hm = src.my_utils.get_heightmap(world_slice, "MOTION_BLOCKING_NO_LEAVES", -1) # inclusive of ground
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
        world_y = y1
        interface = http_framework.interfaceUtils.Interface(x=self.world_x, y=world_y, z=self.world_z,
                                                                   buffering=True, caching=True)
        # if (y2 > 150):
            # print("warning: Y bound is really high!")

        len_z = abs(z2 - z1)
        len_y = abs(y2 - y1)
        len_x = abs(x2 - x1)
        blocks_arr = [[[0 for z in range(len_z)] for y in range(len_y)] for x in range(len_x)] # the format of the state isn't the same as the file's.
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
                    # block = self.world_slice.getBlockAt(x, y, z)#, self.world_x, self.world_y, self.world_z)
                    # blocks_arr[xi][yi][zi] = block
                    zi += 1
                yi += 1
            xi += 1
        len_y = y2 - y1
        return interface, blocks_arr, world_y, len_y, abs_ground_hm


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

    def update_heightmaps(self):
        for pos in list(self.heightmap_tiles_to_update):
            x, z = pos
            if (x,z) in self.built_heightmap: # ignore buildings
                y = self.built_heightmap[(x,z)] - 1
                self.abs_ground_hm[x][z] = y + self.world_y
                self.rel_ground_hm[x][z] = y + 1
            elif (x,z) in self.exterior_heightmap:
                y = self.exterior_heightmap[(x,z)] - 1
                self.abs_ground_hm[x][z] = y + self.world_y
                self.rel_ground_hm[x][z] = y + 1
            else:  # traverse down to find first non passable block
                if self.traverse_update_flags[x][z] == True:
                    y = self.traverse_down_till_block(x, z) + 1
                    self.traverse_update_flags[x][z] = False
                    self.abs_ground_hm[x][z] = y + self.world_y - 1
                    self.rel_ground_hm[x][z] = y
                else:
                    y = self.rel_ground_hm[x][z]
                    self.abs_ground_hm[x][z] = y + self.world_y - 1
                    self.rel_ground_hm[x][z] = y
                self.heightmap_tiles_to_update.remove((x,z))
            curr_height = self.rel_ground_hm[x][z]
            if self.static_ground_hm[x][z] > curr_height:  # don't reduce heightmap ever. this is to avoid bugs rn
                self.static_ground_hm[x][z] = curr_height
            # self.heightmap_tiles_to_update.remove((x,z))
        # self.heightmap_tiles_to_update.clear()  # for some reason when put here, the buildings' dont stick. are they being overidden?

    def update_heightmaps_for_block(self, x, z):
        if (x,z) in self.built_heightmap: # ignore buildings
            y = self.built_heightmap[(x,z)] - 1
            self.abs_ground_hm[x][z] = y + self.world_y
            self.rel_ground_hm[x][z] = y + 1
        elif (x,z) in self.exterior_heightmap:
            y = self.exterior_heightmap[(x,z)] - 1
            self.abs_ground_hm[x][z] = y + self.world_y
            self.rel_ground_hm[x][z] = y + 1
        else:  # traverse down to find first non passable block
            y = self.traverse_down_till_block(x, z) + 1 # only call this if needs traversing
            self.abs_ground_hm[x][z] = y + self.world_y - 1
            self.rel_ground_hm[x][z] = y
        curr_height = self.rel_ground_hm[x][z]
        if self.static_ground_hm[x][z] > curr_height:  # don't reduce heightmap ever. this is to avoid bugs rn
            self.static_ground_hm[x][z] = curr_height
        return

    def traverse_down_till_block(self,x,z):
        y = self.traverse_from[x][z]+1  # don't start from top, but from max_building_height from rel
        # if y >= self.len_y: return False
        while y > 0:
            if self.blocks(x,y,z) not in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value]:
                break
            y-=1
        return y


    # def gen_types(self, heightmap):
    #     xlen = len(self.blocks)
    #     zlen = len(self.blocks[0][0])
    #     types = [["str" for i in range(zlen)] for j in range(xlen)]
    #     for x in range(xlen):
    #         for z in range(zlen):
    #             type = self.determine_type(x, z, heightmap)
    #             if type == "TREES":
    #                 self.trees.append((x, z))
    #             elif type == "TREES":
    #                 self.water.append((x,z))
    #             elif type == "LAVA":
    #                 self.lava.add((x, z))
    #             elif type == "FOREIGN_BUILT":
    #                 node_ptr = self.node_pointers[(x,z)]
    #                 if node_ptr:
    #                     node = self.nodes[node_ptr]
    #                     self.foreign_built.add(node)
    #             types[x][z] = type# each block is a list of types. The node needs to chek its assets
    #     return types

    def add_adjacent_tiles_to_nodes_with_land_neighbors(self, x, z):
        for dir in src.movement.cardinals:
            self.tiles_with_land_neighbors.add((
                max(min(x + dir[0], self.len_x), 0),
                max(min(z + dir[1], self.len_z), 0)
            ))

    def gen_types(self, heightmap):
        xlen = self.len_x
        zlen = self.len_z
        if xlen == 0 or zlen == 0:
            print("  Attempt: gen_types has empty lengths.")
        types = [["str" for j in range(zlen)] for i in range(xlen)]
        for x in range(xlen):
            for z in range(zlen):
                type_name = self.determine_type(x, z, heightmap).name
                if type_name == "WATER":
                    self.water.append((x,z))
                elif type_name == "BROWN":
                    self.add_adjacent_tiles_to_nodes_with_land_neighbors(x, z)
                elif type_name == "GREEN":
                    self.add_adjacent_tiles_to_nodes_with_land_neighbors(x, z)
                elif type_name == "TREE":
                    self.trees.append((x, z))
                    self.add_adjacent_tiles_to_nodes_with_land_neighbors(x,z)
                elif type_name == "ROAD":
                    nptr = self.node_pointers[(x,z)]
                    if nptr!= None:
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

    def determine_type(self, x, z, heightmap, yoffset = 0):
        block_y = int(heightmap[x][z]) - 1 + yoffset
        block = self.blocks(x,block_y,z)
        for i in range(1, len(src.my_utils.TYPE) + 1):
            if block in src.my_utils.TYPE_TILES.tile_sets[i]:
                return src.my_utils.TYPE(i)
        return src.my_utils.TYPE.BROWN



    def save_state(self, state, file_name):
        f = open(file_name, 'w')
        len_x = state.len_x
        len_y = state.len_y
        len_z = state.len_z
        f.write('{}, {}, {}, {}\n'.format(len_x, state.world_y, len_y, len_z))
        i = 0
        for position,block in self.changed_blocks.items():
            to_write = position+';'+block+"\n"
            f.write(to_write)
            i += 1
        f.close()
        print(str(i)+" assets saved")


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
            self.interface.placeBlockBatched(
                self.world_x + state_x, self.world_y + state_y, self.world_z + state_z, block, n_blocks
            )
            i += 1
        f.close()
        self.changed_blocks.clear()
        print(str(i)+" assets loaded")


    # NOTE: you need to get heihtmaps after you place block info. they should be last
    def step(self, is_rendering=True,use_total_changed_blocks=False):
        i = 0
        changed_arr = self.changed_blocks
        changed_arr_xz = self.changed_blocks_xz
        if use_total_changed_blocks:
            changed_arr = self.total_changed_blocks
            changed_arr_xz = self.total_changed_blocks_xz
        n_blocks = len(changed_arr)
        self.old_legal_actions = self.legal_actions.copy()  # needed to update
        for position, block in changed_arr.items():
            x,y,z = position
            if is_rendering == True:
                # self.interface.placeBlockBatched(self.world_x + x, self.world_y + y, self.world_z + z, block, n_blocks)
                self.interface.placeBlockBatched(x, y, z, block, n_blocks)
            i += 1
        self.update_heightmaps()  # must wait until all assets are placed
        for position in changed_arr_xz:
            x,z = position
            self.update_block_info(x, z)  # Must occur after new assets have been placed. Also, only the surface should run it.
        changed_arr.clear()
        changed_arr_xz.clear()
        # if i > 0:
        #     print(str(i)+" assets rendered")
        self.update_phase()
        self.step_number+=1



    def update_phase(self):
        p = np.sum(self.prosperity)
        # print("prosp is "+str(p))
        if p > self.phase3threshold:
            self.phase = 3
        elif p > self.phase2threshold:
            self.phase = 2


    def update_block_info(self, x, z):  # this might be expensive if you use this repeatedly in a group
        for xo in range(-1, 2):
            for zo in range(-1, 2):
                bx = x + xo
                bz = z + zo
                if self.out_of_bounds_2D(bx, bz):
                    continue
                # also need to update legal actions for neighbors
                self.legal_actions[bx][bz] = src.movement.get_legal_actions_from_block(self, self.blocks_arr, bx, bz, self.agent_jump_ability,
                                                                                   self.rel_ground_hm, self.agent_height,
                                                                                   self.unwalkable_blocks)

        # if x z not in closed_for_propagation
        self.pathfinder.update_sector_for_block(x, z, self.sectors,
                                                sector_sizes=self.pathfinder.sector_sizes,
                                                legal_actions=self.legal_actions, old_legal_actions=self.old_legal_actions)


    def get_adjacent_block(self, x_origin, y_origin, z_origin, x_off, y_off, z_off):
        x_target = x_origin + x_off
        y_target = y_origin + y_off
        z_target = z_origin + z_off
        if self.out_of_bounds_3D(x_target, y_target, z_target):
            return None
        return self.blocks(x_target,y_target,z_target)


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
        return x >= self.len_x or y >= self.len_y or z >= self.len_z or x < 0 or y < 0 or z < 0


    def out_of_bounds_2D(self, x, z):
        return x < 0 or z < 0 or x >= self.len_x or z >= self.len_z


    def out_of_bounds_Node(self, x, z):
        # if x < 0 or z < 0 or x > self.last_node_pointer_x or z > self.last_node_pointer_z: # the problem is that some assets don't point to a tile.
        return x < 0 or z < 0 or x > self.last_node_pointer_x or z > self.last_node_pointer_z # the problem is that some assets don't point to a tile.


    ### USED BY DEBUG ONLY
    def set_block(self, x, y, z, block_name):
        # self.blocks[x][y][z] = block_name
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
                node.add_mask_type(src.my_utils.TYPE.BRIDGE.name) # we don't use add_type. instead we give each tile a type
            else:
                node.clear_type(self)
                node.add_mask_type(road_type)
            for road in self.roads:
                # node.clear_type(self)  # mine
                node.add_neighbor(road)
                road.add_neighbor(node)
            if node in self.construction:
                self.construction.discard(node)
            self.roads.append(node)  # put node in roads array
            node.action_cost = 50#src.states.State.Node.ACTION_COSTS[src.my_utils.TYPE.MINOR_ROAD.name]


    def create_well(self, sx, sz, len_x, len_z):
        if len_x < 3 or len_z < 3:
            print("Error: well needs to be at least 3x3")
            return False, -1, []
        height = 2
        well_nodes = set()
        if self.out_of_bounds_Node(sx-6, sz-6) or self.out_of_bounds_Node(sx + len_x, sz + len_z) :
            return False, -1, []
        else:
            endpoints_x = [sx, sx+len_x-1]
            endpoints_z = [sz, sz+len_z-1]
            well_tiles = []
            highest_y = self.static_ground_hm[sx][sz] + 1
            for x in range(sx, sx + len_x + 1):
                for z in range(sz, sz + len_z + 1):
                    if highest_y < self.static_ground_hm[x][z]:
                        highest_y = self.static_ground_hm[x][z]
            if highest_y + height > self.len_y:
                return False, -1, []
            # create water
            for x in range(sx, sx+len_x):
                for z in range(sz, sz + len_z):
                    if (x == sx or x == sx+len_x-1) and \
                         (z == sz or z == sz+len_z-1):
                        src.states.set_state_block(self, x, highest_y, z, 'minecraft:air')
                    elif x == sx or x == sx+len_x-1 or \
                        z == sz or z == sz+len_z-1:
                        # src.states.set_state_block(self,x,lowest_y, z, 'minecraft:stripped_oak_log')
                        src.states.set_state_block(self,x,highest_y, z, 'minecraft:barrel[facing=up]')
                    else:
                        well_tiles.append((x, z))
                        src.states.set_state_block(self,x,highest_y, z, 'minecraft:water')
                    src.manipulation.flood_kill_logs(self,x,highest_y+2, z)
                    src.states.set_state_block(self,x,highest_y - 1, z, 'minecraft:barrel[facing=up]')
                    src.states.set_state_block(self,x,highest_y+1, z, 'minecraft:air')
                    src.states.set_state_block(self,x,highest_y+2, z, 'minecraft:air')
                    self.built.add(self.nodes(*self.node_pointers[(x,z)]))
                    well_nodes.add(self.nodes(*self.node_pointers[(x,z)]))
        return well_nodes, highest_y, well_tiles


    def init_main_st(self, create_well, viable_water_choices, attempt):
        well_tiles = []
        water_choices = viable_water_choices
        if len(self.water) <= 10:# or create_well:
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
            well_y = y-1
            if well_y >= 0:
                self.place_platform(found_nodes_iter=result, build_y=well_y)
            water_choices = well_tiles
        old_water = self.water.copy()
        self.water = self.water+well_tiles
        rand_index = randint(0, len(water_choices)-1)
        x1, y1 = water_choices[rand_index]
        n_pos = self.node_pointers[(x1, y1)]
        water_checks = 100
        n_pos, rand_index = self.init_find_water(water_choices, n_pos, water_checks, rand_index)
        if n_pos == False or n_pos == None:
            print(f"  Attempt {attempt}: could not find suitable water source. Trying again~")
            self.water = old_water
            return False, [], [], None
        n = self.nodes(*n_pos)

        loc = n.local()
        ran = n.range()
        # print("range being "+str(ran))
        # print("local being "+str(loc))
        # print('--------')
        n1_options = list(set(ran) - set(loc))  # Don't put water right next to water, depending on range
        if len(n1_options) < 1:
            print(f"  Attempt {attempt}: could not find any valid starting road options. Trying again~")
            # viable_water_choices.remove(rand_index)
            self.water = old_water
            return False, [], [], None

        n1 = np.random.choice(n1_options, replace=False)  # Pick random point of the above

        n1 = self.init_find_valid_n1(n1, n1_options, water_checks)
        if n1 == False:
            print(f"  Attempt {attempt}: could not find valid starting road option. Trying again~")
            self.water = old_water
            return False, [], [], None

        n2_options = list(set(n1.range()) - set(n1.local()))  # the length of the main road is the difference between the local and the range
        if len(n2_options) < 1:
            print(f"  Attempt {attempt}: could not find ending road options. Trying again~")
            self.water = old_water
            return False, [], [], None

        n2 = np.random.choice(n2_options, replace=False)  # n2 is based off of n1's range, - local to make it farther
        points = src.linedrawing.get_line((n1.center[0], n1.center[1]), (n2.center[0], n2.center[1]))
        limit = 200

        points = self.init_find_path_with_n2(n1, n2, n2_options, points, limit)
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
        self.set_type_road(points, src.my_utils.TYPE.MAJOR_ROAD.name) # TODO check if the fact that this leads to repeats causes issue
        middle_nodes = []
        if len(points) > 2:
            middle_nodes = points[1:len(points) - 1]
        self.road_segs.add(
            RoadSegment(self.nodes(x1,y1), self.nodes(x2,y2), middle_nodes, src.my_utils.TYPE.MAJOR_ROAD.name, self.road_segs, self))

        status = self.init_construction(points)
        if status == False:
            print(f"  Attempt {attempt}: tried to build road outside of bounds! Trying again~")
            self.water = old_water
            return False, [], [], None

        p1 = (x1, y1)
        p2 = (x2, y2)
        self.init_lots(*p1, *p2)  # main street is a lot
        if self.create_road(node_pos1=p1, node_pos2=p2, road_type=src.my_utils.TYPE.MAJOR_ROAD.name, only_place_if_walkable=True) == False:
            print(f"  Attempt {attempt}: Main street wasn't valid! Trying again~")
            self.water = old_water
            return False, [], [], None


        # debug
        # for node in self.roads:
        #     src.states.set_state_block(self,node.center[0], 19, node.center[1], 'minecraft:emerald_block')

        if self.sectors[x1, y1] != self.sectors[x2][y2]:
            p1 = p2  # make sure agents spawn in same sector


        # add starter agent 1
        head = choice(State.agent_heads)
        agent_a = src.agent.Agent(self, *p1, walkable_heightmap=self.rel_ground_hm,
                                    name=names.get_first_name(),parent_1=self.adam, parent_2=self.eve, head=head)
        self.add_agent(agent_a)
        agent_a.is_child_bearing = True

        # add starter agent 2
        head = choice(State.agent_heads)
        agent_b = src.agent.Agent(self, *p1, walkable_heightmap=self.rel_ground_hm,
                                  name=names.get_first_name(), parent_1=self.adam, parent_2=self.eve, head=head)
        self.add_agent(agent_b)
        agent_b.is_child_bearing = False

        # print(f"{agent_b.name}'s parent is {agent_b.parent_1.name}")

        # add child
        head = choice(State.agent_heads)
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

        # src.chronicle.chronicle_event(agent_a.motive, 'going', 900, agent_a)
        # print(src.chronicle.chronicles)
        # exit(1)
        # src.chronicle.place_chronicles(agen)

        return True, old_water, p1, agent_a


    def init_construction(self, points):
        for (x, y) in points:
            if self.out_of_bounds_Node(x,y):
                return False
            adjacent = self.nodes(x,y).range()  # this is where we increase building range
            adjacent = [s for n in adjacent for s in n.adjacent()]  # every node in the road builds buildings around them
            for pt in adjacent:
                if pt not in points:
                    self.set_type_building([self.nodes(pt.center[0], pt.center[1])])
        return True


    def init_find_path_with_n2(self, node1, node2, n2_options, points, limit):
        find_new_n2 = True
        i = 0
        n1 = node1
        n2 = node2
        while find_new_n2:
            if i > limit:
                return False
            find_new_n2 = False
            for p in points:
                x = self.node_pointers[p][0]
                z = self.node_pointers[p][1]
                y = self.rel_ground_hm[x][z] - 1
                b = self.blocks(x,y,z)
                if not self.is_valid_path_block(b):
                    # get new path
                    if len(n2_options) < 1:
                        return False
                    n2 = n2_options.pop()
                    points = src.linedrawing.get_line((n1.center[0], n1.center[1]), (n2.center[0], n2.center[1]))
                    find_new_n2 = True
                    i+=1
                    break
        return points


    def init_find_water(self, water, n_pos, water_checks, rand_index):
        i = 0
        pos = n_pos
        rand_index = rand_index
        # x1, y1 = viable_water_choices[rand_index]
        while pos == None:
            if rand_index in water:
                water.remove(rand_index)
            if i > water_checks:
                return False
            rand_index = randint(0, len(water)-1)
            x1, y1 = water[rand_index]
            pos = self.node_pointers[(x1, y1)]
            i+=1
        return n_pos, rand_index


    def is_valid_n(self, node):
        return src.my_utils.TYPE.WATER.name not in node.type and src.my_utils.TYPE.LAVA.name not in node.type and src.my_utils.TYPE.FOREIGN_BUILT.name not in node.type


    def init_find_valid_n1(self, n1, n1_options, water_checks):
        i = 0
        result = n1
        while not self.is_valid_n(result):  # generate and test until n1 isn't water
            # n1 = np.random.choice(n1_options, replace=False)  # too slow?
            result = n1_options.pop()
            if i >= water_checks or len(n1_options) > 0:
                return False
            i+=1
        return result


    def is_valid_path_block(self, block):
        return block not in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.WATER.value] and block not in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.LAVA.value] and block not in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.FOREIGN_BUILT.value]


    def add_agent(self, agent, use_auto_motive=True):
        self.new_agents.add(agent)  # to be handled by update_agents
        ax = agent.x
        az = agent.z
        self.agents_in_nodes[self.node_pointers[(ax, az)]].add(agent)
        agent.set_motive(agent.Motive.LOGGING)


    def update_agents(self, is_rendering=True):
        for agent in self.agents.keys():
            agent.unshared_resources['rest'] += agent.rest_decay
            agent.unshared_resources['water'] += agent.water_decay
            agent.unshared_resources['happiness'] += agent.happiness_decay
            agent.follow_path(state=self, walkable_heightmap=self.rel_ground_hm)
            agent.socialize(agent.found_and_moving_to_socialization)
            if is_rendering:
                agent.render()
        new_agents = self.new_agents.copy()
        for new_agent in new_agents:  # because error occurs if dict changes during iteration
            self.agents[new_agent] = (new_agent.x, new_agent.y, new_agent.z)
            self.new_agents.remove(new_agent)


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
            if self.out_of_bounds_Node(point[0], point[1]):
                return False
            node = self.node_pointers[point]  # node coords
            if node not in nodes:
                nodes.append(node)
        return nodes

    # might have to get point2 within the func, rather than pass it in
    def create_road(self, node_pos1, node_pos2, road_type, points=None, leave_lot=False, correction=5, road_blocks=None,road_block_slabs=None, inner_block_rate=1.0, outer_block_rate=0.9, fringe_rate=0.05, add_as_road_type = True, bend_if_needed=False, only_place_if_walkable=False, dont_rebuild = True, cap_dist=30, is_capping_dist=True):
        if is_capping_dist:
            if math.dist(node_pos1, node_pos2) > cap_dist:
                return False
        water_set = set(self.water)
        built_set = set(self.built)
        block_path = []

        def is_valid(state, pos):
            nonlocal water_set
            nonlocal tile_coords
            nonlocal built_set
            return pos not in tile_coords and pos not in water_set and pos not in state.foreign_built# and pos not in built_set

        def is_walkable(state, path):
            last_y = state.rel_ground_hm[path[0][0]][path[0][1]]
            for i in range(1, len(path)):
                y = state.rel_ground_hm[path[i][0]][path[i][1]]
                dy = abs(last_y - y)
                if dy > state.agent_jump_ability:
                    # print("returning")
                    return False
                last_y = y
            return True
        if points == None:
            block_path = src.linedrawing.get_line(node_pos1, node_pos2) # inclusive
        else:
            block_path = points
        if bend_if_needed:
            found_road = False
            tile_coords = {tilepos for node in self.built for tilepos in node.get_tiles()}
            if any(not is_valid(self, tile) for tile in block_path) or not is_walkable(self, block_path):
                # get nearest built
                built_node_coords = [node.center for node in self.built]  # returns building node coords

                built_diags = [(node[0] + dir[0] * self.node_size, node[1] + dir[1] * self.node_size)
                               for node in built_node_coords for dir in src.movement.diagonals if is_valid(self, (node[0] + dir[0] * self.node_size, node[1] + dir[1] * self.node_size))]
                nearest_builts = src.movement.find_nearest(self, *node_pos1, built_diags, 5, 30, 10)
                # print("nearest builts is ")
                # print(str(nearest_builts))
                # self.bendcount += len(near)
                closed = set()
                found_bend = False
                for built in nearest_builts:
                    if found_bend == True: break
                    for diag in src.movement.diagonals:
                        nx = self.node_size * diag[0] + built[0]
                        nz = self.node_size * diag[1] + built[1]
                        if (nx, nz) in closed: continue
                        closed.add((nx, nz))
                        if self.out_of_bounds_Node(nx, nz): continue
                        p1_to_diag = src.linedrawing.get_line(node_pos1, (nx, nz))  # TODO add aux to p1 so it checks neigrboars
                        if any(not is_valid(self, tile) for tile in p1_to_diag) or not is_walkable(self, p1_to_diag): continue

                        # # debug
                        # for tile in p1_to_diag:
                        #     set_state_block(self,tile[0], self.rel_ground_hm[tile[0]][tile[1]]+10,tile[1], 'minecraft:diamond_block')

                        self.semibends += 1
                        # p2_to_diag = src.linedrawing.get_line((nx, nz), node_pos2)

                        closest_point, p2_to_diag = self.get_closest_point(node=self.nodes(nx, nz),
                                                                           lots=[],
                                                                           possible_targets=self.roads,
                                                                           road_type=road_type,
                                                                           state=self,
                                                                           leave_lot=False,
                                                                           correction=correction)

                        # lets try raycastign up to the dist of p2
                        if p2_to_diag is None: continue # if none found, try again
                        if any(not is_valid(self,tile) for tile in p2_to_diag) or not is_walkable(self, p2_to_diag): # if building is in path. try again
                            found_raycast = False
                            leeway = 0
                            dist = cap_dist # CAPPED #int(len(p2_to_diag)/2)
                            steps = 60
                            step_amt = 360/steps
                            status = False
                            raycast_path = None
                            for i in range(steps):
                                end_x = int(math.cos(math.radians(i*step_amt)) * dist) + nx  # nx and nz are the satrt
                                end_z = int(math.sin(math.radians(i*step_amt)) * dist) + nz
                                if self.out_of_bounds_Node(end_x, end_z): continue
                                # set_state_block(self, end_x, self.rel_ground_hm[end_x][end_z]+15, end_z, "minecraft:gold_block")
                                status, raycast_path = self.raycast_using_nodes(start=(nx, nz), end=(end_x, end_z), target=self.roads, breaks_list=[])#, breaks_list=[self.built])
                                if status is True: break
                            if status is False: continue
                            if any(not is_valid(self, tile) for tile in raycast_path) or not is_walkable(self, raycast_path): continue
                            p2_to_diag = raycast_path
                            found_road = True
                        else:
                            found_road = True
                        # # debug
                        # for tile in p1_to_diag:
                        #     set_state_block(self, tile[0], self.rel_ground_hm[tile[0]][tile[1]] + 10, tile[1],
                        #                     'minecraft:diamond_block')
                        # for tile in p2_to_diag:
                        #     set_state_block(self, tile[0], self.rel_ground_hm[tile[0]][tile[1]] + 10, tile[1],
                        #                     'minecraft:emerald_block')
                        block_path = p1_to_diag + p2_to_diag  # concat two, building-free roads
                        self.bends += 1
                        found_bend = True
                        break
            else:
                found_road = True
            if not found_road:
                # print("create_road error: no valid road found.")
                return False
        # elif only_place_if_walkable:
        #     if not is_walkable(self, block_path):
        #         return False
        if not is_walkable(self, block_path):
            return False
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
            node_path.append(end)  # end
        ## draw two more lines
        check1 = True
        check2 = True
        if check1:
            n1 = self.nodes(*node_pos1)
            for rs in self.road_segs:
                if node_pos1 in rs.nodes:  # if the road is in roads already, split it off
                    rs.split(n1, self.road_segs, self.road_nodes, state=self)  # split RoadSegment
                    break
        if check2:
            n2 = self.nodes(*node_pos2)
            for rs in self.road_segs:
                if node_pos2 in rs.nodes:
                    rs.split(n2, self.road_segs, self.road_nodes, state=self)
                    break
        # do checks
        if add_as_road_type == True:  # allows us to ignore the small paths from roads to buildings
            road_segment = RoadSegment(self.nodes(*node_pos1), self.nodes(*node_pos2), middle_nodes, road_type, self.road_segs, state=self)
            self.road_segs.add(road_segment)

        # place assets. TODO prolly not right- i think you wanna render road segments
        if road_blocks == None:
            road_blocks = src.my_utils.ROAD_SETS['default']
        if road_block_slabs == None:
            road_block_slabs = src.my_utils.ROAD_SETS['default_slabs']
        ## render
        prev_road_y = self.static_ground_hm[block_path[0][0]][block_path[0][1]] - 1

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
                    if (x, z) in self.trees:  # when sniped
                        self.trees.remove((x, z))

                if src.manipulation.is_sapling(self, x, y + 1, z):
                    set_state_block(self, x, y + 1, z, "minecraft:air")
                    if (x, z) in self.saplings:  # when sniped
                        self.saplings.remove((x, z))
                if random() < rate:
                    # kill tree
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
                    # if (px, pz) in self.road_tiles: continue

                    if (px, pz) in self.road_tiles or (py-1 >= 0 and self.blocks(px, py - 1, pz) in src.my_utils.TYPE_TILES.tile_sets[
                        src.my_utils.TYPE.MAJOR_ROAD.value]): continue  # might not work well.

                    # if dont_rebuild and (px, pz) in self.road_tiles: continue
                    # self.road_tiles.add((px,pz))
                    block_type = 0
                    facing_data = False

                    block = choice(self.road_set[0])

                    # if not in road already, traverse down and fill with scaffold
                    # in a separate if-block because I want them to check nexts as well
                    # TODO make sure these arent overriden
                    if up_slab_next or up_stairs_next:
                        if up_slab_next:
                            up_slab_next = False
                            block = choice(self.road_set[1])
                            block_type = 1
                        elif up_stairs_next:
                            if next_facing is not None:
                                facing_data = next_facing
                                # block = choice(self.road_set[2]) + data
                                block = choice(self.road_set[2]) + """[facing={facing}]""".format(facing=facing_data)
                                block_type = 2
                                # cap_with_stairs = True
                            else:
                                # testing diagonals where would be stairs
                                # py -= 1
                                block = choice(self.road_set[0])
                                block_type = 1  # slab to make it smooth nonetheless
                                is_diagonal = True
                            up_stairs_next = False

                        # guarantee another forward check
                        if ndy > 0 and nndy == 0:  # slab above
                            up_slab_next = True
                            pass
                        elif ndy > 0 and nndy > 0:  # slope 1
                            # py += 1
                            dx = path[i + 2][0] - path[i+1][0]
                            dz = path[i + 2][1] - path[i+1][1]
                            next_facing = None
                            up_stairs_next = True
                            # test if this is right
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
                                # py += 1
                                # block = choice(self.road_set[1])
                                # block_type = 1
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
                                    block = choice(self.road_set[2]) + """[facing={facing}]""".format(facing=facing_data)
                                    block_type = 2
                                else:
                                    block = choice(self.road_set[0])
                                    block_type = 1
                                    is_diagonal = True
                                    # block = choice(self.road_set[1])
                                    # block_type = 1

                                    # if block[-1] == 's': block = block[:-1]  # for brick(s)
                                    # block += '_slab'

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
                                    block = choice(self.road_set[2]) + """[facing={facing}]""".format(facing=facing_data)
                                    block_type = 2
                                else:
                                    block = choice(self.road_set[0])
                                    block_type = 1
                                    is_diagonal = True
                                    # block = choice(self.road_set[1])
                                    # block_type = 1

                                    # if block[-1] == 's': block = block[:-1]  # for brick(s)
                                    # block += '_slab'

                            elif ndy < 0 and nndy == 0:  # slab below (in place)
                                block = choice(self.road_set[1])
                                block_type = 1

                            elif ndy > 0 and nndy > 0:  # slope 1
                                # py += 1
                                dx = path[i + 2][0] - path[i+1][0]
                                dz = path[i + 2][1] - path[i+1][1]
                                next_facing = None
                                up_stairs_next = True
                                # test if this is right
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
                            elif ndy < 0 and nndy > 0:  # flatten next block to get slope 0
                                pass
                                # set_state_block(self,px, py, pz, block)
                                # px = path[i+1][0]
                                # pz = path[i+1][1]
                                # static_temp[px][pz]+=1
                                # set_state_block(self,px, py+1, pz, block)
                            elif ndy > 0 and nndy < 0:  # flatten (lower) next block to get slope 0
                                pass
                                # set_state_block(self,px, py, pz, block)  # for curr
                                # px = path[i+1][0]
                                # pz = path[i+1][1]
                                # set_state_block(self,px, py, pz, block)  # for ahead
                                # py = static_temp[px][pz] + 1
                                # set_state_block(self,px, py, pz, "minecraft:air")  # for ahead
                                # static_temp[px][pz] = py
                        elif check_next_road:
                            if ndy > 0:
                                px = path[i + 1][0]
                                pz = path[i + 1][1]
                                # py += 1
                                block = choice(self.road_set[1])
                                block_type = 1
                                # if block[-1] == 's': block = block[:-1]  # for brick(s)
                                # block += "_slab"
                            elif ndy < 0:
                                block = choice(self.road_set[1])
                                block_type = 1
                                # if block[-1] == 's': block = block[:-1]  # for brick(s)
                                # block += "_slab"
                    static_temp[px][pz] = py + 1
                    # set_state_block(self, px, py, pz, block)
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
                        self.road_tiles.add((px,pz))
            return blocks_ordered, blocks_set


        def set_blocks_for_path_aux(self, main_path, aux_path, rate, blocks_ordered, main_path_set):
            def add_aux_block(self,x,y,z,offx, offz,type,facing, is_diagonal_stairs, dx, dz):
                nx = x + offx
                nz = z + offz
                if (nx, nz) in self.road_tiles or self.blocks(nx,y-1,nz) in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.MAJOR_ROAD.value]: return False  # might not work well.
                nonlocal main_path_set
                if src.manipulation.is_log(self, nx, y + 1, nz):
                    src.manipulation.flood_kill_logs(self, nx, y + 1, nz)
                    if (nx, nz) in self.trees:  # when sniped
                        self.trees.remove((nx, nz))

                if src.manipulation.is_sapling(self, nx, y + 1, nz):
                    set_state_block(self,nx,y+1,nz,"minecraft:air")
                    if (nx, nz) in self.saplings:  # when sniped
                        self.saplings.remove((nx, nz))


                if (nx, nz, 1) not in main_path_set and random() < rate:  # prioritize slabs... might overwrite important sutff
                    if self.blocks(nx, y+1, nz) in src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.GREEN.value].union(src.my_utils.TYPE_TILES.tile_sets[src.my_utils.TYPE.PASSTHROUGH.value]) and self.node_pointers[(nx,nz)] is not None and self.nodes(*self.node_pointers[(nx,nz)]) not in self.built:
                        self.place_scaffold_block(nx, y, nz)
                        set_state_block(self,nx,y+1,nz, "minecraft:air")
                    if (nx,nz) in self.exterior_heightmap:
                        self.place_scaffold_block(nx, y, nz)
                        set_state_block(self,nx,y,nz, choice(self.road_set[0]))
                    else:
                        if facing:
                            if (facing[0] in ['e','w'] and offx == 0) or (facing[0] in ['n','s'] and offz == 0):
                                self.place_scaffold_block(nx, y, nz)
                                set_state_block(self,nx,y,nz, choice(self.road_set[type])+"""[facing={facing}]""".format(facing=facing))
                        else:  # normal stuff
                            if dx is not None and (is_diagonal_stairs and dx == -offx or is_diagonal_stairs and dz == -offz):
                                type = 0
                            self.place_scaffold_block(nx, y, nz)
                            set_state_block(self, nx, y, nz, choice(self.road_set[type]))
                    is_slab_or_stairs = type > 0
                    main_path_set.add((x+offx,z+offz, is_slab_or_stairs))
                    if type == 1:
                        self.road_tiles.add((nx, nz))

            length = len(blocks_ordered)
            for i in range(length):
                type, x, y, z, facing, is_diagonal = blocks_ordered[i]
                dx = dz = None
                if i+1 < length:
                    ntype, nx, ny, nz, nfacing, nis_diagonal = blocks_ordered[i+1]
                    dx = nx - x
                    dz = nz - z
                add_aux_block(self,x,y,z,1,0,type,facing,is_diagonal, dx,dz)
                add_aux_block(self,x,y,z,-1,0,type,facing, is_diagonal, dx,dz)
                add_aux_block(self,x,y,z,0,1,type,facing, is_diagonal,dx,dz)
                add_aux_block(self,x,y,z,0,-1,type,facing, is_diagonal,dx,dz)

        blocks_ordered, blocks_set = set_blocks_for_path(self,block_path,inner_block_rate)

        aux_paths = []
        for card in src.movement.cardinals:
            # offset1 = choice(src.movement.cardinals)
            def clamp_to_state_coords(state, x, z):
                if x > state.last_node_pointer_x:
                    x = state.last_node_pointer_x
                elif x < 0:
                    x = 0
                if z > state.last_node_pointer_z:
                    z = state.last_node_pointer_z
                elif z < 0:
                    z = 0
                return (x,z)
            # aux1 = src.linedrawing.get_line( p1, p2 )
            aux_path = []
            for block in block_path:
                pos = clamp_to_state_coords(self, block[0] + card[0], block[1] + card[1])
                if abs(self.rel_ground_hm[pos[0]][pos[1]] - self.rel_ground_hm[block[0]][block[1]]) > 1: continue
                if pos not in blocks_set:  # to avoid overlapping road blocks
                    aux_path.append(pos)
                    # blocks_set.add(pos)
            # aux_path = [clamp_to_state_coords(self, block[0]+card[0], block[1]+card[1]) for block in block_path]
            # if is_walkable(self,aux_path):
            #     aux_paths.append(aux_path)
        set_blocks_for_path_aux(self, block_path, aux_paths, outer_block_rate, blocks_ordered, blocks_set)


        # ## borders
        # for aux_path in aux_paths:
        #     # last_aux_y = self.static_ground_hm[aux_path[0][0]][aux_path[0][1]] - 1
        #     length = len(aux_path)
        #     static_temp = self.rel_ground_hm.copy()
        #     for x in range(len(static_temp)):
        #         for z in range(len(static_temp[0])):
        #             static_y = self.static_ground_hm[x][z]
        #             if static_temp[x][z] > static_y:
        #                 static_temp[x][z] = static_y
        #     for i in range(length):
        #         x = aux_path[i][0]
        #         z = aux_path[i][1]
        #         # y = int(self.static_ground_hm[x][z]) - 1
        #         y = int(static_temp[x][z]) - 1
        #         block = self.blocks(x,y,z)
        #         if self.blocks(x,y,z )== "minecraft:water" or src.manipulation.is_log(self, x, y, z):
        #             continue
        #         if random() < outer_block_rate:
        #             check_next_road = True
        #             check_next_next_road = True
        #             if i >= length - 2:
        #                 check_next_road = False
        #                 check_next_next_road = False
        #             elif i >= length - 1:
        #                 check_next_road = False
        #             next_road_y = 0
        #             next_next_road_y = 0
        #             if check_next_road:
        #                 next_road_y = static_temp[aux_path[i + 1][0]][aux_path[i + 1][1]] - 1
        #             if check_next_next_road:
        #                 nnx = aux_path[i + 2][0]
        #                 nnz = aux_path[i + 2][1]
        #                 next_next_road_y = static_temp[nnx][nnz] - 1
        #             ndy = next_road_y - y
        #             nndy = next_next_road_y - next_road_y
        #             px = x  # placement x
        #             py = y
        #             pz = z
        #             block = choice(src.my_utils.ROAD_SETS['default'])
        #             if check_next_next_road:
        #                 if ndy == 0:
        #                     pass
        #                 elif ndy > 0 and nndy == 0:  # slab above
        #                     py += 1
        #                     block += "_slab"
        #                 elif ndy < 0 and nndy == 0:  # slab below (in place)
        #                     block += "_slab"
        #                 elif ndy > 0 and nndy > 0:  # slope 1
        #                     py+=1
        #                     dx = block_path[i+1][0] - block_path[i][0]
        #                     dz = block_path[i+1][1] - block_path[i][1]
        #                     facing = None
        #                     if dx > 0 and dz == 0: facing = None
        #                     elif dx < 0 and dz == 0: facing = "west"
        #                     elif dz > 0 and dx == 0: facing = "south"
        #                     elif dz < 0 and dx == 0: facing = "north"
        #                     else: pass
        #                     if facing is not None:
        #                         block += """_stairs[facing={facing}]""".format(facing=facing)
        #                     else:
        #                         block += '_slab'
        #                 elif ndy < 0 and nndy > 0:  # flatten next block to get slope 0
        #                     set_state_block(self, px, py, pz, block)
        #                     px = aux_path[i + 1][0]
        #                     pz = aux_path[i + 1][1]
        #                     # py = static_temp[px][pz] + 1
        #                     static_temp[px][pz] += 1
        #                     # set_state_block(self,px, py, pz, "minecraft:oak_planks")
        #                     set_state_block(self, px, py, pz, block)
        #                     # block = "minecraft:air"
        #                     # block = "minecraft:diamond_block"
        #                 elif ndy < 0 and nndy < 0:  # slope -1
        #                     dx = aux_path[i + 1][0] - aux_path[i][0]
        #                     dz = aux_path[i + 1][1] - aux_path[i][1]
        #                     facing = None
        #                     if dx > 0 and dz == 0: facing = "west"
        #                     elif dx < 0 and dz == 0: facing = "east"
        #                     elif dz > 0 and dx == 0: facing = "north"
        #                     elif dz < 0 and dx == 0: facing = "south"
        #                     else: pass
        #                     if facing is not None:
        #                         block += """_stairs[facing={facing}]""".format(facing=facing)
        #                     else:
        #                         block += '_slab'
        #                 elif ndy > 0 and nndy < 0:  # flatten (lower) next block to get slope 0
        #                     set_state_block(self, px, py, pz, block)  # for curr
        #                     px = aux_path[i + 1][0]
        #                     pz = aux_path[i + 1][1]
        #                     set_state_block(self, px, py, pz, block)  # for ahead
        #                     ty = static_temp[px][pz] + 1
        #                     set_state_block(self, px, ty, pz, "minecraft:air")  # for ahead
        #                     static_temp[px][pz] += 1
        #             elif check_next_road:
        #                 if ndy > 0:
        #                     px = aux_path[i + 1][0]
        #                     pz = aux_path[i + 1][1]
        #                     py += 1
        #                     block = block+"_slab"
        #                 elif ndy < 0:
        #                     block = block+"_slab"
        #             static_temp[px][pz] = py + 1
        #             set_state_block(self, px, py, pz, block)
        #             if not self.out_of_bounds_3D(px, py + 1, pz):
        #                 if 'snow' in self.blocks(px, py + 1, pz):
        #                     set_state_block(self, px, py + 1, pz, 'minecraft:air')
        #             if src.manipulation.is_leaf(self.blocks(x,y + 2,z)):
        #                 src.manipulation.flood_kill_leaves(self, x, y + 2, z, 10)

                    ### OG ALG
                    # check_next_road = True
                    # if i >= length-1:
                    #     check_next_road = False
                    # next_road_y = -1
                    # if check_next_road:
                    #     next_road_y = self.static_ground_hm[aux_path[i+1][0]][aux_path[i+1][1]] - 1
                    #
                    # if prev_road_y - (self.static_ground_hm[x][z]-1) > 0:
                    #     # set_state_block(self, x, y+1, z, choice(road_block_slabs))
                    #     set_state_block(self, x, y+1, z, "minecraft:oak_slab")
                    # elif check_next_road and next_road_y - (self.static_ground_hm[x][z]-1) > 0:
                    #     set_state_block(self, x, y+1, z, "minecraft:oak_slab")
                    #     # set_state_block(self, x, y + 1, z, choice(road_block_slabs))
                    # else:
                    #     # set_state_block(self, x, y, z, choice(road_blocks))
                    #     set_state_block(self, x, y, z, "minecraft:oak_planks")
                    # prev_road_y = y

        # self.set_type_road(node_path, src.my_utils.TYPE.MAJOR_ROAD.name)
        self.road_nodes.append(self.nodes(*self.node_pointers[node_pos1]))  # should these even go here first?
        self.road_nodes.append(self.nodes(*self.node_pointers[node_pos2]))
        if add_as_road_type:
            self.set_type_road(node_path, road_type)
        return [node_pos1, node_pos2]


    def raycast_using_nodes(self, start, end, target, breaks_list):
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


    def append_road(self, point, road_type, leave_lot=False, correction=5, bend_if_needed = False, only_place_if_walkable=False, dont_rebuild=True):
        # convert point to node
        point = self.node_pointers[point]
        node = self.nodes(*point)
        if point is None or node is None:
            print("tried to build road outside of Node bounds!")
            return False
        # self.roads.append((point1))
        closest_point, path_points = self.get_closest_point(node=self.nodes(*self.node_pointers[point]), # get closest point to any road
                                                              lots=[],
                                                              possible_targets=self.roads,
                                                              road_type=road_type,
                                                              state=self,
                                                              leave_lot=False,
                                                              correction=correction)
        if closest_point == None:
            return False
        (x2, y2) = closest_point
        closest_point = None
        # print("given point is ")
        # print("path point is "+str(path_points))

        # if road_type == src.my_utils.TYPE.MINOR_ROAD.name:
        #     closest_point = self.get_point_to_close_gap_minor(*point, path_points)  # connects 2nd end of minor roads to the nearest major or minor road. I think it's a single point
        # elif road_type == src.my_utils.TYPE.MAJOR_ROAD.name:  # extend major
        #     closest_point = self.get_point_to_close_gap_major(node, *point, path_points)  # "extends a major road to the edge of a lot"
        closest_point = self.get_point_to_close_gap_minor(*point, path_points)  # connects 2nd end of minor roads to the nearest major or minor road. I think it's a single point

        # print("closest point is "+str(closest_point))
        if closest_point is not None:
            point = closest_point
            path_points.extend(src.linedrawing.get_line((x2, y2), point))  # append to the points list the same thing in reverse? or is this a diff line?
            # print("path points is "+str(path_points))

        status = self.create_road(point, (x2, y2), road_type=road_type, points=path_points, bend_if_needed=bend_if_needed, only_place_if_walkable=True)#, only_place_if_walkable=only_place_if_walkable, dont_rebuild)
        if status == False:
            return False
        return True


    def get_point_to_close_gap_minor(self, x1, z1, points):
        # print("BUILDING MINOR ROAD")
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
            if src.my_utils.TYPE.MAJOR_ROAD.name in landtype or src.my_utils.TYPE.MINOR_ROAD.name in landtype:# and src.my_utils.TYPE.BYPASS.name not in landtype:
                return (x2, z2)
            (x2, z2) = (x2 + x, z2 + z)
        return None


    def get_point_to_close_gap_major(self, node, x1, z1, points):
        # print("EXTENDING MAJOR ROAD")
        # print('node is ' + str(node.center))
        # print('with xz ' + str((x1, z1)))
        # print('points is  to is ' + str(points))
        # extends a major road to the edge of a lot
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
                # landtype = self.nodes[(x2, z2)].mask_type
                return (x2, z2)
            (x2, z2) = (x2 + x, z2 + z)
        return None


    def get_closest_point(self, node, lots, possible_targets, road_type, state, leave_lot, correction=5):
        x, z = node.center
        nodes = possible_targets
        # nodes = [n for n in nodes if src.my_utils.TYPE.BRIDGE.name not in n.get_type()]  # expensive
        # if len(nodes) == 0:
        #     print("leave_lot = {} no road segments".format(leave_lot))
        #     return None, None
        dists = [math.hypot(n.center[0] - x, n.center[1] - z) for n in nodes]
        node2 = nodes[dists.index(min(dists))]
        (x2, z2) = (node2.center[0], node2.center[1])
        xthr = 2   # TODO tweak these
        zthr = 2
        if node.lot is None:
            # if abs(x2 - x) > xthr and abs( z2 - z) > zthr:
            if True:
            # if road_type is not src.my_utils.TYPE.MINOR_ROAD.name and abs(x2 - x) > xthr and abs(
                if node2.lot is not None:
                    (cx2, cy2) = node2.lot.center
                    # print('center is '+str((cx2, cy2)))
                    # print('with xz '+str((x,z)))
                    # (x, z) = (x + x - cx2, z + z - cy2)  ### CHANGED
                    # print('going to is '+str((x, z)))
                    # clamp road endpoints
                    # print("BUILDING ROAD. IS IT LONG?")
                    if x >= self.last_node_pointer_x:
                        print("YES")
                        x = self.last_node_pointer_x
                    if x < 0:
                        print("YES")
                        x = 0
                    if z >= self.last_node_pointer_z:
                        print("YES")
                        z = self.last_node_pointer_z
                    if z < 0:
                        print("YES")
                        z = 0
                if abs(x2 - x) > xthr and abs(z2 - z) > zthr:
                    if not state.add_lot([(x2, z2), (x, z)]):
                        print("leave_lot = {} add lot failed".format(leave_lot))
                        return None, None
            # else:
            #     print("Failed!")
            #     return None, None
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
    if state.out_of_bounds_Node(x,z) or y >= state.len_y: return False
    state.traverse_from[x][z] = max(y, state.traverse_from[x][z])
    # if y > state.traverse_from[x][z]:
    #     state.traverse_from[x][z] = y
    state.traverse_update_flags[x][z] = True
    state.heightmap_tiles_to_update.add((x,z))
    state.blocks_arr[x][y][z]= block_name
    state.changed_blocks_xz.add((x,z))
    state.total_changed_blocks_xz.add((x,z))
    state.changed_blocks[(x,y,z)] = block_name
    state.total_changed_blocks[(x,y,z)] = block_name
    return True


class RoadSegment:
    def __init__(self, rnode1, rnode2, nodes, type, rslist, state):
        self.start = rnode1
        self.end = rnode2
        self.type = type
        self.shape = []
        self.nodes = nodes
        # mine
        # for n in nodes:
        #     if n in state.built:
        #         state.built.discard(n)
        # if self.start in state.built:
        #     state.built.discard(self.start)
        # if self.end in state.built:
        #     state.built.discard(self.end)

    def merge(self, rs2, match, rs_list, roadnodes):
        if self.type != rs2.mask_type:
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


    def split(self, node, rs_list, roadnodes, state):
        roadnodes.append(node)
        roadnodes.append(node)

        i = 0
        while i < len(self.nodes) - 1:
            if self.nodes[i] == (node.center[0], node.center[1]):
                break
            i += 1
        nodes1 = self.nodes[:i]
        nodes2 = self.nodes[i + 1:]

        new_rs = RoadSegment(node, self.end, nodes2, self.type, roadnodes, state=state)
        rs_list.add(new_rs)

        self.nodes = nodes1
        self.end = node

        # for n in roadnodes:
        #     if n in state.built:
        #         state.built.discard(n)
        # if self.start in state.built:
        #     state.built.discard(self.start)
        # if self.end in state.built:
        #     state.built.discard(self.end)


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
        bx, by  = (int(ax), int(ay))
        self.center = (cx, cy) = self.state.node_pointers[(bx, by)]
        center_node = self.state.nodes(cx,cy)

        lot = set([center_node])
        self.border = set()
        while True:
            neighbors = set([e for n in lot for e in n.adjacent() if \
                             e not in lot and e.lot is None and e.center[0] != pt1[0] and e.center[0] != pt2[0] and e.center[1] != pt1[ 1] and e.center[1] != pt2[1] \
                             and src.my_utils.TYPE.WATER.name not in e.mask_type])
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
