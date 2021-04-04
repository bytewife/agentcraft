# import random  # standard python lib for pseudo random

import src.scheme_utils
import http_framework.interfaceUtils
import http_framework.worldLoader
import src.movement
import src.my_utils
# https://stackoverflow.com/questions/65003877/understanding-leafsize-in-scipy-spatial-kdtree
import src.simulation
import src.manipulation
import src.agent


############## debug
def global_to_state_coords(world_x, world_z, build_area):
    # I want to take a global coord and change it to state y
    x = world_x - build_area[0]
    z = world_z - build_area[1]
    return (x, z)


def get_state_surface_y(state_x, state_z, state_heightmap, state_y):
    return state_heightmap[state_x][state_z] - state_y
##############
areaFlex = [0, 0, 32, 32] # default build area
# you can set a build area in minecraft using the /setbuildarea command
buildArea = http_framework.interfaceUtils.requestBuildArea()
if buildArea != -1:
    x1 = buildArea["xFrom"]
    z1 = buildArea["zFrom"]
    x2 = buildArea["xTo"]
    z2 = buildArea["zTo"]
    areaFlex = [x1, z1, x2-x1, z2-z1]
area = src.my_utils.correct_area(areaFlex)
# load the world data
# this uses the /chunks endpoint in the background
worldSlice = http_framework.worldLoader.WorldSlice(area)  #_so area is chunks?
sim = src.simulation.Simulation(area)

# save_state(state, state_y, "../hope.txt")
# load_state("../hope.txt", area[0], area[1])
# visualize_topography(area, state, state_heightmap, state_y)


# place_schematic_in_state(sim.state, "./test.txt", 0, 25, 0, dir_y=1)
### tree tests
check_x = 5
check_z = 7


# tree_y = get_state_surface_y(*global_to_state_coords( check_x, check_z, area), state_y=sim.state.world_y, state_heightmap=sim.state.surface_heightmap)
# if sim.state.is_log(check_x, tree_y, check_z):
#     sim.state.cut_tree_at(check_x, tree_y, check_z, times=1)
#
# sim.state.update_heightmaps(0,1)

agent = src.agent.Agent(sim.state, 0, 0, sim.state.rel_ground_hm, "JJ")
sim.add_agent(agent)
# nearest_trees = agent.get_nearest_trees(starting_search_radius=15, max_iterations=5, radius_inc= 10)
# chosen_tree = choice(nearest_trees)
# print("chosen tree is ")
# print(chosen_tree)
# if nearest_trees != None:
#     chosen_tree = choice(nearest_trees)
#     dest_x = chosen_tree[0]
#     dest_z = chosen_tree[1]
#     agent.teleport(dest_x, dest_z,sim.state.walkable_heightmap)

###
# state_coords = sim.state.world_to_state((9, 63, 18))
# legal_actions = get_all_legal_actions(sim.state.assets, 2, sim.state.walkable_heightmap, 2, [])
# sim.update_agents()
# sim.state.render()
# get_path(0, 0, 5, 5)

agent.set_motive(src.agent.Agent.Motive.LOGGING)

# agent.follow_path(state=sim.state, walkable_heightmap=sim.state.walkable_heightmap)
# sim.step(50, is_rendering_each_step=True)

# print(sim.state.legal_actions)
sim.state.pathfinder.create_sectors(sim.state.heightmaps["MOTION_BLOCKING_NO_LEAVES"], sim.state.legal_actions)
aaaa = sim.state.sectors
print("sector is ")
print(sim.state.legal_actions[0][2])
print(sim.state.sectors[0,5])
yb = sim.state.abs_ground_hm[0, 5] - sim.state.world_y
print(sim.state.blocks[0][yb][5])
print("walkable is ")
print(sim.state.rel_ground_hm[0][5])
src.manipulation.cut_tree_at(sim.state, 0, yb, 5)
sim.state.step()
print("walkable is ")
print(sim.state.rel_ground_hm[0][5])
# recompute sector after cutting it down at 0, 5
# sim.state.pathfinder.update_sector_for_block(0, 5, sim.state.sectors, sim.state.pathfinder.sector_sizes, legal_actions=sim.state.legal_actions)
aaaa = sim.state.sectors
aaaa = sim.state.sectors


# sim.state.save_state(sim.state, "hope.txt")
# sim.state.load_state("hope.txt", area[0], area[1])

print("done")