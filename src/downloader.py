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

x1 = 295
y1 = 78
z1 = 809
x2 = 307
y2 = 93
z2 = 821
# x1 = 335
# y1 = 48
# z1 = 838
# x2 = 320
# y2 = 64
# z2 = 850
file_name = "../schemes/med_house_1"
src.scheme_utils.download_schematic(x1, y1, z1, x2, y2, z2, file_name)
src.scheme_utils.download_schematic(x1, y1, z1, x2, y2, z2, file_name+"_flex", flexible_tiles=True)
# src.scheme_utils.place_schematic_in_world(file_name, x2, y2 + y2 - y2 + 5, z2, dir_z=-1)

# src.scheme_utils.download_schematic(x1, 62, z1, -7, x2, z2, file_name + ".in")
# src.scheme_utils.download_heightmap(worldSlice, file_name +"hm")

# place_schematic_in_world("market_tent_1", 293, 62, 855)
