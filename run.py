#! /usr/bin/python3
"""### Run
Run the generator!
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"

import sys, getopt
import src.simulation
import http_framework_backup.interfaceUtils
import time
import src.my_utils
import src.agent
import src.states

def parse_opts(argv):
    inputfile = ''
    outputfile = ''
    x1 = 0
    y1 = 0
    x2 = 0
    y2 = 0
    time_limit = 3000
    steps = 1000

    area_given = False

    def help():
        pass
        print("""
Minecraft Minesim by aith
     Runs an agent-based settlement generator in Minecraft! Entry for GDMC 2021.

Options:
     -a X1 Y1 X2 Y2  |  Set the generator's build AREA in the running Minecraft world.
     -t SECONDS      |  Set the TIME limit for the generator's execution.
     -s STEPS        |  Set the number of TIME-STEPS the generator takes.
""")

    try:
        opts, args = getopt.getopt(argv, 'ats:')
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for opt, arg in opts:
        if opt in ('-h','--h'):
            help()
            sys.exit()
        elif opt in ('-t', '--t'):
            if type(arg) == int:
                time_limit= arg
            else:
                print("Error: -t requires an integer.")
                sys.exit(1)
        elif opt in ("-s", "--s"):
            if type(arg) == int:
                area_given = True
                steps = arg
            else:
                print("Error: -t requires an integer.")
                sys.exit(1)
    if not area_given:
        print("Error: requires area given with -a")
        sys.exit(1)

    print ('Input file is "', inputfile)
    print ('Output file is "', outputfile)

if __name__ == '__main__':
    # parse_opts(sys.argv[1:])
    start = time.time()
    time_limit = 5
    x1 = 90000
    z1 = 90000
    x2 = 90100
    z2 = 90100

    area = [x1,z1,x2,z2]
    area = src.my_utils.correct_area(area)
    file_name = ""
    clean_rad = int(max(abs(x2-x1), abs(z2-z1)))
    clean_agents = "kill @e[type=minecraft:armor_stand,x={},y=64,z={},distance=..{}]".format(str((x2+x1)/2), str((z2+z1)/2), clean_rad)
    http_framework_backup.interfaceUtils.runCommand(clean_agents)

    frame_duration = 0.00
    sim = src.simulation.Simulation(area, rendering_step_duration=frame_duration, is_rendering_each_step=False, start_time = start)

    timesteps = 1500
    sim.run_with_render(timesteps, start, time_limit)
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

