import src.agent
import src.states
import src.my_utils
import http_framework.worldLoader
import time
import random
import numpy as np
import names

class Simulation:

    # with names? Let's look after ensembles and other's data scructure for max flexibility
    def __init__(self, XZXZ, run_start=True, phase=0, maNum=5, miNum=400, byNum= 2000, brNum=1000, buNum=10, pDecay=0.98, tDecay=0.25, corNum=5, times=1, is_rendering_each_step=True, rendering_step_duration=0.8):
        self.agents = set()
        self.world_slice = http_framework.worldLoader.WorldSlice(XZXZ)
        self.state = src.states.State(self.world_slice)
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
        self.phase2threshold = 100
        self.phase3threshold = 200
        # parse heads
        f = open("../../../assets/agent_heads.out.txt")
        self.agent_heads = f.readlines()
        self.agent_heads = [h.rstrip('\n') for h in self.agent_heads]
        f.close()

        if run_start:
            self.start()

    def start(self):
        print("started")
        result = False  # returns agent positions or False
        for i in range(100):
            while result is False:
                result = self.state.init_main_st()

        # build a house
        building = "../../../schemes/"+random.choice(src.my_utils.STRUCTURES['small'])[0]
        f = open(building, "r")
        size = f.readline()
        x_size, y_size, z_size = [int(n) for n in size.split(' ')]

        construction_site = random.choice(list(self.state.construction))
        nearest_tree_pos = self.state.get_nearest_tree(*construction_site.center)[0]
        wood_type = self.state.blocks[nearest_tree_pos[0]]\
            [self.state.rel_ground_hm[nearest_tree_pos[0]][nearest_tree_pos[1]]]\
            [nearest_tree_pos[1]]
        wood = src.my_utils.get_wood_type(wood_type)
        i = 0
        build_tries = 300
        while self.state.place_building_at(construction_site, building, x_size, z_size, wood) is False and i < build_tries:  # flip the x and z
            construction_site = random.choice(list(self.state.construction))
            i+=1


        self.state.step()  # check if this affects agent pahs. it seems to.
        # spawn agents at main street endpoints
        for agent_pos in result:
            head = random.choice(self.agent_heads)
            new_agent = src.agent.Agent(self.state, *agent_pos, walkable_heightmap=self.state.rel_ground_hm, name=names.get_first_name(), head=head)
            self.add_agent(new_agent)
            # new_agent.set_motive(src.agent.Agent.Motive.LOGGING)



    def step(self, times=1, is_rendering=True):
        ##########

        for i in range(times):
            p = np.sum(self.state.prosperity)
            if p > self.phase2threshold:
                self.phase = 2
            if p > self.phase3threshold:
                self.phase = 3
            self.handle_nodes()
            self.update_agents(is_rendering)
            self.state.step(is_rendering)
            time.sleep(self.rendering_step_duration * is_rendering)
        if not self.is_rendering_each_step:  # render just the end
            self.state.step(is_rendering=True, use_total_changed_blocks=True)



    def handle_nodes(self):
        self.state.prosperity *= self.pDecay
        self.state.traffic *= self.tDecay

        xInd, yInd = np.where(self.state.updateFlags > 0)  # to update these nodes
        indices = list(zip(xInd, yInd))  # list of tuples
        random.shuffle(indices)  # shuffle coordinates to update
        for (i, j) in indices:  # update a specific random numbor of tiles
            self.state.updateFlags[i][j] = 0
            node_pos = self.state.node_pointers[(i,j)]  # possible optimization here
            node = self.state.nodes[(node_pos)]

            # calculate roads
            if not (src.my_utils.TYPE.GREEN.name in node.get_type() or src.my_utils.TYPE.TREE.name in node.type or src.my_utils.TYPE.BUILDING.name in node.type):
                # print("returnung")
                return


            node.local_prosperity = sum([n.prosperity() for n in node.local])
            # print("going because local prosp is "+str(node.local_prosperity))
            node.local_traffic = sum([n.traffic() for n in node.range if not self.state.out_of_bounds_Node(n.center[0], n.center[1])])

            road_found_far = len(set(node.range) & set(self.state.roads))
            # print("road found far is "+str(road_found_far))
            road_found_near = len(set(node.local) & set(self.state.roads))
            # print("road found near is "+str(road_found_far))

            # major roads
            if node.local_prosperity > self.maNum and not road_found_far:  # if node's local prosperity is high
                # print("prosperity fulfilled; creating road")
                if node.local_prosperity > self.brNum:  # bridge/new lot minimum
                    # print("built major bridge road")
                    self.state.append_road(point=(i, j), road_type=src.my_utils.TYPE.MAJOR_ROAD.name, leave_lot=True, correction=self.corNum)
                else:
                    # print("built major normal road")
                    self.state.append_road(point=(i, j), road_type=src.my_utils.TYPE.MAJOR_ROAD.name, correction=self.corNum)
            if node.local_prosperity > self.buNum and road_found_near:
                # print("prosperity fulfilled; creating building")
                self.state.set_type_building(node.local) # wait, the local is a building?

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
                    self.state.append_road((i, j), src.my_utils.TYPE.MINOR_ROAD.name, correction=self.corNum)

                # calculate reservations of greenery
                elif src.my_utils.TYPE.TREE.name in node.get_type() or src.my_utils.TYPE.GREEN.name in node.get_type():
                    if len(node.neighbors & self.state.construction):
                        lot = node.get_lot()
                        if lot is not None:
                            # if random.random() < 0.5:
                            #     self.state.set_type_city_garden(lot)
                            # else:
                            #     self.state.set_type_building(lot)
                            self.state.set_type_building(lot)


    def add_agent(self, agent : src.agent.Agent, use_auto_motive=True):
        self.agents.add(agent)
        if use_auto_motive:
            agent.auto_motive()

    def update_agents(self, is_rendering=True):
        for agent in self.agents:
            agent.unshared_resources['rest'] += agent.rest_dec_rate
            agent.unshared_resources['water'] += agent.water_dec_rate
            agent.follow_path(state=self.state, walkable_heightmap=self.state.rel_ground_hm)
            # agent.move_in_state()
            if is_rendering:
                agent.render()
            # print("agent is in "+str(self.state.sectors[agent.x][agent.z]))