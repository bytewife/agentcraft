from scipy.spatial import KDTree
from random import choice
from enum import Enum
import src.pathfinding
import src.states
import src.manipulation
import src.movement
import src.my_utils
import http_framework.interfaceUtils

class Agent:

    class Motive(Enum):
        LOGGING = 0
        BUILD = 1
        IDLE = 2
        WATER = 3
        REST = 4

    shared_resources = {
        "oak_log": 0,
        "dark_oak_log": 0,
        "spruce_log": 0,
        "birch_log": 0,
        "acacia_log": 0,
        "jungle_log": 0,
    }

    def __init__(self, state, state_x, state_z, walkable_heightmap, name, head,
                 parent_1=None, parent_2=None, model="minecraft:carved_pumpkin", motive=Motive.LOGGING.name):

        self.x = self.rendered_x = state_x
        self.z = self.rendered_z = state_z
        self.y = self.rendered_y = walkable_heightmap[state_x][state_z] + 0
        self.dx = self.dz = 1  # temp
        self.name = name
        self.parent_1 = parent_1
        self.parent_2 = parent_2
        self.model = model
        self.state = state
        self.path = []
        self.motive = motive
        self.current_action_item = ""
        self.favorite_item = ""
        self.head = head
        self.water_max = 100
        self.thirst_rate = -1 # lose this per turn
        self.thirst_thresh = 50
        self.rest_rate = -0.5
        self.rest_thresh = 30
        self.rest_max = 100
        self.unshared_resources = {
            "water": self.water_max * 0.49,
            "rest": self.rest_max * 0.49
        }


    def auto_motive(self):
        new_motive = self.calc_motive()
        print(self.name+"'s new motive is "+new_motive.name)
        self.set_motive(new_motive)


    def calc_motive(self):
        if self.unshared_resources['rest'] < self.rest_thresh:
            return self.Motive.REST
        if self.unshared_resources['water'] < self.thirst_thresh:
            return self.Motive.WATER
        else:
            return self.Motive.LOGGING


    # 3D movement is a stretch goal
    def move_self(self, new_x, new_z, state, walkable_heightmap):
        if new_x < 0 or new_z < 0 or new_x >= state.len_x or new_z >= state.len_z:
            print(self.name + " tried to move out of bounds!")
            return
        self.dx = new_x - self.x
        self.dz = new_z - self.z
        self.x = new_x
        self.z = new_z
        self.y = walkable_heightmap[new_x][new_z]


    def get_nearby_spots(self, search_array, starting_search_radius, max_iterations, radius_inc=1):
        return src.movement.find_nearest(self.x, self.z, search_array, starting_search_radius, max_iterations, radius_inc)


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
        if len(self.path) > 0:
            new_pos = self.path.pop()
            self.move_self(*new_pos, state=state, walkable_heightmap=walkable_heightmap)
        else:
            if self.motive == self.Motive.REST.name:
                self.do_rest_task()
            if self.motive == self.Motive.WATER.name:
                self.do_water_task()
            elif self.motive == self.Motive.LOGGING.name:
                self.do_log_task()


    def do_rest_task(self):
        if self.calc_motive() == self.Motive.REST and self.unshared_resources['rest'] < self.rest_max:
            # rest
            self.unshared_resources['rest'] += 4
        else:
            self.auto_motive()


    def do_water_task(self):
        print(self.name+"'s water is "+str(self.unshared_resources['water']))
        if self.calc_motive() == self.Motive.WATER and self.unshared_resources['water'] < self.water_max:
            # keep collecting water
            status = self.collect_from_adjacent_spot(self.state, check_func=src.manipulation.is_water, manip_func=src.manipulation.collect_water_at, prosperity_inc=src.my_utils.ACTION_PROSPERITY.WATER) # this may not inc an int
            print(status)
            if status == src.manipulation.TASK_OUTCOME.SUCCESS.name:
                self.unshared_resources['water'] += 7
                pass
            elif status == src.manipulation.TASK_OUTCOME.FAILURE.name:  # if no water found
                self.auto_motive()
        else:
            self.auto_motive()


    def do_log_task(self):
        status = self.collect_from_adjacent_spot(self.state, check_func=src.manipulation.is_log, manip_func=src.manipulation.cut_tree_at, prosperity_inc=src.my_utils.ACTION_PROSPERITY.LOGGING)
        if status == src.manipulation.TASK_OUTCOME.SUCCESS.name:
            src.agent.Agent.shared_resources['oak_log'] += 1
            print("finding another tree!")
            self.auto_motive()
        elif status == src.manipulation.TASK_OUTCOME.FAILURE.name:  # if they got sniped
            print("tree sniped")
            # udate this tree
            for dir in src.movement.directions:
                point = (dir[0] + self.x, dir[1] + self.z)
                if self.state.out_of_bounds_2D(*point): continue
                self.state.update_block_info(*point)
            self.auto_motive()
        else:
            # do nothing (continue logging)
            src.agent.Agent.shared_resources['oak_log'] += 1
            pass


    # prepares for motive
    def set_motive(self, new_motive : Enum):
        tree_search_radius = 10
        radius_increase = 5
        radius_increase_increments = 13
        self.motive = new_motive.name
        if self.motive in src.my_utils.ACTION_ITEMS:
            self.current_action_item = choice(src.my_utils.ACTION_ITEMS[self.motive])
        if new_motive.name == self.Motive.REST.name:
            self.set_path_to_nearest_spot(self.state.built_heightmap.keys(), 30, 10, 5, search_neighbors_instead=False)
        elif new_motive.name == self.Motive.WATER.name:
            self.set_path_to_nearest_spot(self.state.water, 15, 10, 5, search_neighbors_instead=True)
        elif new_motive.name == self.Motive.LOGGING.name:
            self.set_path_to_nearest_spot(self.state.trees, 15, 10, 5, search_neighbors_instead=True)


    def set_path_to_nearest_spot(self, search_array, starting_search_radius, max_iterations, radius_inc=1, search_neighbors_instead=True):
        closed = set()
        for i in range(max_iterations):
            spots = src.movement.find_nearest(self.x, self.z, search_array, starting_search_radius+radius_inc*i, 1, radius_inc)
            if spots is []: continue
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
        print("could not a spot!")
        self.auto_motive()


    def collect_from_adjacent_spot(self, state, check_func, manip_func, prosperity_inc):
        status = src.manipulation.TASK_OUTCOME.FAILURE.name
        for dir in src.movement.directions:
            xo, zo = dir
            bx = self.x + xo
            bz = self.z + zo
            if bx < 0 or bz < 0 or bx >= state.len_x-1 or bz >= state.len_z-1:
                continue
            by = int(state.abs_ground_hm[bx][bz]) - self.state.world_y  # this isn't being updated in heightmap
            if check_func(self.state, bx, by, bz):
                status = manip_func(self.state, bx, by, bz)
                state.nodes[state.node_pointers[bx][bz]].add_prosperity(prosperity_inc)
                if status == src.manipulation.TASK_OUTCOME.SUCCESS.name or status == src.manipulation.TASK_OUTCOME.IN_PROGRESS.name:
                    print("resources is now "+str(src.agent.Agent.shared_resources['oak_log']))
                    break  # cut one at a time
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
            rot=src.my_utils.ROTATION_LOOKUP[(self.dx, self.dz)],
            name=self.name,
            is_small="false",
            head=self.head,
            boots="leather_boots",
            upper_armor="leather_chestplate",
            lower_armor="leather_leggings",
            hand1=self.current_action_item,
            hand2="apple",
            head_tilt="350")  # this can be related to resources! 330 is high, 400 is low
        http_framework.interfaceUtils.runCommand(spawn_cmd)

    # def set_model(self, block):
    #     self.model = block
