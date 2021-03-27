from scipy.spatial import KDTree
from random import choice
from enum import Enum
import src.pathfinding
import src.states
import src.manipulation
import src.movement

class Agent:
    x = 0
    y = 0
    z = 0
    rendered_x = 0
    rendered_y = 0
    rendered_z = 0

    class Motive(Enum):
        LOGGING = 0
        BUILD = 1

    def __init__(self, state, state_x, state_z, walkable_heightmap, name,
                 parent_1=None, parent_2=None, model="minecraft:carved_pumpkin", motive=Motive.LOGGING.name):
        self.x = state_x
        self.z = state_z
        self.y = walkable_heightmap[state_x][state_z]
        self.name = name
        self.parent_1 = parent_1
        self.parent_2 = parent_2
        self.model = model
        self.state = state
        self.path = []
        self.motive = motive

    # 3D movement is a stretch goal
    def move_self(self, new_x, new_z, state, walkable_heightmap):
        if new_x < 0 or new_z < 0 or new_x >= state.len_x or new_z >= state.len_z:
            print(self.name + " tried to move out of bounds!")
            return
        self.x = new_x
        self.z = new_z
        self.y = walkable_heightmap[new_x][new_z]


    def move_in_state(self, state : src.states.State):
        # remove from previous spot
        src.manipulation.set_state_block(self.state, self.rendered_x, self.rendered_y, self.rendered_z, "minecraft:air")
        src.manipulation.set_state_block(self.state, self.x, self.y, self.z, self.model)
        self.rendered_x = self.x
        self.rendered_y = self.y
        self.rendered_z = self.z
        print(self.name + " is now at y of " + str(self.y))


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
        if len(self.path) <= 0:
            if self.motive == self.Motive.LOGGING.name:
                print(self.name + " has finished their path and is now cutting.")
                status = self.log_adjacent_tree()
                if status == src.manipulation.TaskOutcome.SUCCESS:
                    return
                else:
                    return
        else:
            new_pos = self.path.pop()
            self.move_self(*new_pos, state=state, walkable_heightmap=walkable_heightmap)


    def set_motive(self, new_motive : Enum):
        tree_search_radius = 10
        radius_increase = 10
        radius_increase_increments = 10
        self.motive = new_motive.name
        if new_motive.name == self.Motive.LOGGING.name:
            closed = set()
            for inc in range(radius_increase_increments):
                trees = self.get_nearby_trees(starting_search_radius=tree_search_radius,
                                              radius_inc=radius_increase,
                                              max_iterations=1)
                while len(trees) > 0:
                    chosen_tree = choice(trees)
                    trees.remove(chosen_tree)
                    if chosen_tree in closed:
                        continue
                    # see if theres a path to an adjacent tile
                    for pos in src.movement.adjacents(self.state, *chosen_tree):
                        if self.state.pathfinder.sectors[pos[0], pos[1]] ==   \
                        self.state.pathfinder.sectors[self.x][self.z]:
                            path = self.state.pathfinder.get_path((self.x, self.z), pos, 31, 31, self.state.legal_actions)
                            if path == []:
                                print(self.name + " could not find a tree!")
                                self.set_motive(self.Motive.BUILD)
                            else:
                                self.set_path(path)
                                return
                    closed.add(chosen_tree)


    def log_adjacent_tree(self):
        status = src.manipulation.TaskOutcome.FAILURE.name
        for dir in src.movement.directions:
            xo, zo = dir
            bx = self.x + xo
            bz = self.z + zo
            if bx < 0 or bz < 0 or bx >= len(self.state.blocks) or bz >= len(self.state.blocks[0][0]):
                continue
            by = self.state.abs_ground_hm[bx, bz] - self.state.world_y
            if src.manipulation.is_log(self.state, bx, by, bz):
                status = src.manipulation.cut_tree_at(self.state, bx, by, bz)
            return status  # someone sniped this tree.

    # def set_model(self, block):
    #     self.model = block
