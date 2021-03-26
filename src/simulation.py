from agent import *
from states import *
import time
from http_framework.worldLoader import *

class Simulation:

    # with names? Let's look after ensembles and other's data scructure for max flexibility
    def __init__(self, XZXZ):
        self.agents = set()
        self.world_slice = WorldSlice(XZXZ)
        self.state = State(self.world_slice)


    def step(self, times, is_rendering_each_step=False, rendering_step_duration=1.0):

        for i in range(times):

            ## DEBUG
            for agent in self.agents:
                if len(agent.path) != 1:
                    agent.follow_path(state=self.state, walkable_heightmap=self.state.rel_ground_hm)
                else:
                    agent.log_adjacent_tree()
                # agent.move_self(1, 1, self.state, self.state.walkable_heightmap)

            self.update_agents()
            if is_rendering_each_step:
                time.sleep(rendering_step_duration)
                self.state.render()


    def add_agent(self, agent : Agent):
        self.agents.add(agent)


    def update_agents(self):
        for agent in self.agents:
            agent.move_in_state(self.state)
        pass