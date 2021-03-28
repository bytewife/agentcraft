import src.agent
import src.states
import http_framework.worldLoader
import time

class Simulation:

    # with names? Let's look after ensembles and other's data scructure for max flexibility
    def __init__(self, XZXZ):
        self.agents = set()
        self.world_slice = http_framework.worldLoader.WorldSlice(XZXZ)
        self.state = src.states.State(self.world_slice)


    def step(self, times, is_rendering_each_step=False, rendering_step_duration=1.0):

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