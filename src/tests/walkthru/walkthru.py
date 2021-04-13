import src.states
import src.scheme_utils
import src.manipulation
import src.simulation
import http_framework.worldLoader
import http_framework.interfaceUtils
import src.my_utils
import src.agent
import src.states
from pprint import pprint
import numpy as np

from src.linedrawing import get_line
from enum import Enum
x1 = 0
z1 = 0
x2 = 30
z2 = 30

area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
file_name = ""

clean_agents = "kill @e[type=minecraft:armor_stand,x={},y=64,z={},distance=..100]".format(str((x2+x1)/2), str((z2+z1)/2))
http_framework.interfaceUtils.runCommand(clean_agents)

sim = src.simulation.Simulation(area, rendering_step_duration=0.0, is_rendering_each_step=False)

src.agent.Agent.shared_resources["oak_log"] = 60

# sim.step(100, is_rendering=True)
for x in range(sim.state.len_x):
    for z in range(sim.state.len_z):
        pass

for built in sim.state.built:
    src.states.set_state_block(sim.state, built.center[0], sim.state.rel_ground_hm[built.center[0]][built.center[1]]+11, built.center[1], 'minecraft:red_wool')
sim.step(60)

print("done")