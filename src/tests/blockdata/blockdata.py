import src.states
import src.scheme_utils
import src.manipulation
import src.simulation
import http_framework.worldLoader
import http_framework.interfaceUtils
import src.my_utils
import src.agent
from enum import Enum

sign = """minecraft:oak_sign[rotation=2]{Text1:'{"text":"first line"}', Text2:'{"text":"second line"}', Text3:'{"text":"third line"}', Text4:'{"text":"forth line"}'}"""

working_head_command = """\
setblock 308 37 822 minecraft:player_head[rotation=1]{display:{Name:"{\\"text\\":\\"Link\\"}"},SkullOwner:{Id:[I;992165650,-2095955837,-1891443028,-215838394],Properties:{textures:[{Value:"eyJ0ZXh0dXJlcyI6eyJTS0lOIjp7InVybCI6Imh0dHA6Ly90ZXh0dXJlcy5taW5lY3JhZnQubmV0L3RleHR1cmUvNmJiMmU2OWIzODcwZmUyZjRmMWJhMTRhOGY5Y2E4YWNjOWE3NTIwZTRlNGE5Nzg0YzE5YTNhMGM5NDQ2ZTRkIn19fQ=="}]}}}\
"""

# I just copy pasted the /data get block when pointed at a head
example_head_set = """{SkullOwner: {Id: [I; 992165650, -2095955837, -1891443028, -215838394], Properties: {textures: [{Value: "eyJ0ZXh0dXJlcyI6eyJTS0lOIjp7InVybCI6Imh0dHA6Ly90ZXh0dXJlcy5taW5lY3JhZnQubmV0L3RleHR1cmUvNmJiMmU2OWIzODcwZmUyZjRmMWJhMTRhOGY5Y2E4YWNjOWE3NTIwZTRlNGE5Nzg0YzE5YTNhMGM5NDQ2ZTRkIn19fQ=="}]}}, x: 308, y: 37, z: 822, id: "minecraft:skull"}"""
head = src.my_utils.get_player_head_block_id("bob", example_head_set)

# If you're going to create more, watch out for escape characters
# http_framework.interfaceUtils.setBlockWithData(308, 37, 822, head)
# http_framework.interfaceUtils.setBlockWithData(307, 37, 822, sign)

## This is for myself when I want to download head id's
## I do this because you currently cannot get this kind of data from the http interface
name = "barrel"
new_head = """\
{SkullOwner: {Id: [I; -1113038487, 1526484579, -1311424843, 637932952], Properties: {textures: [{Value: "eyJ0ZXh0dXJlcyI6eyJTS0lOIjp7InVybCI6Imh0dHA6Ly90ZXh0dXJlcy5taW5lY3JhZnQubmV0L3RleHR1cmUvYzY3ZDVkMzdjZDY0Y2UzZmI1NzM3N2QyNWQ2MTUyYWE0YWMyZTM3OTU0MjQ4ZDVkOTFmODhmYmQ3OTFmNDc2NiJ9fX0="}]}}, x: 295, y: 63, z: 843, id: "minecraft:skull"}\
""" # just put the head data here
id = src.my_utils.get_player_head_block_id(name, new_head)
print(id)

print("done")