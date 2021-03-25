import block_manipulation
from states import *
from scipy.spatial import KDTree



class Agent:
    x = 0
    y = 0
    z = 0
    rendered_x = 0
    rendered_y = 0
    rendered_z = 0

    def __init__(self, state, state_x, state_z, walkable_heightmap, name, parent_1=None, parent_2=None, model="minecraft:carved_pumpkin"):
        self.x = state_x
        self.z = state_z
        self.y = walkable_heightmap[state_x][state_z]
        self.name = name
        self.parent_1 = parent_1
        self.parent_2 = parent_2
        self.model = model
        self.state = state

    # 3D movement is a stretch goal
    def move(self, x_off, z_off, state, walkable_heightmap):
        target_x = self.x + x_off
        target_z = self.z + z_off
        if (target_x < 0 or target_z < 0 or target_x >= state.len_x or target_z >= state.len_z):
            print(self.name + " tried to move out of bounds!")
            return
        self.x = target_x
        self.z = target_z
        self.y = walkable_heightmap[target_x][target_x]


    def update_pos_in_state(self, state : State):
        # remove from previous spot
        state.update_block(self.rendered_x, self.rendered_y, self.rendered_z, "minecraft:air")
        state.update_block(self.x, self.y, self.z, self.model)
        self.rendered_x = self.x
        self.rendered_y = self.y
        self.rendered_z = self.z
        print(self.name + " is now at y of " + str(self.y))


    def get_nearest_trees(self, starting_search_radius,max_iterations, radius_inc=1):
        if len(self.state.trees) <= 0: return
        T = KDTree(self.state.trees)
        for iteration in range(max_iterations):
            radius = starting_search_radius + iteration*radius_inc
            idx = T.query_ball_point([self.x, self.z], r=radius)
            if len(idx) > 0:
                result = []
                for i in idx:
                    result.append(self.state.trees[i])
                return result
        return []


    def teleport(self, target_x, target_z, walkable_heightmap):
        if (target_x < 0 or target_z < 0 or target_x >= self.state.len_x or target_z >= self.state.len_z):
            print(self.name + " tried to move out of bounds!")
            return
        self.x = target_x
        self.z = target_z
        target_y = walkable_heightmap[target_x][target_z]
        self.y = target_y
        print(self.name + " teleported to "+str(target_x)+" "+str(target_y)+" "+str(target_z))


    # def set_model(self, block):
    #     self.model = block
