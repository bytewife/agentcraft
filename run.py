#! /usr/bin/python3
"""### Run
Run the generator!
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"

import sys
import getopt
import src.simulation
import http_framework.interfaceUtils
import time
import src.my_utils
import src.agent
import src.states

IS_RENDERING_FRAMEWISE = True
IS_WRITING_CHRONICLE = True
IS_WRITING_CHRONICLE_TO_CONSOLE = False
IS_WRITING_LOCATION_AT_MIDPOINT = False
IS_INCREASING_TICK_RATE = False

def parse_opts(argv):
    global IS_WRITING_CHRONICLE_TO_CONSOLE, IS_RENDERING_FRAMEWISE, IS_WRITING_CHRONICLE, IS_WRITING_LOCATION_AT_MIDPOINT, IS_INCREASING_TICK_RATE
    x1 = 0
    y1 = 0
    x2 = 0
    y2 = 0
    time_limit = 3000
    steps = 1500
    frame_length = 0.20

    area_given = False
    def help():
        msg = f"""Minecraft Minesim by aith
     Runs an agent-based settlement generator in Minecraft! Entry for GDMC 2021.

Options:
     -a X1,Y1,X2,Y2   |  Set the generator's build AREA in the running Minecraft world. Avoid spaces in between numbers.
     -t SECONDS       |  Set the TIME limit for the generator's execution. DEFAULT={time_limit}
     -s STEPS         |  Set the number of TIME-STEPS the generator takes. DEFAULT={steps}
     -f FRAMELENGTH   |  Set the duration of each frame of render. DEFAULT={frame_length} seconds
     --norender       |  Disable per-frame rendering (for performance) 
     --nochronicle    |  Disable writing to chronicle
     --printchronicle |  Write the chronicle's output to console
     --leavesign      |  Render a sign at the center of the given area describing the location of the settlement.

Example:
     python3 run.py -a 0,0,200,200 -t 600 -s 1000 -f 0.4 --norender
     
Warning:
     With larger areas, such as 1000x1000, the initialization can take long. If necessary, using the --norender flag can speed up settlement generation.
"""
        print(msg)
        return

    try:
        opts, args = getopt.getopt(argv, 'a:t:s:f:', ['norender', 'printchronicle', 'nochronicle', 'leavesign', 'inctick'])
    except getopt.GetoptError:
        help()
        sys.exit(1)
    for opt, arg in opts:
        if opt in ['-h','--h']:
            help()
            sys.exit()
        elif opt in ['-t', '--t']:
            try:
                time_limit= int(arg)
            except ValueError:
                print("Error: -t requires an integer.")
                sys.exit(1)
        elif opt in ["-s", "--s"]:
            try:
                steps = int(arg)
            except ValueError:
                print("Error: -t requires an integer.")
                sys.exit(0)
        elif opt in ["-a", "--a"]:
            try:
                nums = arg.split(',')
                if len(nums) != 4:
                    raise ValueError
                nums = [int(a) for a in nums]
            except ValueError:
                print("Error: -a requires x1,y1,x2,y2 as integer coordinates.")
                print("Example: -a 0,0,100,100")
                sys.exit(1)
            area_given = True
            x1 = nums[0]
            y1 = nums[1]
            x2 = nums[2]
            y2 = nums[3]
        elif opt in ["-f", "--f"]:
            try:
                frame_length = float(arg)
            except ValueError:
                print("Error: -f requires an decimal number.")
                sys.exit(0)
        elif opt == '--norender':
            IS_RENDERING_FRAMEWISE = False
        elif opt == '--nochronicle':
            IS_WRITING_CHRONICLE = False
        elif opt == '--printchronicle':
            IS_WRITING_CHRONICLE_TO_CONSOLE = True
        elif opt == '--leavesign':
            IS_WRITING_LOCATION_AT_MIDPOINT = True
        elif opt == '--inctick':
            IS_INCREASING_TICK_RATE = True
    if not area_given:
        print("Error: requires area given with -a. Use -h for options.")
        sys.exit(0)
    return [x1,y1,x2,y2], time_limit, steps, frame_length, IS_RENDERING_FRAMEWISE

if __name__ == '__main__':
    argv = sys.argv[1:]
    area, time_limit, steps, frame_duration, is_rendering_per_frame = parse_opts(argv)
    start = time.time()
    x1, z1, x2, z2 = area
    print(f"Executing in area [{str(x1)}, {str(z1)}, {str(x2)}, {str(z2)}] with {steps} steps in {time_limit} seconds!")
    area = src.my_utils.correct_area(area)
    file_name = ""
    clean_rad = int(max(abs(x2-x1), abs(z2-z1)))
    clean_agents_cmd = "kill @e[type=minecraft:armor_stand,x={},y=64,z={},distance=..{}]".format(str((x2+x1)/2), str((z2+z1)/2), clean_rad)
    http_framework.interfaceUtils.runCommand(clean_agents_cmd)

    if IS_INCREASING_TICK_RATE:
        inc_tick_cmd = "gamerule randomTickSpeed 100"
        http_framework.interfaceUtils.runCommand(inc_tick_cmd)

    # frame_duration = 0.00
    sim = src.simulation.Simulation(area, rendering_step_duration=frame_duration, is_rendering_each_step=False, start_time = start)

    if IS_RENDERING_FRAMEWISE:
        sim.run_with_render(steps, start, time_limit, IS_WRITING_LOCATION_AT_MIDPOINT)
    else:
        sim.run_without_render(steps, start, time_limit, IS_WRITING_LOCATION_AT_MIDPOINT)

    ## ROADS
    # for r in sim.state.roads:
    #     if r in sim.state.construction:
    #         # sim.state.construction.discard(r)
    #         pass
    #     x = r.center[0]
    #     z = r.center[1]
    #     y = sim.state.rel_ground_hm[x][z] + 1
    #     sim.state.set_block(x,y,z,"minecraft:redstone_block")

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

    # sim.state.step(1)

    print(src.agent.Agent.shared_resources)
    print("Execution complete! Enjoy your new settlement :)")

