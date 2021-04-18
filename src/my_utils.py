### returns a tuple of coordinates, with the lower x and z values first
from enum import Enum
import http_framework.interfaceUtils
import src.agent

# https://stackoverflow.com/questions/34470597/is-there-a-dedicated-way-to-get-the-number-of-items-in-a-python-enum

ROAD_SETS = {
	'default': ["minecraft:bricks	", "minecraft:granite", "minecraft:coarse_dirt", "minecraft:grass_path"],
	'default_slabs': ["minecraft:brick_slab", "minecraft:granite_slab"]
}

STRUCTURES = {
    "decor": [
		( "cart_1_flex", 10 ),
		( "market_stall_1_flex", 15 ),
		( "market_stall_2_flex", 15 ),
	],
	"small": [
		( "small_house_1_flex", 20 ),
		( "small_house_2_flex", 20 ),
	],
	"med": [
		("med_house_1_flex", 30),
		("med_house_2_flex", 30),
		("med_house_3_flex", 30),
		("med_house_4_flex", 30),
	],
	"large": [
		("church_1_flex", 40),
		("church_2_flex", 35),
		("castle_1_flex", 50),
	],
}

ROTATION_LOOKUP = {
	(0, 1): "0",
	(-1, 1): "45",
	(-1, 0): "90",
	(-1, -1): "135",
	(0, -1): "180",
	(1, -1): "225",
	(1, 0): "270",
	(1, 1): "315",
	(0, 0): "0",
}

AGENT_ITEMS = {"REST": ["clock", "white_tulip", "white_wool", "white_bed"],
			   "LOGGING": ["iron_axe", "golden_axe", "stone_axe"],
			   "WATER": ["glass_bottle", 'bucket'],
			   "BUILD": ["iron_shovel", "stone_shovel", "golden_shovel"],
			   "FAVORITE": ['apple', 'bread', 'melon_slice', 'golden_apple', 'book', 'diamond', 'emerald', 'nautilus_shell', 'cornflower', 'bamboo', 'torch', 'sunflower', 'zombie_head', 'ladder', 'poppy', 'warped_fungus'],
			   "REPLENISH": ['bone_meal']}



class ACTION_PROSPERITY():
	LOGGING = 10
	WATER = 20
	REPLENISH_TREE = 5
	WALKING = 1


class TYPE(Enum):
	WATER = 1
	TREE = 2
	GREEN = 3
	BROWN = 4
	CONSTRUCTION = 5
	MAJOR_ROAD = 6
	MINOR_ROAD = 7
	BRIDGE = 8
	CITY_GARDEN = 9
	HIGHWAY = 10
	AIR = 11
	PASSTHROUGH = 12
	BUILT = 13
	LAVA = 14
	FOREIGN_BUILT = 15


class HEIGHTMAPS(Enum):
	MOTION_BLOCKING = 1
	MOTION_BLOCKING_NO_LEAVES = 2
	OCEAN_FLOOR = 3
	WORLD_SURFACE = 4

