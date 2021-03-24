from agent import *
from states import *
from src.http_framework.worldLoader import *

class Simulation:

    # with names? Let's look after ensembles and other's data scructure for max flexibility
    def __init__(self, XZXZ):
        self.agents = {}
        self.world_slice = WorldSlice(XZXZ)
        self.state = State(self.world_slice)


    def add_agent(self, agent : Agent):
        self.agents[agent.name] = agent


    def update_agents(self):
        for agent in self.agents.values():
            agent.update_pos_in_state(self.state)