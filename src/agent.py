import block_manipulation



class Agent:
    x = 0
    y = 0
    z = 0

    def __init__(self, name, state_x, state_y, state_z, parent_1, parent_2):
        self.name = name
        self.x = state_x
        self.y = state_y
        self.z = state_z
        self.parent_1 = parent_1
        self.parent_2 = parent_2

    # 3D movement is a stretch goal
    def move_2d(self, x_off, z_off):
        self.x += x_off
        self.z += z_off
