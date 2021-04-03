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
#med house 1 (barrel, books)
# x1 = 296
# y1 = 78
# z1 = 810
# x2 = 307
# y2 = 93
# z2 = 820
#med house 2
# x1 = 302
# y1 = 95
# z1 = 843
# x2 = 312
# y2 = 111
# z2 = 856
#market_stall_1
# x1 = 285
# y1 = 79
# z1 = 855
# x2 = 290
# y2 = 84
# z2 = 862
#market_stall_2 (barrel
# x1 = 286
# y1 = 74
# z1 = 826
# x2 = 291
# y2 = 79
# z2 = 833
# # barn 1 (change gate trap doors to spruce. get misc heads)
# x1 = 314
# y1 = 81
# z1 = 791
# x2 = 322
# y2 = 90
# z2 = 804
# # small_house_1 (meat)
# x1 = 338
# y1 = 69
# z1 = 794
# x2 = 348
# y2 = 82
# z2 = 803
# # church 1 (books)
# x1 = 287
# y1 = 63
# z1 = 813
# x2 = 304
# y2 = 103
# z2 = 823
# # # church 2 (books)
# x1 = 280
# y1 = 98
# z1 = 723
# x2 = 290
# y2 = 123
# z2 = 734
# # # med_house_3
# x1 = 244
# y1 = 54
# z1 = 842
# x2 = 253
# y2 = 68
# z2 = 855
# # # cart 1 (hay)
# x1 = 278
# y1 = 71
# z1 = 721
# x2 = 282
# y2 = 74
# z2 = 724
# # # castle 1 (misc)
# x1 = 231
# y1 = 122
# z1 = 806
# x2 = 251
# y2 = 158
# z2 = 835
# # med_house_4
# x1 = 257
# y1 = 111
# z1 = 777
# x2 = 267
# y2 = 129
# z2 = 791
# # small_house 2 (meat, books)
# x1 = 339
# y1 = 55
# z1 = 822
# x2 = 349
# y2 = 71
# z2 = 831

# # Sector test 1
x1 = 0
y1 = 63
z1 = 0
x2 = 2
y2 = 66
z2 = 2

file_name = "../schemes/Sector_test_2"
src.scheme_utils.download_schematic(x1, y1, z1, x2, y2, z2, file_name)
# src.scheme_utils.download_schematic(x1, y1, z1, x2, y2, z2, file_name+"_flex", flexible_tiles=True, leave_dark_oak=False)
# src.scheme_utils.download_schematic(x1, y1, z1, x2, y2, z2, file_name+"_flex_keep_dark", flexible_tiles=True, leave_dark_oak=True)

# src.scheme_utils.place_schematic_in_world(file_name, x2, y2 + y2 - y2 + 5, z2, dir_z=-1)

# src.scheme_utils.download_schematic(x1, 62, z1, -7, x2, z2, file_name + ".in")
# src.scheme_utils.download_heightmap(worldSlice, file_name +"hm")

# place_schematic_in_world("market_tent_1", 293, 62, 855)
