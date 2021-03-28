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

    def __init__(self, state, state_x, state_z, walkable_heightmap, name,
                 parent_1=None, parent_2=None, model="minecraft:carved_pumpkin", motive=Motive.LOGGING.name):

        self.x = self.rendered_x = state_x
        self.z = self.rendered_z = state_z
        self.y = self.rendered_y = walkable_heightmap[state_x][state_z] + 1
        self.name = name
        self.parent_1 = parent_1
        self.parent_2 = parent_2
        self.model = model
        self.state = state
        self.path = []
        self.motive = motive
        self.x = 0
        self.y = 0
        self.z = 0
        self.rendered_x = 0
        self.rendered_y = 0
        self.rendered_z = 0
        self.current_action_item = ""
        self.favorite_item = ""


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


    def get_nearby_trees(self, starting_search_radius, max_iterations, radius_inc=1):
        return src.movement.find_nearest(self.x, self.z, self.state.trees, starting_search_radius, max_iterations, radius_inc)


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
        if len(self.path) < 1:
            if self.motive == self.Motive.LOGGING.name:
                print(self.name + " has finished their path and is now cutting.")
                status = self.log_adjacent_tree(state)
                if status == src.manipulation.TaskOutcome.SUCCESS:
                    print("done!")
                    return
                else:
                    return
        else:
            new_pos = self.path.pop()
            self.move_self(*new_pos, state=state, walkable_heightmap=walkable_heightmap)


    def set_motive(self, new_motive : Enum):
        print(self.state.sectors)
        tree_search_radius = 10
        radius_increase = 10
        radius_increase_increments = 10
        self.motive = new_motive.name
        self.current_action_item = choice(src.my_utils.ACTION_ITEMS[self.motive])
        if new_motive.name == self.Motive.LOGGING.name:
            closed = set()
            for inc in range(radius_increase_increments):
                trees = self.get_nearby_trees(starting_search_radius=tree_search_radius,
                                              radius_inc=radius_increase,
                                              max_iterations=1)
                if trees is None: continue
                while len(trees) > 0:
                    chosen_tree = choice(trees)
                    trees.remove(chosen_tree)
                    if chosen_tree in closed:
                        continue
                    # see if theres a path to an adjacent tile
                    for pos in src.movement.adjacents(self.state, *chosen_tree):
                        if self.state.sectors[pos[0], pos[1]] ==   \
                        self.state.sectors[self.x][self.z]:
                            path = self.state.pathfinder.get_path((self.x, self.z), pos, 31, 31, self.state.legal_actions)
                            self.set_path(path)
                            return
                    closed.add(chosen_tree)
            print("could not find trees!")
            exit(1)


    def log_adjacent_tree(self, state):
        status = src.manipulation.TaskOutcome.FAILURE.name
        for dir in src.movement.directions:
            xo, zo = dir
            bx = self.x + xo
            bz = self.z + zo
            if bx < 0 or bz < 0 or bx >= len(self.state.blocks) or bz >= len(self.state.blocks[0][0]):
                continue
            by = int(state.abs_ground_hm[bx][bz]) - self.state.world_y  # this isn't being updated in heightmap
            print("BY_IS")
            print(by)
            if src.manipulation.is_log(self.state, bx, by, bz):
                status = src.manipulation.cut_tree_at(self.state, bx, by, bz)
                break  # cut one at a time
        return status  # someone sniped this tree.


    def render(self):
        # kill agent
        kill_cmd = """kill @e[name={name}]""".format(name = self.name)
        http_framework.interfaceUtils.runCommand(kill_cmd)
        spawn_cmd = """\
summon minecraft:armor_stand {x} {y} {z} {{ShowArms:1, NoBasePlate:1, CustomNameVisible:1, Rotation:[{rot}f,0f,0f], \
Small:{is_small}, CustomName: '{{"text":"{name}", "color":"customcolor", "bold":false, "underlined":false, \
"strikethrough":false, "italic":false, "obscurated":false}}', \
ArmorItems:[{{id:"{boots}",Count:1b}},\
{{id:"{lower_armor}",Count:1b}},\
{{id:"{upper_armor}",Count:1b}},\
{{id:"player_head",Count:1b,tag:{{SkullOwner:{{Id:"401c89f6-384e-473d-b448-1c73a342aed9",Properties:{{textures:[{{Value:"eyJ0ZXh0dXJlcyI6eyJTS0lOIjp7InVybCI6Imh0dHA6Ly90ZXh0dXJlcy5taW5lY3JhZnQubmV0L3RleHR1cmUvOTVhZWY4ZDczYzZiM2I5N2Q3YjU3MTZmY2EyMTVmNWViYTY3OTkyMTJkMTFlYjYzZTE1ODg5NDBkMWUyMWI3MyJ9fX0="}}]}}}}}}}}],\
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
            boots="leather_boots",
            upper_armor="leather_chestplate",
            lower_armor="leather_leggings",
            hand1=self.current_action_item,
            hand2="apple",
            head_tilt="350")  # this can be related to resources! 330 is high, 400 is low
        print(http_framework.interfaceUtils.runCommand(spawn_cmd))

    # def set_model(self, block):
    #     self.model = block
