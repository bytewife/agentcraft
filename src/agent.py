import block_manipulation
from states import *



class Agent:
    x = 0
    y = 0
    z = 0
    rendered_x = 0
    rendered_y = 0
    rendered_z = 0

    def __init__(self, state_x, state_z, walkable_heightmap, name, parent_1=None, parent_2=None, model="minecraft:carved_pumpkin"):
        self.x = state_x
        self.z = state_z
        self.y = walkable_heightmap[state_x][state_z]
        self.name = name
        self.parent_1 = parent_1
        self.parent_2 = parent_2
        self.model = model

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
        state.mark_changed_blocks(self.rendered_x, self.rendered_y, self.rendered_z, "minecraft:air")
        state.mark_changed_blocks(self.x, self.y, self.z, self.model)
        self.rendered_x = self.x
        self.rendered_y = self.y
        self.rendered_z = self.z
        print(self.name + " is now at y of " + str(self.y))


    # def set_model(self, block):
    #     self.model = block
