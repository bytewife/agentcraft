import src.states
import src.scheme_utils
import src.manipulation
import src.simulation
import http_framework.worldLoader
import http_framework.interfaceUtils
import src.my_utils
import src.agent
import json
from enum import Enum

x1 = 0
z1 = 0
x2 = 1
z2 = 1
area = [x1,z1,x2,z2]
area = src.my_utils.correct_area(area)
worldSlice = http_framework.worldLoader.WorldSlice(area)  #_so area is chunks?
sign = """minecraft:oak_sign[rotation=2]{Text1:'{"text":"first line"}', Text2:'{"text":"second line"}', Text3:'{"text":"third line"}', Text4:'{"text":"forth line"}'}"""
working_head_command = """\
setblock 308 37 822 minecraft:player_head[rotation=1]{display:{Name:"{\\"text\\":\\"Link\\"}"},SkullOwner:{Id:[I;992165650,-2095955837,-1891443028,-215838394],Properties:{textures:[{Value:"eyJ0ZXh0dXJlcyI6eyJTS0lOIjp7InVybCI6Imh0dHA6Ly90ZXh0dXJlcy5taW5lY3JhZnQubmV0L3RleHR1cmUvNmJiMmU2OWIzODcwZmUyZjRmMWJhMTRhOGY5Y2E4YWNjOWE3NTIwZTRlNGE5Nzg0YzE5YTNhMGM5NDQ2ZTRkIn19fQ=="}]}}}\
"""

# I just copy pasted the /data get block when pointed at a head
example_head_set = """{SkullOwner: {Id: [I; 992165650, -2095955837, -1891443028, -215838394], Properties: {textures: [{Value: "eyJ0ZXh0dXJlcyI6eyJTS0lOIjp7InVybCI6Imh0dHA6Ly90ZXh0dXJlcy5taW5lY3JhZnQubmV0L3RleHR1cmUvNmJiMmU2OWIzODcwZmUyZjRmMWJhMTRhOGY5Y2E4YWNjOWE3NTIwZTRlNGE5Nzg0YzE5YTNhMGM5NDQ2ZTRkIn19fQ=="}]}}, x: 308, y: 37, z: 822, id: "minecraft:skull"}"""
head = src.my_utils.get_player_head_block_id("bob", example_head_set)

http_framework.interfaceUtils.setBlockWithData(308, 37, 822, head)
http_framework.interfaceUtils.setBlockWithData(307, 37, 822, sign)

# minecraft:player_head{SkullOwner:"jeb"}
# print(http_framework.interfaceUtils.setBlockWithData(0, 63, 0, command))
# print(http_framework.interfaceUtils.runCommand(working_head_command))
print("done")
# oak_sign[rotation=1]{Text1:'{"text":"first line"}', Text2:'{"text":"second line"}', Text3:'{"text":"third line"}', Text4:'{"text":"forth line"}'}
# print(worldSlice.getBlockCompoundAt((0,63,0))['Properties'])

# file_name = ""
#
# sim = src.simulation.Simulation(area)
#
# ag = src.agent.Agent(sim.state, 1, 0, sim.state.rel_ground_hm, "Jonah")
# sim.add_agent(ag)
# la = sim.state.legal_actions
# ag.set_motive(ag.Motive.LOGGING)
# sim.step(10, True, 1.0)
#
# print(file_name+" complete")