class TYPE_TILES:
	tile_sets = {
		TYPE.WATER.value: {  #WATER
			"minecraft:water",
			"minecraft:flowing_water",
		},
		TYPE.TREE.value: {  # FOREST
			"minecraft:dark_oak_log",
			"minecraft:spruce_log",
			"minecraft:acacia_log",
			"minecraft:oak_log",
			"minecraft:jungle_log",
			"minecraft:birch_log",
		},
		TYPE.GREEN.value: {  # GREEN
			"minecraft:grass_block",
			"minecraft:sand"
			"minecraft:dirt",
			# "minecraft:oak_sapling",
		},
		TYPE.BROWN.value: {  # BROWN
			"minecraft:gravel",
			"minecraft:diorite",
			"minecraft:stone",
			"minecraft:coarse_dirt",
		},
		TYPE.CONSTRUCTION.value: {  # BUILDING
			""
		},
		TYPE.MAJOR_ROAD.value: {  # MAJOR ROAD

		},
		TYPE.MINOR_ROAD.value: {  # MINOR ROAD

		},
		TYPE.BRIDGE.value: {  # BRIDGE

		},
		TYPE.CITY_GARDEN.value: {

		},
		TYPE.HIGHWAY.value: {

		},
		TYPE.AIR.value: {
			"minecraft:air",
			"minecraft:cave_air"
		},
		TYPE.PASSTHROUGH.value: {
			"minecraft:air",
			"minecraft:cave_air",
			"minecraft:snow",
			"minecraft:spruce_wall_sign",
			"minecraft:oak_wall_sign",
			"minecraft:birch_wall_sign",
			"minecraft:acacia_wall_sign",
			"minecraft:jungle_wall_sign",
			"minecraft:dark_oak_wall_sign",
			"minecraft:spruce_door",
			"minecraft:oak_door",
			"minecraft:birch_door",
			"minecraft:acacia_door",
			"minecraft:jungle_door",
			"minecraft:dark_oak_door",
			"minecraft:grass",
			"minecraft:oak_sapling",
			"minecraft:spruce_sapling",
			"minecraft:birch_sapling",
			"minecraft:acacia_sapling",
			"minecraft:jungle_sapling",
			"minecraft:dark_oak_sapling",
			"minecraft:oak_leaves",
			"minecraft:spruce_leaves",
			"minecraft:birch_leaves",
			"minecraft:jungle_leaves",
			"minecraft:acacia_leaves",
			"minecraft:oak_leaves[distance=7]",
			"minecraft:spruce_leaves[distance=7]",
			"minecraft:birch_leaves[distance=7]",
			"minecraft:jungle_leaves[distance=7]",
			"minecraft:acacia_leaves[distance=7]",
			"minecraft:white_carpet",
			"minecraft:orange_carpet",
			"minecraft:magenta_carpet",
			"minecraft:light_blue_carpet",
			"minecraft:yellow_carpet",
			"minecraft:lime_carpet",
			"minecraft:pink_carpet",
			"minecraft:gray_carpet",
			"minecraft:light_gray_carpet",
			"minecraft:cyan_carpet",
			"minecraft:purple_carpet",
			"minecraft:blue_carpet",
			"minecraft:brown_carpet",
			"minecraft:green_carpet",
			"minecraft:red_carpet",
			"minecraft:black_carpet",
			"minecraft:player_head",
			"minecraft:flower_pot",
			"minecraft:fern",
			"minecraft:poppy",
			"minecraft:dandelion",
			"minecraft:large_fern",
			"minecraft:lily_pad",
		},
		TYPE.BUILT.value: {  # TODO hook this up with settingg the nodes to be built on start
			"minecraft:oak_stairs",
			"minecraft:spruce_stairs",
			"minecraft:birch_stairs",
			"minecraft:dark_oak_stairs",
			"minecraft:acacia_stairs",
			"minecraft:jungle_stairs",
			"minecraft:oak_planks",
			"minecraft:spruce_planks",
			"minecraft:birch_planks",
			"minecraft:dark_oak_planks",
			"minecraft:acacia_planks",
			"minecraft:jungle_planks",
		},
		TYPE.LAVA.value: {
			"minecraft:lava",
		},
        TYPE.FOREIGN_BUILT.value: {
            "minecraft:oak_stairs",
            "minecraft:spruce_stairs",
            "minecraft:birch_stairs",
            "minecraft:dark_oak_stairs",
            "minecraft:acacia_stairs",
            "minecraft:jungle_stairs",
            "minecraft:oak_planks",
            "minecraft:spruce_planks",
            "minecraft:birch_planks",
            "minecraft:dark_oak_planks",
            "minecraft:acacia_planks",
            "minecraft:jungle_planks",
        },
    }


def correct_area(area):
    if area[0] > area[2]:
        swap_array_elements(area, 0, 2)
    if area[1] > area[3]:
        swap_array_elements(area, 1, 3)
    return (area[0], area[1], area[2], area[3])


def swap_array_elements(arr, a, b):
    temp = arr[a]
    arr[a] = arr[b]
    arr[b] = temp


def convert_coords_to_key(x, y, z):
    # return str(x)+','+str(y)+','+str(z)
	return (x, y, z)


def convert_key_to_coords(key):
	# x, y, z = [int(coord) for coord in key.split(',')]
	# return x, y, z
    return key


# copy paste the text when you run /data get block, from {SkullOwner onwards
def get_player_head_block_id(name, SkullOwnerSet, rotation="1"):
	prop = SkullOwnerSet[1:]
	prop = prop.split(", x")[0]
	prop = prop.replace(" ", "")
	command = """player_head[rotation={0}]{{display:{{Name:"{{\\"text\\":\\"{1}\\"}}"}},{2}}}"""\
		.format(rotation, name, prop)
	return command


def get_wood_type(block):
    type = "oak"
    if 'oak' in block:
        type = 'oak'
    elif 'birch' in block:
        type = 'birch'
    elif 'spruce' in block:
        type = 'spruce'
    elif 'acacia' in block:
        type = 'acacia'
    elif 'jungle' in block:
        type = 'jungle'
    elif 'dark_oak' in block:
        type = 'dark_oak'
    return type


