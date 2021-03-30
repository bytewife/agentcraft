import src.agent
import src.states
import src.my_utils
import http_framework.worldLoader
import time
import random
import numpy as np

class Simulation:

    # with names? Let's look after ensembles and other's data scructure for max flexibility
    def __init__(self, XZXZ, run_start=True):
        self.agents = set()
        self.world_slice = http_framework.worldLoader.WorldSlice(XZXZ)
        self.state = src.states.State(self.world_slice)
        if run_start:
            self.start()

    def start(self):
            # for i in range(200):
            a = False
            while a is False:
                a = self.state.init_main_st()

    def step(self, phase=0, maNum=10, miNum=400, byNum= 2000, brNum=1000, buNum=400, pDecay=0.75, tDecay=0.25, corNum=5, times=1, is_rendering_each_step=True, rendering_step_duration=1.0):
        self.state.prosperity *= pDecay
        self.state.traffic *= tDecay

        # xInd, yInd = np.where(self.state.updateFlags > 0)  # to update these nodes
        # indices = list(zip(xInd, yInd))  # list of tuples
        # random.shuffle(indices)  # shuffle coordinates to update
        # for (i, j) in indices:  # update a specific random numbor of tiles
        #     self.state.updateFlags[i][j] = 0
        #     node_pos = self.state.nodes[self.state.node_pointers[(i,j)]]  # possible optimization here
        #     node = self.state.nodes[(node_pos)]
        #
        #     # calculate roads
        #     if not (src.my_utils.Type.GREEN.name in node.type or src.my_utils.Type.TREE.name in node.type or src.my_utils.Type.BUILDING.name in node.type):
        #         return
        #
        #     node.local_prosperity = sum([n.prosperity for n in node.local])  # should i change this to be tile-based?
        #     node.local_traffic = sum([n.traffic for n in node.range])
        #
        #     road_found_far = len(set(node.range) & set(self.state.roads))
        #     road_found_near = len(set(node.local) & set(self.state.roads))
        #
        #     # major roads
        #     if node.local_prosperity > maNum and not road_found_far:  # if node's local prosperity is high
        #         if node.local_prosperity > brNum:  # bridge/new lot minimum
        #             self.state.create_road(i, j, src.my_utils.Type.MAJOR_ROAD.name, leave_lot=True, correction=corNum)
        #         else:
        #             self.state.create_road(i, j, src.my_utils.Type.MAJOR_ROAD.name, correction=corNum)
        #     if node.local_prosperity > buNum and road_found_near:
        #         self.state.set_type_building(node.local) # wait, the local is a building?
        #
        #     if phase >= 2:
        #         # bypasses
        #         if node.local_traffic > byNum and not road_found_far:
        #             self.set_new_bypass(i, j, corNum)
        #
        #     # minor roads
        #     if phase >= 3:
        #         # find closest road node, connect to it
        #         if node.local_prosperity > miNum and not road_found_near:
        #             # if not len([n for n in node.plot() if Type.BUILDING not in n.type]):
        #             self.set_new_road(i, j, Type.MINOR_ROAD, correction=corNum)
        #
        #         # calculate reservations of greenery
        #         elif Type.TREE in node.type or Type.GREEN in node.type:
        #             if len(node.neighbors & self.built):
        #                 lot = node.get_lot()
        #                 if lot is not None:
        #                     if random.random() < 0.5:
        #                         self.set_type_city_garden(lot)
        #                     else:
        #                         self.set_type_building(lot)
        
        
        ##########
        for i in range(times):
            self.update_agents()
            self.state.render()
            time.sleep(rendering_step_duration)


    def add_agent(self, agent : src.agent.Agent):
        self.agents.add(agent)


    def update_agents(self):
        for agent in self.agents:
            agent.follow_path(state=self.state, walkable_heightmap=self.state.rel_ground_hm)
            # agent.move_in_state()
            agent.render()