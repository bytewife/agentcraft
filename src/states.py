import http_framework.interfaceUtils
import http_framework.worldLoader
import src.my_utils
import src.movement
import src.pathfinding
import src.scheme_utils

class State:

    tallest_building_height = 30
    changed_blocks = {}
    blocks = []  # 3D Array of all the blocks in the state
    abs_ground_hm = []
    rel_ground_hm = [] # TODO create function for this. Agents will be armor stands, and they can be updated in real time
    trees = []
    world_y = 0
    world_x = 0
    world_z = 0
    len_x = 0
    len_y = 0
    len_z = 0
    unwalkable_blocks = []
    agent_height = 2
    agent_jump_ability = 2
    heightmap_offset = -1

    ## Create surface grid
    def __init__(self, world_slice=None, blocks_file=None, max_y_offset=tallest_building_height):
        if not world_slice is None:
            self.blocks, self.world_y, self.len_y, self.abs_ground_hm = self.gen_blocks_array(world_slice)
            self.rel_ground_hm = self.gen_rel_ground_hm(self.abs_ground_hm)  # a heightmap based on the state's y values. -1
            self.heightmaps = world_slice.heightmaps
            self.types = self.gen_types("MOTION_BLOCKING")  # 2D array. Include leaves
            self.world_x = world_slice.rect[0]
            self.world_z = world_slice.rect[1]
            self.len_x = world_slice.rect[2] - world_slice.rect[0]
            self.len_z = world_slice.rect[3] - world_slice.rect[1]
            self.legal_actions = src.movement.gen_all_legal_actions(
                self.blocks, 2, self.rel_ground_hm, self.agent_jump_ability, []
            )
            self.pathfinder = src.pathfinding.Pathfinding()
            self.pathfinder.create_sectors(self.heightmaps["MOTION_BLOCKING_NO_LEAVES"],
                                            self.legal_actions)  # add tihs into State

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
            self.len_x, self.len_y, self.len_z, self.blocks = parse_blocks_file(blocks_file)


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
        x1, z1, x2, z2 = world_slice.rect
        abs_ground_hm = world_slice.get_heightmap("MOTION_BLOCKING_NO_LEAVES", -1) # inclusive of ground
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
        y1, y2  = get_y_bounds(abs_ground_hm)  # keep range not too large
        y2 += max_y_offset
        if (y2 > 150):
            print("warning: Y bound is really high!")

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
        world_y = y1
        len_y = y2 - y1
        return blocks, world_y, len_y, abs_ground_hm


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
        #         new_type = "FOREST"
        self.types[x][z] = new_type


    ## hope this isn't too expensive. may need to limit area if it is
    def update_heightmaps(self, x, z):
        x_to = x + 1
        z_to = z + 1
        area = [x + self.world_x, z + self.world_z, x_to + self.world_x, z_to + self.world_z]
        area = src.my_utils.correct_area(area)
        worldSlice = http_framework.worldLoader.WorldSlice(area)
        for index in range(1,len(worldSlice.heightmaps)+1):
            name = src.my_utils.Heightmaps(index).name
            new_y = int(worldSlice.heightmaps[name][0][0]) - 1
            self.heightmaps[name][x][z] = new_y
        hm_base = self.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
        for x in range(len(hm_base)):
            for z in range(len(hm_base[0])):
                state_adjusted_y = int(hm_base[x][z])
                self.abs_ground_hm[x][z] = state_adjusted_y
        # self.abs_ground_hm[x][z] = self.heightmaps["MOTION_BLOCKING_NO_LEAVES"][x][z]
        self.rel_ground_hm = self.gen_rel_ground_hm(self.abs_ground_hm)


    def gen_types(self, heightmap_name):
        types = []
        for x in range(len(self.blocks)):
            types.append([])
            for z in range(len(self.blocks[0][0])):
                type = self.determine_type(x, z, heightmap_name)
                if type == "TREE":
                    self.trees.append((x, z))
                types[x].append(type)
        print("done initializing types")
        return types


    def determine_type(self, x, z, heightmap_name="MOTION_BLOCKING_NO_LEAVES"):
        block_y = self.heightmaps[heightmap_name][x][z] - self.world_y + self.heightmap_offset
        block = self.blocks[x][block_y][z]
        for i in range(1, len(src.my_utils.Type)+1):
            if block in src.my_utils.Type_Tiles.tile_sets[i]:
                return src.my_utils.Type(i).name
        return src.my_utils.Type.AIR.name




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
            state_x, state_y, state_z = src.my_utils.convert_key_to_coords(position_raw)
            http_framework.interfaceUtils.placeBlockBatched(
                self.world_x + state_x, self.world_y + state_y, self.world_z + state_z, block, n_blocks
            )
            i += 1
        f.close()
        self.changed_blocks.clear()
        print(str(i)+" blocks loaded")


    def render(self):
        i = 0
        n_blocks = len(self.changed_blocks)
        for position, block in self.changed_blocks.items():
            state_x, state_y, state_z = src.my_utils.convert_key_to_coords(position)
            block = block
            http_framework.interfaceUtils.placeBlockBatched(self.world_x + state_x, self.world_y + state_y, self.world_z + state_z, block, n_blocks)
            i += 1
            self.update_block_info(state_x, state_y, state_z)  # Must occur after new blocks have been placed

        self.changed_blocks.clear()
        print(str(i)+" blocks rendered")


    ## do we wanna cache tree locations? I don't want them to cut down buildings lol


    # is this state x
    def update_block_info(self, x, y, z):  # this might be expensive if you use this repeatedly in a group
        self.update_heightmaps(x, z)
        for xo in range(-1, 2):
            for zo in range(-1, 2):
                bx = x + xo
                bz = z + zo
                if self.out_of_bounds_2D(bx, bz):
                    continue
                print(self.rel_ground_hm)
                self.legal_actions[bx][bz] = src.movement.get_legal_actions_from_block(self.blocks, bx, bz, self.agent_jump_ability,
                                                                                   self.rel_ground_hm, self.agent_height,
                                                                                   self.unwalkable_blocks)
        self.pathfinder.update_sector_for_block(x, z, self.pathfinder.sectors,
                                                sector_sizes=self.pathfinder.sector_sizes,
                                                legal_actions=self.legal_actions)


    def get_adjacent_block(self, x_origin, y_origin, z_origin, x_off, y_off, z_off):
        x_target = x_origin + x_off
        y_target = y_origin + y_off
        z_target = z_origin + z_off
        if self.out_of_bounds_3D(x_target, y_target, z_target):
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


    def world_to_state(self,coords):
        x = coords[0] - self.world_x
        z = coords[2] - self.world_z
        y = self.rel_ground_hm[x][z]
        result = (x,y,z)
        return result


    def out_of_bounds_3D(self, x, y, z):
        return True if \
            x >= len(self.blocks) \
            or y >= len(self.blocks[0]) \
            or z >= len(self.blocks[0][0]) \
            else False


    def out_of_bounds_2D(self, x, z):
        return True if x < 0 or z < 0 or x >= len(self.blocks) or z >= len(self.blocks[0][0]) \
            else False




