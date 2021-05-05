#! /usr/bin/python3
"""### Simulation
Simulations contain and modify data regarding the execution of the State and the generator.
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"


import src.agent
import src.states
import src.my_utils
import http_framework.worldLoader
import http_framework.interfaceUtils
import time
import random
import numpy as np

class Simulation:

    # with names? Let's look after ensembles and other's data scructure for max flexibility
    def __init__(self, XZXZ, precomp_world_slice=None, precomp_legal_actions = None, precamp_pathfinder=None, precomp_types = None, run_start=True, precomp_sectors = None, precomp_nodes=None, precomp_node_pointers=None, phase=0, maNum=5, miNum=400, byNum= 2000, brNum=1000, buNum=10, pDecay=0.98, tDecay=0.25, corNum=5, times=1, is_rendering_each_step=True, rendering_step_duration=0.8):
        if precomp_world_slice == None:
            self.world_slice = http_framework.worldLoader.WorldSlice(*XZXZ)
        else:
            self.world_slice = precomp_world_slice
        self.state = src.states.State(XZXZ, self.world_slice, precomp_pathfinder=precamp_pathfinder, precomp_legal_actions=precomp_legal_actions, precomp_types=precomp_types, precomp_sectors=precomp_sectors, precomp_nodes=precomp_nodes, precomp_node_pointers=precomp_node_pointers)
        # exit(0)
        # if precomp_legal_actions:
        #     self.state.legal_actions = precomp_legal_actions
        # if precomp_types:
        #     self.state.types = precomp_types
        # if precomp_sectors:
        #     self.state.sectors = precomp_sectors
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

        # parse heads
        f = open("./assets/agent_heads.out.txt")
        agent_heads = f.readlines()
        agent_heads = [h.rstrip('\n') for h in agent_heads]
        src.states.State.agent_heads = agent_heads
        f.close()

        if run_start:
            clean_agents = "kill @e[type=minecraft:armor_stand,x={},y=64,z={},distance=..100]".format(
                str((XZXZ[2] + XZXZ[0]) / 2),
                str((XZXZ[3] + XZXZ[1]) / 2))
            http_framework.interfaceUtils.runCommand(clean_agents)

    def run_with_render(self, steps):
        while self.start() == False:
            self.state.reset_for_restart()
        self.step(steps, is_rendering=True)

    def run_without_render(self, steps):
        while self.start() == False:
            self.state.reset_for_restart()
        self.step(steps, is_rendering=False)
        self.state.step(is_rendering=True, use_total_changed_blocks=True)

    # this needs to be run manually so that we can rerun the sim if needed
    def start(self):
        result = False  # returns agent positions or False
        i=0
        max_tries = 50
        while result is False:
            self.state.reset_for_restart(use_heavy=True)
            # self.state.construction.clear()
            # self.state.roads.clear()
            if i > max_tries: return False
            result = self.state.init_main_st()
            i+=1

        # build a house
        building = "./schemes/"+random.choice(src.my_utils.STRUCTURES['small'])[0]
        f = open(building, "r")
        size = f.readline()
        x_size, y_size, z_size = [int(n) for n in size.split(' ')]

        construction_site = random.choice(list(self.state.construction))
        c_center = construction_site.center
        positions = self.state.get_nearest_tree(*c_center, 30)
        use_generated_tree = False
        if len(positions) < 1:
            use_generated_tree = True
        nearest_tree_pos = positions[0]

        wood_type = self.state.blocks(nearest_tree_pos[0], self.state.rel_ground_hm[nearest_tree_pos[0]][nearest_tree_pos[1]], nearest_tree_pos[1]) if not use_generated_tree else 'oak'
        wood = src.my_utils.get_wood_type(wood_type)
        i = 0
        # rx = random.randint(0,self.state.last_node_pointer_x)
        # rz = random.randint(0,self.state.last_node_pointer_z)
        schematic_args = self.state.find_build_location(0,0,building,wood,ignore_sector=True, max_y_diff=6)
        if schematic_args is False:  # flip the x and z
            print("Error: could not find build location!")
            return False
        status, build_y = self.state.place_schematic(*schematic_args)
        if status is False: return False
        # self.state.place_platform(*schematic_args, build_y)
        self.state.step()  # check if this affects agent pahs. it seems to.
        print("Finished simulation init!!")
        fixed_pos = (schematic_args[0].center[0]+self.state.world_x,schematic_args[0].center[1]+self.state.world_z)
        print("Successfully initialized main street! Go to position "+str(fixed_pos))
        return True



    def step(self, times=1, is_rendering=True):
        for i in range(times):
            self.handle_nodes()
            self.state.update_agents(is_rendering)
            self.state.step(is_rendering)
            time.sleep(self.rendering_step_duration * is_rendering)



    def handle_nodes(self):
        self.state.prosperity *= self.pDecay
        self.state.traffic *= self.tDecay

        xInd, yInd = np.where(self.state.updateFlags > 0)  # to update these nodes
        indices = list(zip(xInd, yInd))  # list of tuples
        random.shuffle(indices)  # shuffle coordinates to update
        for (i, j) in indices:  # update a specific random numbor of tiles
            self.state.updateFlags[i][j] = 0
            node_pos = self.state.node_pointers[(i,j)]  # possible optimization here
            node = self.state.nodes(*node_pos)

            # calculate roads
            if not (src.my_utils.TYPE.GREEN.name in node.get_type() or src.my_utils.TYPE.TREE.name in node.type or src.my_utils.TYPE.CONSTRUCTION.name in node.type):
                # print("returnung")
                return

            node.local_prosperity = sum([n.prosperity() for n in node.local()])
            # print("going because local prosp is "+str(node.local_prosperity))
            node.local_traffic = sum([n.traffic() for n in node.range() if not self.state.out_of_bounds_Node(n.center[0], n.center[1])])

            road_found_far = len(set(node.range()) & set(self.state.roads))
            # print("road found far is "+str(road_found_far))
            road_found_near = len(set(node.local()) & set(self.state.roads))
            # print("road found near is "+str(road_found_far))

            # major roads
            if node.local_prosperity > self.maNum and not road_found_far:  # if node's local prosperity is high
                # print("prosperity fulfilled; creating road")
                if node.local_prosperity > self.brNum:  # bridge/new lot minimum
                    # print("built major bridge road")
                    # self.state.append_road(point=(i, j), road_type=src.my_utils.TYPE.MAJOR_ROAD.name, leave_lot=True, correction=self.corNum, bend_if_needed=True)
                    self.state.append_road(point=(i, j), road_type=src.my_utils.TYPE.MAJOR_ROAD.name, correction=self.corNum, bend_if_needed=True, only_place_if_walkable=True)
                    # print("road 1: at point "+str((i,j)))
                else:
                    # print("built major normal road")
                    self.state.append_road(point=(i, j), road_type=src.my_utils.TYPE.MAJOR_ROAD.name, correction=self.corNum, bend_if_needed=True, only_place_if_walkable=True)
                    # print("road 2: at point " + str((i, j)))
            if node.local_prosperity > self.buNum and road_found_near:
                # print("prosperity fulfilled; creating building")
                self.state.set_type_building(node.local()) # wait, the local is a building?

            # if self.phase >= 2:
            #     # bypasses
            #     if node.local_traffic > self.byNum and not road_found_far:
            #         # self.state.set_new_bypass(i, j, self.corNum)
            #         self.state.set_new_bypass(i, j, self.corNum)

            # minor roads
            if self.phase >= 3:
                # find closest road node, connect to it
                if node.local_prosperity > self.miNum and not road_found_near:
                    # print("building minor road")
                    # if not len([n for n in node.plot() if Type.BUILDING not in n.type]):
                    pass
                    self.state.append_road((i, j), src.my_utils.TYPE.MINOR_ROAD.name, correction=self.corNum, bend_if_needed=True)

                # calculate reservations of greenery
                elif src.my_utils.TYPE.TREE.name in node.get_type() or src.my_utils.TYPE.GREEN.name in node.get_type():
                    if len(node.neighbors() & self.state.construction):
                        lot = node.get_lot()
                        if lot is not None:
                            # if random.random() < 0.5:
                            #     self.state.set_type_city_garden(lot)
                            # else:
                            #     self.state.set_type_building(lot)
                            self.state.set_type_building(lot)


        # if use_auto_motive:
        #     agent.auto_motive()
