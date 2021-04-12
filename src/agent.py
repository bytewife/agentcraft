import math

from scipy.spatial import KDTree
from random import choice, random, choices, randint
from enum import Enum
import src.pathfinding
import src.states
import src.manipulation
import src.movement
import src.my_utils
import src.scheme_utils
import http_framework.interfaceUtils
from math import dist, ceil

class Agent:

    class Motive(Enum):
        LOGGING = 0
        BUILD = 1
        IDLE = 2
        WATER = 3
        REST = 4
        REPLENISH_TREE = 5

    shared_resources = {
        "oak_log": 0,
        "dark_oak_log": 0,
        "spruce_log": 0,
        "birch_log": 0,
        "acacia_log": 0,
        "jungle_log": 0,
    }
    max_turns_staying_still = 10



    def __init__(self, state, state_x, state_z, walkable_heightmap, name, head,
                 parent_1=None, parent_2=None, motive=Motive.LOGGING.name):

        self.x = self.rendered_x = state_x
        self.z = self.rendered_z = state_z
        self.y = self.rendered_y = walkable_heightmap[state_x][state_z] + 0
        self.dx = self.dz = 1  # temp
        self.name = name
        self.parent_1 = parent_1
        self.parent_2 = parent_2
        self.state = state
        self.path = []
        self.motive = motive
        self.current_action_item = ""
        self.favorite_item = choice(src.my_utils.AGENT_ITEMS['FAVORITE'])
        self.head = head
        self.water_max = 100
        self.water_dec_rate = -0.2 # lose this per turn
        self.water_inc_rate = 10
        self.thirst_thresh = 50
        self.rest_dec_rate = -0.15
        self.rest_inc_rate = 2
        self.rest_thresh = 30
        self.rest_max = 100
        self.unshared_resources = {
            "water": self.water_max * 0.8,
            "rest": self.rest_max * 0.8
        }
        self.build_params = set()
        self.building_material = ''
        self.build_cost = 0
        self.tree_grow_iteration = 0
        self.tree_grow_iterations_max = randint(3,5)
        self.tree_leaves_height = randint(5,7)
        self.turns_staying_still = 0


    def find_build_location(self, building_file, wood_type):
        f = open(building_file, "r")
        size = f.readline()
        f.close()
        x_size, y_size, z_size = [int(n) for n in size.split(' ')]
        i = 0
        build_tries = 200
        while i < build_tries:
            construction_site = choice(list(self.state.construction))
            result = self.check_build_spot(construction_site, building_file, x_size, z_size, wood_type)
            if result != None:
                # check if any of the nodes are in built
                if result[1] in self.state.built:
                    continue
                not_in_built = True
                for node in result[2]:
                    if node in self.state.built:
                        not_in_built = False
                        break
                # see if found road is in same sector
                if not_in_built:
                    nx, nz = result[0].center
                    if self.state.sectors[self.x][self.z] == self.state.sectors[nx][nz]:
                        assert type(result[2]) == set
                        for node in result[2].union({result[1]}):  # this is equal to
                            # src.states.set_state_block(self.state, node.center[0], self.state.rel_ground_hm[node.center[0]][node.center[1]]+10, node.center[1], 'minecraft:gold_block')
                            self.state.built.add(node)  # add to built in order to avoid roads being placed before buildings placed
                            pass
                        return result
            i += 1
        return None
        # self.construction_site = construction_site


    def check_build_spot(self, ctrn_node, bld, bld_lenx, bld_lenz, wood_type):
        # check if theres adequate space by getting nodes, and move the building to center it if theres extra space
        # if not ctrn_node in self.construction: return
        # for every orientation of this node+neighbors whose lenx and lenz are the min space required to place building at
        min_nodes_in_x = ceil(bld_lenx / ctrn_node.size)
        min_nodes_in_z = ceil(bld_lenz / ctrn_node.size)
        min_tiles = min_nodes_in_x * min_nodes_in_z
        found_ctrn_dir = None
        found_nodes = set()
        # get rotation based on neighboring road
        found_road = None
        face_dir = None
        for dir in src.movement.cardinals:  # maybe make this cardinal only
            nx = ctrn_node.center[0] + dir[0] * ctrn_node.size
            nz = ctrn_node.center[1] + dir[1] * ctrn_node.size
            if self.state.out_of_bounds_Node(nx, nz): continue
            np = (nx, nz)
            neighbor = self.state.nodes[self.state.node_pointers[np]]
            if neighbor in self.state.roads:
                found_road = neighbor
                face_dir = dir
            if neighbor in self.state.built:
                return None                     # don't put buildings right next to each other
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
        for dir in src.movement.diagonals:
            if found_ctrn_dir != None:
                break
            tiles = 0
            for x in range(0, min_nodes_in_x):
                for z in range(0, min_nodes_in_z):
                    # x1 = ctrn_node.center[0]+x*ctrn_node.size*dir[0]
                    # z1 = ctrn_node.center[1]+z*ctrn_node.size*dir[1]
                    nx = ctrn_node.center[0] + x * ctrn_node.size * dir[0]
                    nz = ctrn_node.center[1] + z * ctrn_node.size * dir[1]
                    if self.state.out_of_bounds_Node(nx, nz): break
                    node = self.state.nodes[(nx, nz)]
                    if not node in self.state.construction: break
                    if node in self.state.roads: break  # don't go over roads
                    if node in self.state.built: break  # don't build over buildings
                    for tile in node.get_tiles():
                        # src.states.set_state_block(self.state, tile[0], self.state.rel_ground_hm[tile[0]][tile[1]] + 3, tile[1], 'minecraft:netherite')
                        if tile in self.state.water: continue
                    tiles += 1
                    found_nodes.add(node)
            if tiles == min_tiles:  # found a spot!
                found_ctrn_dir = dir
                break
            else:
                found_nodes.clear()
        if found_ctrn_dir == None:  # if there's not enough space, return
            return None


        ctrn_dir = found_ctrn_dir
        return (found_road, ctrn_node, found_nodes, ctrn_dir, bld, rot, min_nodes_in_x, min_nodes_in_z, self.state.built, wood_type)


    def do_build_task(self, found_road, ctrn_node, found_nodes, ctrn_dir, bld, rot, min_nodes_in_x, min_nodes_in_z, built_arr, wood_type):
        x1 = ctrn_node.center[0] - ctrn_dir[0]  # to uncenter
        z1 = ctrn_node.center[1] - ctrn_dir[1]
        x2 = ctrn_node.center[0] + ctrn_dir[0] + ctrn_dir[0] * ctrn_node.size * (min_nodes_in_x - 1)
        z2 = ctrn_node.center[1] + ctrn_dir[1] + ctrn_dir[1] * ctrn_node.size * (min_nodes_in_z - 1)
        xf = min(x1, x2)  # since the building is placed is ascending
        zf = min(z1, z2)
        # find lowest y
        lowest_y = self.state.rel_ground_hm[ctrn_node.center[0]][ctrn_node.center[1]]
        radius = math.ceil(ctrn_node.size / 2)
        for node in found_nodes.union({ctrn_node}):
            for x in range(-radius, radius + 1):
                for z in range(-radius, radius + 1):
                    nx = node.center[0] + x
                    nz = node.center[1] + z
                    if self.state.out_of_bounds_Node(nx, nz): continue
                    by = self.state.rel_ground_hm[nx][nz]
                    if by < lowest_y:
                        lowest_y = by
        y = lowest_y  # This should be the lowest y in the
        status, building_heightmap, exterior_heightmap = src.scheme_utils.place_schematic_in_state(self.state, bld, xf, y, zf,
                                                                                                   rot=rot,
                                                                                                   built_arr=self.state.built,
                                                                                                   wood_type=wood_type)
        if status == False:
            for node in found_nodes.union({ctrn_node}):
                self.state.built.remove(node)  # since this was set early in check_build_spot, remove it
            return False
        self.state.built_heightmap.update(building_heightmap)
        self.state.exterior_heightmap.update(exterior_heightmap)
        # build road from the road to the building
        self.state.create_road(found_road.center, ctrn_node.center, road_type="None", points=None, leave_lot=False,
                         add_as_road_type=False)
        xmid = int((x2 + x1) / 2)
        zmid = int((z2 + z1) / 2)
        distmax = dist((ctrn_node.center[0] - ctrn_dir[0], ctrn_node.center[1] - ctrn_dir[1]), (xmid, zmid))
        # build construction site ground
        for n in found_nodes:
            # for each of the nodes' tiles, generate random, based on dist. Also, add it to built.
            for dir in src.movement.idirections:
                x = n.center[0] + dir[0]
                z = n.center[1] + dir[1]
                # add to built
                y = int(self.state.rel_ground_hm[x][z]) - 1
                inv_chance = dist((x, z), (xmid, zmid)) / distmax  # clamp to 0-1
                if inv_chance == 1.0:  # stylistic choice: don't let corners be placed
                    continue
                attenuate = 0.8
                if random() > inv_chance * attenuate:
                    block = choice(src.my_utils.ROAD_SETS['default'])
                    src.states.set_state_block(self.state, x, y, z, block)
        y = self.state.rel_ground_hm[xf][zf] + 5
        # debug
        # for n in found_nodes:
        #     x = n.center[0]
        #     z = n.center[1]
        #     y = self.state.rel_ground_hm[x][z] + 20
        #     src.states.set_state_block(self.state, x, y, z, "minecraft:iron_block")
        ## remove nodes from construction
        for node in list(found_nodes):
            if node in self.state.construction:
                self.state.construction.remove(node)
            self.state.built.add(node)
            for tile in node.get_tiles():  # remove trees & saplings if they're in build spot
                if tile in self.state.trees:
                    self.state.trees.remove(tile)
                    node.type = node.get_type()  # update Types to remove trees
                if tile in self.state.saplings:
                    self.state.saplings.remove(tile)
                    node.type = node.get_type()  # update Types to remove saplings
        return True

    def auto_motive(self):
        new_motive = self.calc_motive()
        print(self.name+"'s new motive is "+new_motive.name)
        self.set_motive(new_motive)


    def calc_motive(self):
        if self.unshared_resources['rest'] < self.rest_thresh:
            return self.Motive.REST
        elif self.unshared_resources['water'] < self.thirst_thresh:
            return self.Motive.WATER
        elif self.has_enough_to_build(self.state.phase):
            return self.Motive.BUILD
        else:
            actions = (self.Motive.LOGGING, self.Motive.REPLENISH_TREE)
            weights = (10, 1)
            choice = choices(actions, weights, k=1)
            return choice[0]


    def has_enough_to_build(self, phase):
        for res, amt in self.shared_resources.items():
            if phase == 1:
                if amt > self.state.build_minimum_phase_1:
                    self.building_material = res
                    return True
            elif phase == 2:
                if amt > self.state.build_minimum_phase_2:
                    self.building_material = res
                    return True
            elif phase == 3:
                if amt > self.state.build_minimum_phase_3:
                    self.building_material = res
                    return True
            else:
                return False


    def get_appropriate_build(self, phase):
        rp = '../../../schemes/'
        build = ''
        cost = 0 # TODO
        if phase == 1:
            pool = src.my_utils.STRUCTURES['decor'] + src.my_utils.STRUCTURES['small']
            build, cost = choice(pool)
        elif phase == 2:
            pool = src.my_utils.STRUCTURES['decor'] + src.my_utils.STRUCTURES['small'] + src.my_utils.STRUCTURES['med']
            build, cost = choice(pool)
        elif phase == 3:
            pool = src.my_utils.STRUCTURES['small'] + src.my_utils.STRUCTURES['med'] + src.my_utils.STRUCTURES['large']
            build, cost = choice(pool)
        else:
            print('error: incorrect phase')
            exit(1)
        return rp+build, cost


    # 3D movement is a stretch goal
    def move_self(self, new_x, new_z, state, walkable_heightmap):
        if new_x < 0 or new_z < 0 or new_x >= state.len_x or new_z >= state.len_z:
            print(self.name + " tried to move out of bounds!")
            return
        self.dx = (new_x - self.x) #& -1
        self.dz = (new_z - self.z) #& -1
        self.x = new_x
        self.z = new_z
        self.y = walkable_heightmap[new_x][new_z]


    def teleport(self, target_x, target_z, walkable_heightmap):
        if (target_x < 0 or target_z < 0 or target_x >= self.state.len_x or target_z >= self.state.len_z):
            print(self.name + " tried to move out of bounds!")
            return
        self.x = target_x
        self.z = target_z
        target_y = walkable_heightmap[target_x][target_z]
        self.y = target_y
        print(self.name + " teleported to "+str(target_x)+" "+str(target_y)+" "+str(target_z))


    def set_path(self, path):
        self.path = path


    def follow_path(self, state, walkable_heightmap):
        dx = dz = 0
        status = False
        if len(self.path) > 0:
            dx, dz = self.path.pop()
            self.move_self(dx, dz, state=state, walkable_heightmap=walkable_heightmap)
            self.turns_staying_still = 0
        else:
            if self.motive == self.Motive.REST.name:
                status = self.do_rest_task()
            if self.motive == self.Motive.WATER.name:
                status = self.do_water_task()
            if self.motive == self.Motive.BUILD.name:
                if self.build_params is None:
                    print("failed to get to build spot")
                else:
                    self.do_build_task(*self.build_params)
                status = self.do_idle_task()
            elif self.motive == self.Motive.LOGGING.name:
                status = self.do_log_task()
            elif self.motive == self.Motive.REPLENISH_TREE.name:
                status = self.do_replenish_tree_task()
            elif self.motive == self.Motive.IDLE.name:
                status = self.do_idle_task()
        if self.turns_staying_still > Agent.max_turns_staying_still and status is False:  # _move in random direction if still for too long
            print("stayed still too long and now moving!")
            nx = nz = 1
            found_open = False
            for dir in src.movement.directions:
                nx = self.x + dir[0]
                nz = self.z + dir[1]
                ny = self.state.rel_ground_hm[nx][nz]
                if ny < self.state.rel_ground_hm[self.x][self.z]:
                    found_open = True
                    break
            if not found_open:
                nx, nz = choice(src.movement.directions)
            self.move_self(nx, nz, state=state, walkable_heightmap=walkable_heightmap)
            self.turns_staying_still = 0
        if dx == 0 and dz == 0:
            self.turns_staying_still += 1


            
    def do_replenish_tree_task(self):
        def is_in_state_saplings(state, x, y, z):
            return (x,z) in state.saplings
        if self.tree_grow_iteration < self.tree_grow_iterations_max+self.tree_leaves_height - 1:
            status = self.collect_from_adjacent_spot(self.state, check_func=is_in_state_saplings, manip_func=src.manipulation.grow_tree_at, prosperity_inc=src.my_utils.ACTION_PROSPERITY.REPLENISH_TREE)
            self.tree_grow_iteration+=1
            if status == src.manipulation.TASK_OUTCOME.FAILURE.name:
                self.tree_grow_iteration = 999   # so that they can go into else loop next run
            return True
        else:
            self.tree_grow_iteration = 0
            saps = set(self.state.saplings)
            for dir in src.movement.directions:  # remove sapling from state, add to trees instead
                x,z = (dir[0] + self.x, dir[1] + self.z)
                if self.state.out_of_bounds_2D(x,z): continue
                self.state.update_block_info(x,z)
                if (x,z) in saps:
                    self.state.saplings.remove((x,z))
                    # get log type
                    leaf = 'minecraft:oak_leaves'
                    if src.manipulation.is_log(self.state, x,self.state.rel_ground_hm[x][z], z):
                        log = self.state.blocks[x][self.state.rel_ground_hm[x][z]][z]
                        leaf = log[:-3] + "leaves[distance=7]"
                    # grow leaves there
                    # src.manipulation.grow_leaves(self.state, x, self.state.rel_ground_hm[x][z], z, 'minecraft:oak_leaves[distance=7]', leaves_height=self.tree_leaves_height)
                    src.manipulation.grow_leaves(self.state, x, self.state.rel_ground_hm[x][z], z, leaf, leaves_height=self.tree_leaves_height)
                if src.manipulation.is_log(self.state, x, self.state.rel_ground_hm[x][z]-1, z):
                    self.state.trees.append((x,z))
            self.set_motive(self.Motive.IDLE)
            return False


    def do_idle_task(self):
        self.auto_motive()
        return False


    def do_rest_task(self):
        if self.unshared_resources['rest'] < self.rest_max: # self.calc_motive() == self.Motive.REST:
            self.unshared_resources['rest'] += self.rest_inc_rate
            return True
        else:
            self.set_motive(self.Motive.IDLE)
            return False


    def do_water_task(self):
        print(self.name+"'s water is "+str(self.unshared_resources['water']))
        if self.unshared_resources['water'] < self.water_max:# and self.calc_motive() == self.Motive.WATER :
            # keep collecting water
            status = self.collect_from_adjacent_spot(self.state, check_func=src.manipulation.is_water, manip_func=src.manipulation.collect_water_at, prosperity_inc=src.my_utils.ACTION_PROSPERITY.WATER) # this may not inc an int
            print('status is '+status)
            if status == src.manipulation.TASK_OUTCOME.SUCCESS.name:
                print("collected water!")
                self.unshared_resources['water'] += self.water_inc_rate
                return True
            elif status == src.manipulation.TASK_OUTCOME.FAILURE.name:  # if no water found
                print("did not collect water!")
                self.set_motive(self.Motive.IDLE)
                return False
            return True  # in prograss
        else:
            print("idling from water")
            self.set_motive(self.Motive.IDLE)
            return True


    def do_log_task(self):
        status = self.collect_from_adjacent_spot(self.state, check_func=src.manipulation.is_log, manip_func=src.manipulation.cut_tree_at, prosperity_inc=src.my_utils.ACTION_PROSPERITY.LOGGING)
        if status == src.manipulation.TASK_OUTCOME.SUCCESS.name:
            src.agent.Agent.shared_resources['oak_log'] += 1
            print("finding another tree!")
            self.set_motive(self.Motive.IDLE)
            return True
        elif status == src.manipulation.TASK_OUTCOME.FAILURE.name:  # if they got sniped
            print("tree sniped")
            # udate this tree
            for dir in src.movement.idirections:
                point = (dir[0] + self.x, dir[1] + self.z)
                if point in self.state.trees:
                    self.state.trees.remove(point)
                if self.state.out_of_bounds_2D(*point): continue
                self.state.update_block_info(*point)
            self.set_motive(self.Motive.IDLE)
            return False
        else:
            # do nothing (continue logging)
            src.agent.Agent.shared_resources['oak_log'] += 1
            return True


    # prepares for motive
    def set_motive(self, new_motive : Enum):
        tree_search_radius = 10
        radius_increase = 5
        radius_increase_increments = 13
        self.motive = new_motive.name
        if self.motive in src.my_utils.AGENT_ITEMS:
            self.current_action_item = choice(src.my_utils.AGENT_ITEMS[self.motive])
        if new_motive.name == self.Motive.REST.name:
            self.set_path_to_nearest_spot(list(self.state.built_heightmap.keys()), 30, 10, 20, search_neighbors_instead=False)
        elif new_motive.name == self.Motive.WATER.name:
            self.set_path_to_nearest_spot(self.state.water, 10, 10, 20, search_neighbors_instead=True)
        elif new_motive.name == self.Motive.BUILD.name:
            building, cost = self.get_appropriate_build(self.state.phase)
            result = self.find_build_location(building, self.building_material[:-4])
            # now move to teh road
            if result != None:
                self.build_params = result
                tx, tz = result[0].center
                path = self.state.pathfinder.get_path((self.x, self.z), (tx, tz), self.state.len_x, self.state.len_z,
                                                                  self.state.legal_actions)
                self.build_cost = cost
                self.shared_resources[self.building_material] -= cost  # preemptively apply cost to avoid races
                self.set_path(path)
            else:
                # there are no build spots. so let's do something else
                self.set_motive(self.Motive.LOGGING)
        elif new_motive.name == self.Motive.LOGGING.name:
            self.set_path_to_nearest_spot(self.state.trees, 20, 10, 20, search_neighbors_instead=True)
            if len(self.path) < 1:  # if no trees were found
                self.set_motive(self.Motive.REPLENISH_TREE)
        elif new_motive.name == self.Motive.REPLENISH_TREE.name:
            self.set_path_to_nearest_spot(self.state.saplings, 15, 10, 20, search_neighbors_instead=True)
        elif new_motive.name == self.Motive.IDLE.name: # just let it go into follow_path
            pass


    def set_path_to_nearest_spot(self, search_array, starting_search_radius, max_iterations, radius_inc=1, search_neighbors_instead=True):
        closed = set()
        for i in range(max_iterations):
            spots = src.movement.find_nearest(self.x, self.z, search_array, starting_search_radius+radius_inc*i, 1, radius_inc)
            if spots is [] or spots is None: continue
            while len(spots) > 0:
                chosen_spot = choice(spots)
                spots.remove(chosen_spot)
                if chosen_spot in closed:
                    continue
                # see if theres a path to an adjacent tile
                if search_neighbors_instead == True:
                    for pos in src.movement.adjacents(self.state, *chosen_spot):
                        if self.state.sectors[pos[0], pos[1]] == self.state.sectors[self.x][self.z]:
                            path = self.state.pathfinder.get_path((self.x, self.z), pos, self.state.len_x, self.state.len_z, self.state.legal_actions)
                            self.set_path(path)
                            return
                    closed.add(chosen_spot)
                else:
                    if self.state.sectors[chosen_spot[0]][chosen_spot[1]] == self.state.sectors[self.x][self.z]:
                        path = self.state.pathfinder.get_path((self.x, self.z), (chosen_spot[0], chosen_spot[1]), self.state.len_x, self.state.len_z,
                                                              self.state.legal_actions)
                        self.set_path(path)
                        return
                    closed.add(chosen_spot)
        print(self.name+" could not find a spot!")
        self.set_path([])


    def collect_from_adjacent_spot(self, state, check_func, manip_func, prosperity_inc):
        status = src.manipulation.TASK_OUTCOME.FAILURE.name
        for dir in src.movement.directions:
            xo, zo = dir
            bx = self.x + xo
            bz = self.z + zo
            if self.state.out_of_bounds_Node(bx, bz):
                continue
            by = int(state.abs_ground_hm[bx][bz]) - self.state.world_y  # this isn't being updated in heightmap
            if check_func(self.state, bx, by, bz):
                status = manip_func(self.state, bx, by, bz)
                node = state.nodes[state.node_pointers[bx][bz]]
                node.add_prosperity(prosperity_inc)
                if status == src.manipulation.TASK_OUTCOME.SUCCESS.name or status == src.manipulation.TASK_OUTCOME.IN_PROGRESS.name:
                    break  # cut one at a time
                return src.manipulation.TASK_OUTCOME.SUCCESS.name
        return status  # someone sniped this tree.


    def render(self):
        # kill agent
        kill_cmd = """kill @e[name={name}]""".format(name = self.name)
        http_framework.interfaceUtils.runCommand(kill_cmd)
        spawn_cmd = """\
summon minecraft:armor_stand {x} {y} {z} {{NoGravity: 1, ShowArms:1, NoBasePlate:1, CustomNameVisible:1, Rotation:[{rot}f,0f,0f], \
mall:{is_small}, CustomName: '{{"text":"{name}", "color":"customcolor", "bold":false, "underlined":false, \
"strikethrough":false, "italic":false, "obscurated":false}}', \
ArmorItems:[{{id:"{boots}",Count:1b}},\
{{id:"{lower_armor}",Count:1b}},\
{{id:"{upper_armor}",Count:1b}},\
{{id:"player_head",Count:1b,tag:{{{head}}}}}],\
HandItems:[{{id:"{hand1}", Count:1b}},{{id:"{hand2}", Count:1b}}],\
Pose:{{Head:[{head_tilt}f,10f,0f], \
LeftLeg:[3f,10f,0f], \
RightLeg:[348f,18f,0f], \
LeftArm:[348f,308f,0f], \
RightArm:[348f,67f,0f]}}\
}}\
""".format(

            x=self.x+self.state.world_x,
            y=self.y+self.state.world_y,
            z=self.z+self.state.world_z,
            rot=src.my_utils.ROTATION_LOOKUP[max(min(self.dx, 1), -1, -1), max(min(self.dz, 1), -1)],
            name=self.name,
            is_small="false",
            head=self.head,
            boots="leather_boots",
            upper_armor="leather_chestplate",
            lower_armor="leather_leggings",
            hand1=self.current_action_item,
            hand2=self.favorite_item,
            head_tilt="350")  # this can be related to resources! 330 is high, 400 is low
        http_framework.interfaceUtils.runCommand(spawn_cmd)
