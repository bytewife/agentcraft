import src.scheme_utils
import src.my_utils
import http_framework.worldLoader

areaFlex = [0, 0, 10, 10] # default build area
# you can set a build area in minecraft using the /setbuildarea command
# buildArea = requestBuildArea()
# if buildArea != -1:
#     x1 = buildArea["xFrom"]
#     z1 = buildArea["zFrom"]
#     x2 = buildArea["xTo"]
#     z2 = buildArea["zTo"]
#     areaFlex = [x1, z1, x2-x1, z2-z1]

# x1 = -5
# z1 = 25
# x2 = -7
# z2 = 27
# area = [x1,z1,x2,z2]
# area = src.my_utils.correct_area(area)
# worldSlice = http_framework.worldLoader.WorldSlice(area)  #_so area is chunks?

file_name = "tests/prosperity/market_stall_2"
src.scheme_utils.download_schematic(10, 63, 30, 15, 67, 37, file_name)
src.scheme_utils.place_schematic_in_world(file_name, 0, 63, 0, dir_z=-1)

# src.scheme_utils.download_schematic(x1, 62, z1, -7, x2, z2, file_name + ".in")
# src.scheme_utils.download_heightmap(worldSlice, file_name +"hm")

# place_schematic_in_world("market_tent_1", 293, 62, 855)
