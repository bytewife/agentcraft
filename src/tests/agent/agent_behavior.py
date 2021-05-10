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
x2 = 10
z2 = 10
area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)

clean_agents = "kill @e[type=minecraft:armor_stand,x={},y=64,z={},distance=..100]".format(str((x2+x1)/2), str((z2+z1)/2))
http_framework.interfaceUtils.runCommand(clean_agents)
building = '../../../schemes/Sector_test_2'
sim = src.simulation.Simulation(area, rendering_step_duration=1, run_start=False)

sim.state.saplings.append((4,4))

ag = src.agent.Agent(sim.state, 3, 3, sim.state.rel_ground_hm, "George", """SkullOwner:{Id:[I;412153319,853231097,-1973860048,684905748],Properties:{textures:[{Value:"eyJ0ZXh0dXJlcyI6eyJTS0lOIjp7InVybCI6Imh0dHA6Ly90ZXh0dXJlcy5taW5lY3JhZnQubmV0L3RleHR1cmUvYjI0M2NkMmUyYjMxMWExMzY5Zjg2M2FmMWIzMjNiOTkxNzRhM2JkM2E5OTFjMWI0NDA3MzAxYTI2NGNlZTZmYyJ9fX0="}]}}""", motive=src.agent.Agent.Motive.REPLENISH_TREE.name)
sim.add_agent(ag, use_auto_motive=False)

sim.step(14)
print(sim.state.saplings)
print(sim.state.trees)
sim.step(1)

print("done")
