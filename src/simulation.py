#! /usr/bin/python3
"""
### Simulation
Simulations contain and modify data regarding the execution of the State and the generator.
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"

import src.agent
import src.states
import src.utils
import http_framework.worldLoader
import http_framework.interfaceUtils
import time
import random
import numpy as np
import src.chronicle
import wonderwords
import run


class Simulation:

    def __init__(self, XZXZ, precomp_world_slice=None, precomp_legal_actions=None, precamp_pathfinder=None,
                 precomp_types=None, run_start=True, precomp_sectors=None, precomp_nodes=None,
                 precomp_node_pointers=None, phase=0, maNum=5, miNum=400, byNum=2000, brNum=1000, buNum=10, pDecay=0.98,
                 tDecay=0.25, corNum=5, times=1, is_rendering_each_step=True, rendering_step_duration=0.8,
                 building_max_y_diff=1, start_time=0):
        if precomp_world_slice == None:
            self.world_slice = http_framework.worldLoader.WorldSlice(*XZXZ)
        else:
            self.world_slice = precomp_world_slice
        self.state = src.states.State(XZXZ, self.world_slice, precomp_pathfinder=precamp_pathfinder,
                                      precomp_legal_actions=precomp_legal_actions, precomp_types=precomp_types,
                                      precomp_sectors=precomp_sectors, precomp_nodes=precomp_nodes,
                                      precomp_node_pointers=precomp_node_pointers)
        self.maNum = maNum
        self.miNum = miNum
        self.byNum = byNum
        self.brNum = brNum
        self.buNum = buNum
        self.pDecay = pDecay
        self.tDecay = tDecay
        self.corNum = corNum
        self.times = times
        self.is_rendering_each_step = is_rendering_each_step
        self.rendering_step_duration = rendering_step_duration
        self.phase = phase
        self.prosperity = 0
        self.building_max_y_diff = 1
        self.building_max_y_diff_tries = 0
        self.chronicles_pos = None
        self.settlement_name = str.capitalize(
            src.chronicle.WORD_PICKER.random_words(include_parts_of_speech=['nouns'])[0]) + random.choice(
            ['town', 'bottom', 'land', 'dom', 'fields', 'lot', 'valley', ' Heights'])
        self.original_agent = None
        self.settlement_pos = None

        # parse heads
        f = open("./assets/agent_heads.out.txt")
        agent_heads = f.readlines()
        agent_heads = [h.rstrip('\n') for h in agent_heads]
        src.states.State.AGENT_HEADS = agent_heads
        f.close()

        if run_start:
            clean_agents = "kill @e[type=minecraft:armor_stand,x={},y=64,z={},distance=..100]".format(
                str((XZXZ[2] + XZXZ[0]) / 2),
                str((XZXZ[3] + XZXZ[1]) / 2))
            http_framework.interfaceUtils.runCommand(clean_agents)

    def run_with_render(self, steps, start, time_limit, is_writing_sign):
        """
        Execute simulation for given steps while rendering at each iteration
        :param steps:
        :param start:
        :param time_limit:
        :param is_writing_sign:
        :return:
        """
        is_writing = run.IS_WRITING_CHRONICLE_TO_CONSOLE
        run.IS_WRITING_CHRONICLE_TO_CONSOLE = False
        self.get_max_building_dy()
        viable_water_starts = list(set(self.state.water).intersection(self.state.blocks_near_land))
        max_tries = 99
        status, attempt = self.start(viable_water_starts, -1, max_tries)
        while status == False:
            self.state.reset()
            self.update_building_max_dy()
            status, attempt = self.start(viable_water_starts, attempt, max_tries)
            if attempt > max_tries:
                print(
                    "Error: could not find valid settlement location in given area! Try running with a different area.")
                exit(1)
            attempt += 1
        run.IS_WRITING_CHRONICLE_TO_CONSOLE = is_writing
        finished_fully, times, steps = self.step(steps - 1, True, start, time_limit)
        x = self.chronicles_pos[0]
        z = self.chronicles_pos[1]
        y = self.state.rel_ground_hm[x][z]
        finished_fully = self.step(1, True, start, time_limit)
        http_framework.interfaceUtils.runCommand(
            f'setblock {x + self.state.world_x} {y + self.state.world_y} {z + self.state.world_z} minecraft:chest')
        src.chronicle.place_chronicles(self.state, x, y, z, f"History of {self.settlement_name}",
                                       self.original_agent.name)
        print("Simulation finished after " + str(time.time() - start) + " seconds. " + str(
            steps + 1) + " steps performed, out of " + str(times + 1) + " steps.")
        cx = self.state.world_x + x
        cz = self.state.world_z + z
        print(f"Chronicles placed at {cx}, {self.state.world_y + y}, {cz}! ")
        if is_writing_sign:
            sx = int(self.state.world_x + self.state.len_x / 2)
            sz = int(self.state.world_z + self.state.len_z / 2)
            sy = self.state.world_y + self.state.rel_ground_hm[int(self.state.len_x / 2)][int(self.state.len_z / 2)]
            http_framework.interfaceUtils.runCommand(
                f'setblock {sx} {sy} {sz} minecraft:oak_sign')
            src.chronicle.write_coords_to_sign(sx, sy, sz, self.settlement_pos, (cx, cz))
            http_framework.interfaceUtils.runCommand(
                f'setblock {sx} {sy + 1} {sz} minecraft:torch')
        exit(0)

    def run_without_render(self, steps, start, time_limit, is_writing_sign):
        """
        Execute simulation for given steps without rendering at each iteration
        :param steps:
        :param start:
        :param time_limit:
        :param is_writing_sign:
        :return:
        """
        is_writing = run.IS_WRITING_CHRONICLE_TO_CONSOLE
        run.IS_WRITING_CHRONICLE_TO_CONSOLE = False
        self.get_max_building_dy()
        viable_water_starts = list(set(self.state.water).intersection(self.state.blocks_near_land))
        max_tries = 99
        status, attempt = self.start(viable_water_starts, -1, max_tries)
        while status == False:
            self.state.reset()
            self.update_building_max_dy()
            status, attempt = self.start(viable_water_starts, attempt, max_tries)
            if attempt > max_tries:
                print(
                    "Error: could not find valid settlement location in given area! Please try running with a different area.")
                print("Exiting")
                exit(1)
            attempt += 1
        run.IS_WRITING_CHRONICLE_TO_CONSOLE = is_writing
        finished_fully, times, steps = self.step(steps - 1, False, start, time_limit)
        x = self.chronicles_pos[0]
        z = self.chronicles_pos[1]
        y = self.state.rel_ground_hm[x][z]
        self.state.step(is_rendering=True, use_total_changed_blocks=True)
        http_framework.interfaceUtils.runCommand(
            f'setblock {x + self.state.world_x} {y + self.state.world_y} {z + self.state.world_z} minecraft:chest')
        finished_fully = src.chronicle.place_chronicles(self.state, x, y, z, f"History of {self.settlement_name}",
                                                        self.original_agent.name)
        print("Simulation finished after " + str(time.time() - start) + " seconds. " + str(
            steps + 1) + " steps performed, out of " + str(times + 1) + " steps.")
        cx = self.state.world_x + x
        cz = self.state.world_z + z
        print(f"Chronicles placed at {cx}, {self.state.world_y + y}, {cz}! ")
        if is_writing_sign:
            sx = int(self.state.world_x + self.state.len_x / 2)
            sz = int(self.state.world_z + self.state.len_z / 2)
            sy = self.state.world_y + self.state.rel_ground_hm[int(self.state.len_x / 2)][int(self.state.len_z / 2)]
            http_framework.interfaceUtils.runCommand(
                f'setblock {sx} {sy} {sz} minecraft:oak_sign')
            src.chronicle.write_coords_to_sign(sx, sy, sz, self.settlement_pos, (cx, cz))
            http_framework.interfaceUtils.runCommand(
                f'setblock {sx} {sy + 1} {sz} minecraft:torch')
        exit(0)

    def get_max_building_dy(self):
        """
        Determine the max y difference in building ground for valid buildings
        :return:
        """
        if self.state.len_x > 900 or self.state.len_z > 900:
            print("Caution: chosen area is very large! Generator initialization may take a long time.")
            self.building_max_y_diff = 6
        elif self.state.len_x > 700 or self.state.len_z > 700:
            print("Caution: chosen area is large! Generator initialization may take a long time.")
            self.building_max_y_diff = 5
        elif self.state.len_x > 400 or self.state.len_z > 400:
            print("Caution: chosen area is large! Generator initialization may take a long time.")
            self.building_max_y_diff = 3
        else:
            self.building_max_y_diff = 2

    def update_building_max_dy(self):
        y = self.building_max_y_diff_tries + 1
        self.building_max_y_diff = min(y, 6)

    def start(self, viable_water_starts, attempt_start, max_tries):
        """
        Initialize main street + more checks up to max_tries
        :param viable_water_starts:
        :param attempt_start:
        :param max_tries:
        :return:
        """
        result = False  # returns agent positions or False
        attempt = attempt_start - 1
        create_well = False
        old_water = []
        while result is False:
            attempt += 1
            self.state.reset()
            if attempt > max_tries: return False, attempt
            create_well = attempt > 25
            result, old_water, self.chronicles_pos, self.original_agent = self.state.init_main_st(viable_water_starts,
                                                                                                  str(attempt + 1) + "/" + str(
                                                                                                      max_tries + 1))
        # build a house
        building = "./schemes/" + random.choice(src.utils.STRUCTURES['small'])[0]
        f = open(building, "r")
        construction_site = random.choice(list(self.state.construction))
        c_center = construction_site.center
        positions = self.state.get_nearest_tree(*c_center, 30)
        use_generated_tree = False
        if len(positions) < 1:
            use_generated_tree = True
            nearest_tree_pos = [0, 0]
        else:
            nearest_tree_pos = positions[0]

        wood_type = self.state.blocks(nearest_tree_pos[0],
                                      self.state.rel_ground_hm[nearest_tree_pos[0]][nearest_tree_pos[1]],
                                      nearest_tree_pos[1]) if not use_generated_tree else 'oak'
        wood = src.utils.get_wood_type(wood_type)
        schematic_args = self.state.find_build_spot(0, 0, building, wood, ignore_sector=True,
                                                    max_y_diff=self.building_max_y_diff, build_tries=100)
        if schematic_args is False:  # flip the x and z
            print(f"  Attempt {str(attempt + 1)}/{str(max_tries + 1)}: could not find build location! Trying again~")
            self.state.water = old_water
            return False, attempt
        status, build_y = self.state.place_building(*schematic_args)
        if status is False:
            self.state.water = old_water
            return False, attempt
        self.state.step()  # check if this affects agent pahs. it seems to.
        print("Finished simulation init!")
        self.settlement_pos = (
            schematic_args[0].center[0] + self.state.world_x, schematic_args[0].center[1] + self.state.world_z)
        print("Successfully initialized main street! Go to position " + str(self.settlement_pos))
        return True, -1

    def step(self, times, is_rendering, start, time_limit):
        """
        Iterate through simulation
        :param times:
        :param is_rendering:
        :param start:
        :param time_limit:
        :return:
        """
        current = time.time()
        for i in range(times + 1):
            if current - start > time_limit - 10:  # to allow for book-writing
                return False, times, i
            self.update_nodes()
            self.state.update_agents(is_rendering)
            self.state.step(is_rendering)
            time.sleep(self.rendering_step_duration * is_rendering)
            current = time.time()
        return True, times, i

    def update_nodes(self):
        """
        Update Nodes by prosperity and State Phase if needed
        :return:
        """
        self.state.prosperity *= self.pDecay
        self.state.traffic *= self.tDecay

        xInd, yInd = np.where(self.state.update_flags > 0)  # to update these nodes
        indices = list(zip(xInd, yInd))  # list of tuples
        random.shuffle(indices)  # shuffle coordinates to update
        for (i, j) in indices:  # update a specific random numbor of tiles
            self.state.update_flags[i][j] = 0
            node_pos = self.state.node_pointers[(i, j)]  # possible optimization here
            node = self.state.nodes(*node_pos)
            # calculate roads
            if not (
                    src.utils.TYPE.GREEN.name in node.get_type() or src.utils.TYPE.TREE.name in node.type or src.utils.TYPE.CONSTRUCTION.name in node.type):
                return
            node.local_prosperity = sum([n.prosperity() for n in node.local()])
            node.local_traffic = sum(
                [n.traffic() for n in node.range() if not self.state.out_of_bounds_Node(n.center[0], n.center[1])])
            road_found_far = len(set(node.range()) & set(self.state.roads))
            road_found_near = len(set(node.local()) & set(self.state.roads))
            # major roads
            if node.local_prosperity > self.maNum and not road_found_far:  # if node's local prosperity is high
                if node.local_prosperity > self.brNum:  # bridge/new lot minimum
                    if self.state.append_road(point=(i, j), road_type=src.utils.TYPE.MAJOR_ROAD.name,
                                              correction=self.corNum, bend_if_needed=True):
                        self.state.generated_a_road = True
                else:
                    if self.state.append_road(point=(i, j), road_type=src.utils.TYPE.MAJOR_ROAD.name,
                                              correction=self.corNum, bend_if_needed=True):
                        self.state.generated_a_road = True
            if node.local_prosperity > self.buNum and road_found_near:
                self.state.set_type_building(node.local())  # wait, the local is a building?
            # minor roads
            if self.phase >= 3:
                if node.local_prosperity > self.miNum and not road_found_near:
                    pass
                    self.state.append_road((i, j), src.utils.TYPE.MINOR_ROAD.name, correction=self.corNum,
                                           bend_if_needed=True)
                elif src.utils.TYPE.TREE.name in node.get_type() or src.utils.TYPE.GREEN.name in node.get_type():
                    if len(node.neighbors() & self.state.construction):
                        lot = node.get_lot()
                        if lot is not None:
                            self.state.set_type_building(lot)
