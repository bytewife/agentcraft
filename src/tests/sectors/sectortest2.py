import src.states
import src.scheme_utils
import src.manipulation
import src.simulation
import http_framework.worldLoader
import http_framework.interfaceUtils
import src.my_utils
import src.agent
import src.states
import numpy as np
import random

from src.linedrawing import get_line
from enum import Enum

x1 = 0
z1 = 0
x2 = 6
z2 = 3
area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)

clean_agents = "kill @e[type=minecraft:armor_stand,x={},y=64,z={},distance=..100]".format(str((x2+x1)/2), str((z2+z1)/2))
http_framework.interfaceUtils.runCommand(clean_agents)
building = '../../../schemes/Sector_test_1'
sim = src.simulation.Simulation(area, rendering_step_duration=0.2, run_start=False)
f = open(building, "r")
r = f.readline().split(' ')
sim.state.create_road((4,1), (4,1), road_type=src.my_utils.TYPE.MAJOR_ROAD.name)
sim.state.construction.add(sim.state.nodes[sim.state.node_pointers[(1,1)]])

print(sim.state.construction)
i = 0
build_tries = 150
while sim.state.place_building_at(sim.state.nodes[sim.state.node_pointers[(0,0)]], building, int(r[0]), int(r[2])) is False and i < build_tries:  # flip the x and z construction_site = random.choice(list(sim.state.construction))
    i+=1
sim.step(1)

print("legal actions are ")
print(sim.state.legal_actions)
print("heightmap is ")
print(sim.state.rel_ground_hm)
print("sectors are")
print(sim.state.sectors)