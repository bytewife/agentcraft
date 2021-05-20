#! /usr/bin/python3
"""### Misc tools
Contains an assortment of tools and data needed for the generator.
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"
from enum import Enum
import http_framework.interfaceUtils
import src.agent
import numpy as np
from random import choice

# https://stackoverflow.com/questions/34470597/is-there-a-dedicated-way-to-get-the-number-of-items-in-a-python-enum

colors = [('white', '16383998'), ('orange', '16351261'), ('magenta', '13061821'), ('light_blue', '3847130'), ('yellow', '16701501'), ('lime', '8439583'), ('pink', '15961002'), ('gray', '4673362'), ('cyan', '1481884'), ('purple', '8991416'), ('blue', '3949738'), ('brown', '8606770'), ('green', '6192150'), ('red', '11546150'), ('black', '1908001')]
boots_per_phase = {
	1: 'leather_boots',
	2: 'iron_boots',
	3: 'golden_boots'
}
#_currently I don't use the slabs here
set_choices = [
	[["minecraft:bricks", "minecraft:granite", "minecraft:polished_granite"], ["minecraft:brick_slab", "minecraft:granite_slab", "minecraft:polished_granite_slab"], ["minecraft:brick_stairs", "minecraft:granite_stairs", "minecraft:polished_granite_stairs"]],
	[["minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:gravel"], ["minecraft:stone_brick_slab[type=bottom]", "minecraft:cobblestone_slab"], ["minecraft:stone_brick_stairs", "minecraft:cobblestone_stairs"]],
	[["minecraft:basalt", "minecraft:nether_bricks", "minecraft:blackstone"], ["minecraft:nether_brick_slab[type=bottom]", "minecraft:blackstone_slab"], ["minecraft:nether_brick_stairs", "minecraft:blackstone_stairs"]],
	  # [["minecraft:sandstone", "minecraft:gravel", "minecraft:diorite"], ["minecraft:stone_brick_slab[type=bottom]", "minecraft:cobblestone_slab"],
	#  [["minecraft:prismarine", "minecraft:prismarine_bricks", "minecraft:dark_prismarine"], ["minecraft:stone_brick_slab[type=bottom]", "minecraft:cobblestone_slab"],
	 ]

ROAD_SETS = {
	'default': ["minecraft:bricks", "minecraft:granite", "minecraft:polished_granite"],
	'default_slabs': ["minecraft:brick_slab", "minecraft:granite_slab"]
}
road_set = choice(set_choices)
ROAD_SETS['default'] = road_set[0]
ROAD_SETS['default_slabs'] = road_set[1]

STRUCTURES = {
    "decor": [
		( "cart_1_flex", 20 ),
		( "cart_2_flex", 20 ),
		( "cart_3_flex", 20 ),
		( "hay_1_flex", 15 ),
		( "lamp_1_flex", 15 ),
		( "lamp_2_flex", 15 ),
		( "logs_1_flex", 15 ),
		( "market_stall_1_flex", 15 ),
		( "market_stall_2_flex", 15 ),
		( "market_stall_3_flex", 15),
		("market_stall_3_flex", 15),
		("ornamental_tree_1_flex", 15),
	],
	"small": [
		("tiny_house_1", 35),
		("tiny_house_2", 35),
		("tiny_house_3", 35),
		("tiny_house_4", 35),
		("storage_1_flex", 35),
		# need to give these heads
		("tiny_house_1_flex", 35),
		("tiny_house_2_flex", 35),
		("tiny_house_3_flex", 35),
		("tiny_house_4_flex", 35),
		("storage_1", 35),
	],
	"med": [
		( "small_house_1_flex", 50 ),
		( "small_house_2_flex", 50 ),
		( "small_house_3_flex", 50 ),
		( "small_house_4_flex", 50 ),
		("med_house_1_flex_keep_dark", 50),
		("med_house_2_flex", 50),
		("med_house_3_flex", 50),
		("med_house_4_flex", 50),
		("med_house_5_flex", 50),
		("tower_1", 50),
		("tower_1_flex", 50),
	],
	"large": [
		("church_1_flex", 70),
		("church_2_flex", 70),
		("castle_1_flex", 70),
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
			   "PROPAGATE": ['turtle_egg'],
			   "REPLENISH_TREE": ['bone_meal'],
			   "SOCIALIZE_LOVER": ["poppy", 'cake', 'sweet_berries'],
			   "SOCIALIZE_FRIEND": ["honey_bottle", 'wheat'],
			   "SOCIALIZE_ENEMY": ["stone_sword", 'golden_sword', 'iron_sword'],
			   }



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
	LEAVES = 16


class HEIGHTMAPS(Enum):
	MOTION_BLOCKING = 1
	MOTION_BLOCKING_NO_LEAVES = 2
	OCEAN_FLOOR = 3
	WORLD_SURFACE = 4

class TYPE_TILES:
	tile_sets = {
		TYPE.WATER.value: {  #WATER
			"minecraft:water",
			"minecraft:water[level=0]",
			"water",
			"water[level = 0]",
			"minecraft:ice",
			"minecraft:stone",
			"stone",
			"minecraft:stone[]",
			"stone[]",
			"minecraft:ice[]",
			"ice",
			"ice[]",
			"minecraft:seagrass[]",
			"minecraft:seagrass",
			"seagrass[]",
			"seagrass",
		},
		TYPE.TREE.value: {  # FOREST
			"minecraft:dark_oak_log[axis=y]",
			"dark_oak_log[axis=y]",
			"minecraft:dark_oak_log",
			"dark_oak_log",
			"minecraft:spruce_log[axis=y]",
			"spruce_log[axis=y]",
			"minecraft:spruce_log",
			"spruce_log",
			"minecraft:acacia_log[axis=y]",
			"acacia_log[axis=y]",
			"minecraft:acacia_log",
			"acacia_log",
			"minecraft:oak_log[axis=y]",
			"minecraft:oak_log",
			"oak_log[axis=y]",
			"oak_log",
			"minecraft:jungle_log[axis=y]",
			"minecraft:jungle_log",
			"jungle_log[axis=y]",
			"jungle_log",
			"minecraft:birch_log[axis=y]",
			"minecraft:birch_log",
			"birch_log[axis=y]",
			"birch_log",
		},
		TYPE.GREEN.value: {  # GREEN
			"minecraft:grass_block",
			"grass_block",
			"minecraft:grass_block[]",
			"grass_block[]",
			"minecraft:sand"
			"sand"
			"minecraft:sand[]"
			"sand[]"
			"minecraft:dirt",
			"dirt",
			"minecraft:dirt[]",
			"dirt[]",
			"minecraft:podzol",
			"minecraft:sand",
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
			"minecraft:bricks", "minecraft:granite", "minecraft:polished_granite",
			"minecraft:brick_slab", "minecraft:granite_slab", "minecraft:polished_granite_slab",
			"minecraft:brick_stairs", "minecraft:granite_stairs", "minecraft:polished_granite_stairs",
			"minecraft:stone_bricks", "minecraft:cobblestone", "minecraft:gravel",
			"minecraft:stone_brick_slab[type=bottom]", "minecraft:cobblestone_slab",
			"minecraft:stone_brick_stairs", "minecraft:cobblestone_stairs",
			"minecraft:basalt", "minecraft:nether_bricks", "minecraft:blackstone",
			"minecraft:nether_brick_slab[type=bottom]", "minecraft:blackstone_slab",
			"minecraft:nether_brick_stairs", "minecraft:blackstone_stairs",
			"minecraft:brick_stairs[facing=east]",
			"minecraft:brick_stairs[facing=west]",
			"minecraft:brick_stairs[facing=north]",
			"minecraft:brick_stairs[facing=south]",
			"minecraft:granite_stairs[facing=west]",
			"minecraft:granite_stairs[facing=east]",
			"minecraft:granite_stairs[facing=north]",
			"minecraft:granite_stairs[facing=south]",
			"minecraft:polished_granite_stairs[facing=west]",
			"minecraft:polished_granite_stairs[facing=east]",
			"minecraft:polished_granite_stairs[facing=north]",
			"minecraft:polished_granite_stairs[facing=south]",
			"minecraft:stone_brick_stairs[facing=west]",
			"minecraft:stone_brick_stairs[facing=east]",
			"minecraft:stone_brick_stairs[facing=north]",
			"minecraft:stone_brick_stairs[facing=south]",
			"minecraft:cobblestone_stairs[facing=west]",
			"minecraft:cobblestone_stairs[facing=east]",
			"minecraft:cobblestone_stairs[facing=north]",
			"minecraft:cobblestone_stairs[facing=south]",
			"minecraft:nether_brick_stairs[facing=west]",
			"minecraft:nether_brick_stairs[facing=east]",
			"minecraft:nether_brick_stairs[facing=north]",
			"minecraft:nether_brick_stairs[facing=south]",
			"minecraft:blackstone_stairs[facing=west]",
			"minecraft:blackstone_stairs[facing=east]",
			"minecraft:blackstone_stairs[facing=north]",
			"minecraft:blackstone_stairs[facing=south]",
		},
		TYPE.MINOR_ROAD.value: {  # MINOR ROAD
			"minecraft:bricks", "minecraft:granite", "minecraft:polished_granite", "minecraft:brick_slab",
			"minecraft:granite_slab",
			"minecraft:grass_path",
		},
		TYPE.BRIDGE.value: {  # BRIDGE

		},
		TYPE.CITY_GARDEN.value: {

		},
		TYPE.HIGHWAY.value: {

		},
		TYPE.AIR.value: {
			"minecraft:air",
			"air",
			"minecraft:air[]",
			"air[]",
			"minecraft:cave_air"
		},
		TYPE.PASSTHROUGH.value: {
			"air",
			"minecraft:air",
			"minecraft:cave_air",
			"minecraft:vines",
			"minecraft:snow",
			"minecraft:snow[]",
			"minecraft:snow[layers=1]",
			"snow[layers=1]",
			"snow",
			"minecraft:sunflower",
			"minecraft:spruce_wall_sign",
			"minecraft:vine[east = true, north = false, south = false, up = false, west = false]",
			"minecraft:vine[east = true, north = true, south = false, up = false, west = false]",
			"minecraft:vine[east = false, north = false, south = true, up = false, west = false]",
			"minecraft:vine[east = false, north = false, south = false, up = false, west = true]",
			"minecraft:vine[east = true, north = false, south = false, up = true, west = false]",
			"minecraft:vine[east = false, north = true, south = false, up = true, west = false]",
			"minecraft:vine[east = false, north = false, south = true, up = true, west = false]",
			"minecraft:vine[east = false, north = false, south = false, up = true, west = true]",
			"minecraft:cocoa[age = 0, facing = north]",
			"minecraft:cocoa[age = 1, facing = north]",
			"minecraft:cocoa[age = 2, facing = north]",
			"minecraft:cocoa[age = 3, facing = north]",
			"minecraft:cocoa[age = 0, facing = south]",
			"minecraft:cocoa[age = 1, facing = south]",
			"minecraft:cocoa[age = 2, facing = south]",
			"minecraft:cocoa[age = 3, facing = south]",
			"minecraft:cocoa[age = 0, facing = east]",
			"minecraft:cocoa[age = 1, facing = east]",
			"minecraft:cocoa[age = 2, facing = east]",
			"minecraft:cocoa[age = 3, facing = east]",
			"minecraft:cocoa[age = 0, facing = west]",
			"minecraft:cocoa[age = 1, facing = west]",
			"minecraft:cocoa[age = 2, facing = west]",
			"minecraft:cocoa[age = 3, facing = west]",
			"minecraft:oak_wall_sign[facing=north]",
			"minecraft:oak_wall_sign[facing=south]",
			"minecraft:oak_wall_sign[facing=east]",
			"minecraft:oak_wall_sign[facing=west]",
			"minecraft:birch_wall_sign[facing=north]",
			"minecraft:birch_wall_sign[facing=south]",
			"minecraft:birch_wall_sign[facing=east]",
			"minecraft:birch_wall_sign[facing=west]",
			"minecraft:acacia_wall_sign[facing=north]",
			"minecraft:acacia_wall_sign[facing=south]",
			"minecraft:acacia_wall_sign[facing=east]",
			"minecraft:acacia_wall_sign[facing=west]",
			"minecraft:jungle_wall_sign[facing=north]",
			"minecraft:jungle_wall_sign[facing=south]",
			"minecraft:jungle_wall_sign[facing=east]",
			"minecraft:jungle_wall_sign[facing=west]",
			"minecraft:dark_oak_wall_sign[facing=north]",
			"minecraft:dark_oak_wall_sign[facing=south]",
			"minecraft:dark_oak_wall_sign[facing=east]",
			"minecraft:dark_oak_wall_sign[facing=west]",
			"minecraft:spruce_door",
			"minecraft:oak_door",
			"minecraft:birch_door",
			"minecraft:acacia_door",
			"minecraft:jungle_door",
			"minecraft:dark_oak_door",
			"minecraft:dark_oak_door",

			"minecraft:spruce_door[facing=north,half=upper,hinge=left,open=false,powered=false]",
			"minecraft:spruce_door[facing=east,half=upper,hinge=left,open=false,powered=false]",
			"minecraft:spruce_door[facing=south,half=upper,hinge=left,open=false,powered=false]",
			"minecraft:spruce_door[facing=west,half=upper,hinge=left,open=false,powered=false]",

			"minecraft:spruce_door[facing=north,half=lower,hinge=left,open=false,powered=false]",
			"minecraft:spruce_door[facing=east,half=lower,hinge=left,open=false,powered=false]",
			"minecraft:spruce_door[facing=south,half=lower,hinge=left,open=false,powered=false]",
			"minecraft:spruce_door[facing=west,half=lower,hinge=left,open=false,powered=false]",

			"minecraft:spruce_door[facing=north,half=upper,hinge=right,open=false,powered=false]",
			"minecraft:spruce_door[facing=east,half=upper,hinge=right,open=false,powered=false]",
			"minecraft:spruce_door[facing=south,half=upper,hinge=right,open=false,powered=false]",
			"minecraft:spruce_door[facing=west,half=upper,hinge=right,open=false,powered=false]",

			"minecraft:spruce_door[facing=north,half=lower,hinge=right,open=false,powered=false]",
			"minecraft:spruce_door[facing=east,half=lower,hinge=right,open=false,powered=false]",
			"minecraft:spruce_door[facing=south,half=lower,hinge=right,open=false,powered=false]",
			"minecraft:spruce_door[facing=west,half=lower,hinge=right,open=false,powered=false]",

			"minecraft:spruce_door[facing=north,half=upper,hinge=left,open=true,powered=false]",
			"minecraft:spruce_door[facing=east,half=upper,hinge=left,open=true,powered=false]",
			"minecraft:spruce_door[facing=south,half=upper,hinge=left,open=true,powered=false]",
			"minecraft:spruce_door[facing=west,half=upper,hinge=left,open=true,powered=false]",

			"minecraft:spruce_door[facing=north,half=lower,hinge=left,open=true,powered=false]",
			"minecraft:spruce_door[facing=east,half=lower,hinge=left,open=true,powered=false]",
			"minecraft:spruce_door[facing=south,half=lower,hinge=left,open=true,powered=false]",
			"minecraft:spruce_door[facing=west,half=lower,hinge=left,open=true,powered=false]",

			"minecraft:grass",
			"minecraft:grass[]",
			"grass",
			"grass[]",
			"minecraft:lily_of_the_valley",
			"minecraft:lily_of_the_valley[]",
			"minecraft:oak_sapling",
			"minecraft:oak_sapling[stage=0]",
			"minecraft:oak_sapling[stage=1]",
			"minecraft:spruce_sapling",
			"minecraft:spruce_sapling[stage=0]",
			"minecraft:spruce_sapling[stage=1]",
			"minecraft:birch_sapling",
			"minecraft:birch_sapling[stage=0]",
			"minecraft:spruce_sapling[stage=1]",
			"minecraft:acacia_sapling",
			"minecraft:acacia_sapling[stage=0]",
			"minecraft:acacia_sapling[stage=1]",
			"minecraft:jungle_sapling",
			"minecraft:jungle_sapling[stage=0]",
			"minecraft:jungle_sapling[stage=1]",
			"minecraft:dark_oak_sapling",
			"minecraft:dark_oak_sapling[stage=0]",
			"minecraft:dark_oak_sapling[stage=1]",
			"minecraft:oak_leaves",
			"minecraft:spruce_leaves",
			"minecraft:birch_leaves",
			"minecraft:jungle_leaves",
			"minecraft:acacia_leaves",
			"minecraft:oak_leaves[distance=1]",
			"minecraft:oak_leaves[distance=2]",
			"minecraft:oak_leaves[distance=3]",
			"minecraft:oak_leaves[distance=4]",
			"minecraft:oak_leaves[distance=5]",
			"minecraft:oak_leaves[distance=6]",
			"minecraft:oak_leaves[distance=6]",
			"minecraft:oak_leaves[distance=7]",
			"minecraft:spruce_leaves[distance=1]",
			"minecraft:spruce_leaves[distance=2]",
			"minecraft:spruce_leaves[distance=3]",
			"minecraft:spruce_leaves[distance=4]",
			"minecraft:spruce_leaves[distance=5]",
			"minecraft:spruce_leaves[distance=6]",
			"minecraft:spruce_leaves[distance=7]",
			"minecraft:birch_leaves[distance=1]",
			"minecraft:birch_leaves[distance=2]",
			"minecraft:birch_leaves[distance=3]",
			"minecraft:birch_leaves[distance=4]",
			"minecraft:birch_leaves[distance=5]",
			"minecraft:birch_leaves[distance=6]",
			"minecraft:birch_leaves[distance=7]",
			"minecraft:jungle_leaves[distance=1]",
			"minecraft:jungle_leaves[distance=2]",
			"minecraft:jungle_leaves[distance=3]",
			"minecraft:jungle_leaves[distance=4]",
			"minecraft:jungle_leaves[distance=5]",
			"minecraft:jungle_leaves[distance=6]",
			"minecraft:jungle_leaves[distance=7]",
			"minecraft:acacia_leaves[distance=1]",
			"minecraft:acacia_leaves[distance=2]",
			"minecraft:acacia_leaves[distance=3]",
			"minecraft:acacia_leaves[distance=4]",
			"minecraft:acacia_leaves[distance=5]",
			"minecraft:acacia_leaves[distance=6]",
			"minecraft:acacia_leaves[distance=7]",
			"minecraft:dark_oak_sapling[distance=1]",
			"minecraft:dark_oak_sapling[distance=2]",
			"minecraft:dark_oak_sapling[distance=3]",
			"minecraft:dark_oak_sapling[distance=4]",
			"minecraft:dark_oak_sapling[distance=5]",
			"minecraft:dark_oak_sapling[distance=6]",
			"minecraft:dark_oak_sapling[distance=7]",
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
			"minecraft:poppy[]",
			"minecraft:dandelion",
			"minecraft:dandelion[]",
			"minecraft:large_fern",
			"minecraft:cornflower",
			"minecraft:dead_bush",
			"minecraft:tall_grass",
			"minecraft:azure_bluet",
			"minecraft:azure_bluet[]",
			"azure_bluet[]",
			"azure_bluet",
			"tall_grass",
			"minecraft:tall_grass[half=upper]",
			"minecraft:tall_grass[half=lower]",
			"tall_grass[half=upper]",
			"tall_grass[half=lower]",
			"minecraft:lily_pad",
			"minecraft:allium",
			"minecraft:allium[]",
			"minecraft:red_tulip",
			"minecraft:red_tulip[]",
			"minecraft:rose_bush",
			"minecraft:rose_bush[]",
			"minecraft:rose_bush[half=upper]",
			"minecraft:rose_bush[half=lower]",
			"rose_bush[half=upper]",
			"rose_bush[half=lower]",
			"minecraft:sweet_berry_bush",
			"minecraft:sweet_berry_bush[]",
		},
		TYPE.BUILT.value: {  # TODO hook this up with settingg the nodes to be built on start
			"minecraft:oak_stairs",
			"minecraft:oak_slab[type=bottom]",
			"minecraft:spruce_stairs",
			"minecraft:spruce_slab[type=bottom]",
			"minecraft:birch_stairs",
			"minecraft:birch_slab[type=bottom]",
			"minecraft:dark_oak_stairs",
			"minecraft:dark_oak_slab[type=bottom]",
			"minecraft:acacia_stairs",
			"minecraft:acacia_slab[type=bottom]",
			"minecraft:jungle_stairs",
			"minecraft:jungle_slab[type=bottom]",
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
			"minecraft:oak_planks",
			"minecraft:spruce_planks",
			"minecraft:birch_planks",
			"minecraft:acacia_planks",
			"minecraft:dark_oak_planks",
			"minecraft:jungle_planks",
			"minecraft:jungle_stairs",
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
		TYPE.LEAVES.value: {
			"minecraft:dark_oak_sapling",
			"minecraft:oak_leaves",
			"minecraft:spruce_leaves",
			"minecraft:birch_leaves",
			"minecraft:jungle_leaves",
			"minecraft:acacia_leaves",
			"minecraft:oak_leaves[distance=1]",
			"minecraft:oak_leaves[distance=2]",
			"minecraft:oak_leaves[distance=3]",
			"minecraft:oak_leaves[distance=4]",
			"minecraft:oak_leaves[distance=5]",
			"minecraft:oak_leaves[distance=6]",
			"minecraft:oak_leaves[distance=6]",
			"minecraft:oak_leaves[distance=7]",
			"minecraft:spruce_leaves[distance=1]",
			"minecraft:spruce_leaves[distance=2]",
			"minecraft:spruce_leaves[distance=3]",
			"minecraft:spruce_leaves[distance=4]",
			"minecraft:spruce_leaves[distance=5]",
			"minecraft:spruce_leaves[distance=6]",
			"minecraft:spruce_leaves[distance=7]",
			"minecraft:birch_leaves[distance=1]",
			"minecraft:birch_leaves[distance=2]",
			"minecraft:birch_leaves[distance=3]",
			"minecraft:birch_leaves[distance=4]",
			"minecraft:birch_leaves[distance=5]",
			"minecraft:birch_leaves[distance=6]",
			"minecraft:birch_leaves[distance=7]",
			"minecraft:jungle_leaves[distance=1]",
			"minecraft:jungle_leaves[distance=2]",
			"minecraft:jungle_leaves[distance=3]",
			"minecraft:jungle_leaves[distance=4]",
			"minecraft:jungle_leaves[distance=5]",
			"minecraft:jungle_leaves[distance=6]",
			"minecraft:jungle_leaves[distance=7]",
			"minecraft:acacia_leaves[distance=1]",
			"minecraft:acacia_leaves[distance=2]",
			"minecraft:acacia_leaves[distance=3]",
			"minecraft:acacia_leaves[distance=4]",
			"minecraft:acacia_leaves[distance=5]",
			"minecraft:acacia_leaves[distance=6]",
			"minecraft:acacia_leaves[distance=7]",
			"minecraft:dark_oak_sapling[distance=1]",
			"minecraft:dark_oak_sapling[distance=2]",
			"minecraft:dark_oak_sapling[distance=3]",
			"minecraft:dark_oak_sapling[distance=4]",
			"minecraft:dark_oak_sapling[distance=5]",
			"minecraft:dark_oak_sapling[distance=6]",
			"minecraft:dark_oak_sapling[distance=7]",
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

def setBlockWithData(abs_x, abs_y, abs_z, data):
    command = "setblock {} {} {} {}".format(abs_x, abs_y, abs_z, data)
    return http_framework.interfaceUtils.runCommand(command)


def get_heightmap(world_slice, heightmap_type="MOTION_BLOCKING_NO_LEAVES", y_offset=0):
    heightmap = world_slice.heightmaps[heightmap_type]
    if y_offset != 0:
        for x in range(len(heightmap)):
            for z in range(len(heightmap[x])):
                heightmap[x][z] += y_offset
    return np.array(heightmap, dtype=np.uint8)
