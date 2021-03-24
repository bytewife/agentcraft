from src.http_framework.worldLoader import *
from src.http_framework.interfaceUtils import *
from my_utils import *

class State:

    tallest_building_height = 30
    changed_blocks = {}
    blocks = []  # 3D Array of all the blocks in the state
    top_heightmap = []
    walkable_heightmap = [] # TODO create function for this. Agents will be armor stands, and they can be updated in real time
    world_y = 0
    world_x = 0
    world_z = 0
    len_x = 0
    len_y = 0
    len_z = 0

    ## Create surface grid
    def __init__(self, world_slice:WorldSlice, max_y_offset=tallest_building_height):
        self.blocks, self.world_y, self.len_y, self.top_heightmap = self.create_blocks_array(world_slice)
        self.walkable_blocks = self.blocks  # eventually path find to find these
        self.types = self.create_types_array(self.blocks, self.top_heightmap)
        self.world_x = world_slice.rect[0]
        self.world_z = world_slice.rect[1]
        self.len_x = world_slice.rect[2] - world_slice.rect[0]
        self.len_z = world_slice.rect[3] - world_slice.rect[1]

    def create_blocks_array(self, world_slice:WorldSlice, max_y_offset=tallest_building_height):
        x1, z1, x2, z2 = world_slice.rect
        state_heightmap = world_slice.get_heightmap("MOTION_BLOCKING_NO_LEAVES", -1) # inclusive of ground
        def get_y_bounds(_heightmap):  ## Get the y range that we'll save tha state in?
            lowest = 99
            highest = 0
            for col in _heightmap:
                for block_y in col:
                    if (block_y < lowest):
                        lowest = block_y
                    elif (block_y > highest):
                        highest = block_y
            return lowest, highest
        y1, y2  = get_y_bounds(state_heightmap)  # keep range not too large
        y2 += max_y_offset

        len_z = abs(z2 - z1)
        len_y = abs(y2 - y1)
        len_x = abs(x2 - x1)
        blocks = [[[0 for z in range(len_z)] for y in range(len_y)] for x in range(len_x)] # the format of the state isn't the same as the file's.
        xi = 0
        yi = 0
        zi = 0
        for x in range(x1, x2):
            yi *= 0
            for y in range(y1, y2):
                zi *= 0
                for z in range(z1, z2):
                    block = world_slice.getBlockAt((x, y, z))
                    blocks[xi][yi][zi] = block
                    zi += 1
                yi += 1
            xi += 1
        state_y = y1
        len_y = y2 - y1
        return blocks, state_y, len_y, state_heightmap


    def create_types_array(self, blocks, heightmap):
        types = []
        for x in range(len(blocks)):
            types.append([])
            for z in range(len(blocks[0][0])):
                block_y = heightmap[x][z] - self.world_y
                block = blocks[x][block_y][z]
                type = self.determine_types(block)
                types[x].append(type)
        print("done initializing types")
        return types


    def determine_types(self, block):
        for i in range(1, len(Type)+1):
            if block in Type_Tiles.tile_sets[i]:
                return Type(i).name
        # print(block)
        return Type.AIR.name



    def mark_changed_blocks(self, state_x, state_y, state_z, block_name):
        key = convert_coords_to_key(state_x, state_y, state_z)
        self.changed_blocks[key] = block_name


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
            state_x, state_y, state_z = convert_key_to_coords(position_raw)
            placeBlockBatched(self.world_x + state_x, self.world_y + state_y, self.world_z + state_z, block, n_blocks)
            i += 1
        f.close()
        self.changed_blocks.clear()
        print(str(i)+" blocks loaded")


    def render(self):
        i = 0
        n_blocks = len(self.changed_blocks)
        for position, block in self.changed_blocks.items():
            state_x, state_y, state_z = convert_key_to_coords(position)
            block = block
            placeBlockBatched(self.world_x + state_x, self.world_y + state_y, self.world_z + state_z, block, n_blocks)
            i += 1
        self.changed_blocks.clear()
        print(str(i)+" blocks rendered")


    ## do we wanna cache tree locations? I don't want them to cut down buildings lol
    def is_log(self, x, y, z):
        block = self.blocks[x][y][z]
        if block[-3:] == 'log':
            return True
        return False


    ## assumes there's a tree at the location
    def cut_tree_at(self, x, y, z, times=1):
        for i in range(times):
            log_type = self.get_log_type(self.blocks[x][y][z])
            replacement = "minecraft:air"
            self.blocks[x][y][z] = replacement
            self.mark_changed_blocks(x, y, z, replacement)
            if \
            self.is_leaf(self.get_adjacent_block(x, y, z, 0, 1, 0)) or \
            self.is_leaf(self.get_adjacent_block(x, y, z, 1, 0, 0)
            ):
                self.trim_leaves(x, y+1, z)
            if not self.is_log(x, y-1, z):  # place sapling
                sapling = "minecraft:"+log_type+"_sapling"
                self.blocks[x][y][z] = sapling
                self.mark_changed_blocks(x, y, z, sapling)
            y-=1


    def get_adjacent_block(self, x_origin, y_origin, z_origin, x_off, y_off, z_off):
        x_target = x_origin + x_off
        y_target = y_origin + y_off
        z_target = z_origin + z_off
        if x_target >= len(self.blocks) or y_target >= len(self.blocks[0]) or z_target >= len(self.blocks[0][0]):
            #TODO this might lead to clipping
            print("Cannot check for block out of state bounds")
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


    def perform_on_adj_recursively(self, x, y, z, target_block_checker, recur_func, forward_call):
        forward_call(self.blocks, x, y, z)
        adj_blocks = self.get_all_adjacent_blocks(x, y, z)
        for block in adj_blocks:
            if target_block_checker(block[0]):
                recur_func(block[1], block[2], block[3], target_block_checker, recur_func, forward_call)


    def trim_leaves(self, leaf_x, leaf_y, leaf_z):
        def leaf_to_air(blocks, x, y, z):
            blocks[x][y][z] = 'minecraft:air'
            self.mark_changed_blocks(x, y, z, 'minecraft:air')
        self.perform_on_adj_recursively(leaf_x, leaf_y, leaf_z,self.is_leaf,self.perform_on_adj_recursively,leaf_to_air)


    def is_leaf(self, block_name):
        if block_name[-6:] == 'leaves':
            return True
        return False


    def get_log_type(self, block_name):
        return block_name[10:-4]
