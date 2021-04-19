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
example_head_set = """{SkullOwner: {Id: [I; 657576908, -1980940883, 933235114, 513329351], Properties: {textures: [{Value: "eyJ0ZXh0dXJlcyI6eyJTS0lOIjp7InVybCI6Imh0dHA6Ly90ZXh0dXJlcy5taW5lY3JhZnQubmV0L3RleHR1cmUvYTBhZDg2NTE4Y2Q0OWNjZmUyODdmZTFkNzM5OTk0NTA1MjFhZDAxODE5ZTVhOGQ5OTg5NTIzMTUyY2IxZjY2ZSJ9fX0="}]}}, x: 178, y: 67, z: 254, id: "minecraft:skull"}"""
head = src.my_utils.get_player_head_block_id("Coal", example_head_set)
print(head)


# If you're going to create more, watch out for escape characters
# http_framework.interfaceUtils.setBlockWithData(308, 37, 822, head)
# http_framework.interfaceUtils.setBlockWithData(307, 37, 822, sign)

## This is for myself when I want to download head id's
## I do this because you currently cannot get this kind of data from the http interface

# name = "barrel"
# new_head = """\
# {SkullOwner: {Id: [I; -1113038487, 1526484579, -1311424843, 637932952], Properties: {textures: [{Value: "eyJ0ZXh0dXJlcyI6eyJTS0lOIjp7InVybCI6Imh0dHA6Ly90ZXh0dXJlcy5taW5lY3JhZnQubmV0L3RleHR1cmUvYzY3ZDVkMzdjZDY0Y2UzZmI1NzM3N2QyNWQ2MTUyYWE0YWMyZTM3OTU0MjQ4ZDVkOTFmODhmYmQ3OTFmNDc2NiJ9fX0="}]}}, x: 295, y: 63, z: 843, id: "minecraft:skull"}\
# """ # just put the head data here
# id = src.my_utils.get_player_head_block_id(name, new_head)
# print(id)


# summon = """\
# summon minecraft:armor_stand {x} {y} {z} {{ShowArms:1, NoBasePlate:1, CustomNameVisible:1, Rotation:[90f,0f,0f], \
# Small:{is_small}, CustomName: '{{"text":"{name}", "color":"customcolor", "bold":false, "underlined":false, \
# "strikethrough":false, "italic":false, "obscurated":false}}', \
# ArmorItems:[{{id:"{boots}",Count:1b}},\
# {{id:"{lower_armor}",Count:1b}},\
# {{id:"{upper_armor}",Count:1b}},\
# {{id:"player_head",Count:1b,tag:{{SkullOwner:{{Id:"401c89f6-384e-473d-b448-1c73a342aed9",Properties:{{textures:[{{Value:"eyJ0ZXh0dXJlcyI6eyJTS0lOIjp7InVybCI6Imh0dHA6Ly90ZXh0dXJlcy5taW5lY3JhZnQubmV0L3RleHR1cmUvOTVhZWY4ZDczYzZiM2I5N2Q3YjU3MTZmY2EyMTVmNWViYTY3OTkyMTJkMTFlYjYzZTE1ODg5NDBkMWUyMWI3MyJ9fX0="}}]}}}}}}}}],\
# HandItems:[{{id:"{hand1}", Count:1b}},{{id:"{hand2}", Count:1b}}],\
# Pose:{{Head:[{head_tilt}f,10f,0f], \
# LeftLeg:[3f,10f,0f], \
# RightLeg:[348f,18f,0f], \
# LeftArm:[348f,308f,0f], \
# RightArm:[348f,67f,0f]}}\
# }}\
# """.format(
#     x=0,
#     y=63,
#     z=0,
#     name="Ari",
#     is_small="false",
#     boots="leather_boots",
#     upper_armor="leather_chestplate",
#     lower_armor="leather_leggings",
#     hand1="apple",
#     hand2="oak_log",
#     head_tilt="350"# this can be related to resources! 330 is high, 400 is low
# )
# print(http_framework.interfaceUtils.runCommand(summon))
print("done")