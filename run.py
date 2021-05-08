#! /usr/bin/python3
"""### Run
Run the generator!
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"

import src.simulation
import http_framework.interfaceUtils
import src.my_utils
import src.agent
import src.states

if __name__ == '__main__':
    x1 = 40000
    z1 = 40000
    x2 = 40100
    z2 = 40100

    area = [x1,z1,x2,z2]
    area = src.my_utils.correct_area(area)
    file_name = ""
    clean_rad = int(max(abs(x2-x1), abs(z2-z1)))
    clean_agents = "kill @e[type=minecraft:armor_stand,x={},y=64,z={},distance=..{}]".format(str((x2+x1)/2), str((z2+z1)/2), clean_rad)
    http_framework.interfaceUtils.runCommand(clean_agents)

    frame_duration = 0.00
    sim = src.simulation.Simulation(area, rendering_step_duration=frame_duration, is_rendering_each_step=False)

    timesteps = 1000
    sim.run_with_render(timesteps)
    a = sim.state.sectors

    ## ROADS
    for r in sim.state.roads:
        if r in sim.state.construction:
            # sim.state.construction.discard(r)
            pass
        x = r.center[0]
        z = r.center[1]
        y = sim.state.rel_ground_hm[x][z] + 1
        sim.state.set_block(x,y,z,"minecraft:redstone_block")

    ## CONSTRUCTION
    # for b in sim.state.construction:
    #     x = b.center[0]
    #     z = b.center[1]
    #     y = sim.state.rel_ground_hm[x][z] + 1
    #     sim.state.set_block(x,y,z,"minecraft:gold_block")
        # if src.my_utils.TYPE.WATER.name in b.get_type():
        #     pass

    #HEIGHTMAP
    # for x in range(len(sim.state.blocks_arr)):
    #     for z in range(len(sim.state.blocks_arr[0][0])):
            # y = sim.state.static_ground_hm[x][z]
            # sim.state.set_block(x, y, z, "minecraft:oak_sign")
            # y = sim.state.rel_ground_hm[x][z]
            # sim.state.set_block(x, y, z, "minecraft:oak_sign")

    #EXT HEIGHTMAP
    # for pos in sim.state.built_heightmap:
    #     x,z=pos
    #     y = sim.state.rel_ground_hm[x][z]
    #     sim.state.set_block(x, y, z, "minecraft:oak_sign")


    #Water
    # for r in sim.state.built:
    #     x,z = r.center
    #     y = sim.state.rel_ground_hm[x][z] + 1
    #     sim.state.set_block(x,y,z,"minecraft:gold_block")

    sim.state.step(1)

    print(src.agent.Agent.shared_resources)
    print("done")
