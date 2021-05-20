#! /usr/bin/python3
"""### Downloads buildings from a running MC world into a file

"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"


import src.scheme_utils
# import src.my_utils
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
# x1 = 0
# y1 = 63
# z1 = 0
# x2 = 2
# y2 = 66
# z2 = 2

# # tiny house 1
# x1 = 155
# y1 = 95
# z1 = -45
# x2 = 163
# y2 = 102
# z2 = -37


# tiny house 2
# x1 = 153
# y1 = 90
# z1 = -61
# x2 = 159
# y2 = 100
# z2 = -53


# cart 2
# x1 = 131
# y1 = 88
# z1 = -49
# x2 = 136
# y2 = 90
# z2 = -45


# small house 3 (cabin from ire)
# x1 = 134
# y1 = 95
# z1 = -59
# x2 = 142
# y2 = 105
# z2 = -48


# tiny house 3 (next to armorery from ire)
# x1 = 144
# y1 = 108
# z1 = -13
# x2 = 152
# y2 = 119
# z2 = -5


# tiny house 4 (armory)
# x1 = 161
# y1 = 113
# z1 = -22
# x2 = 169
# y2 = 120
# z2 = -14


# storage 1
# x1 = 172
# y1 = 105
# z1 = -40
# x2 = 177
# y2 = 111
# z2 = -32

# # ornamental tree 1
# x1 = 199
# y1 = 114
# z1 = -74
# x2 = 201
# y2 = 121
# z2 = -72


# # cart 3
# x1 = 205
# y1 = 120
# z1 = -75
# x2 = 210
# y2 = 122
# z2 = -71

# # # market stall 3
# x1 = 177
# y1 = 66
# z1 = 252
# x2 = 182
# y2 = 70
# z2 = 257


# # # med house 5
# x1 = 130
# y1 = 50
# z1 = 168
# x2 = 140
# y2 = 60
# z2 = 178

# # # bell
# x1 = 62
# y1 = 50
# z1 = 180
# x2 = 64
# y2 = 56
# z2 = 182


# # # hay 1
# x1 = 25
# y1 = 39
# z1 = 168
# x2 = 27
# y2 = 41
# z2 = 170

# # # small house 4
# x1 = 39
# y1 = 57
# z1 = 160
# x2 = 47
# y2 = 72
# z2 = 169

# # # # logs 1
# x1 = 41
# y1 = 57
# z1 = 183
# x2 = 43
# y2 = 58
# z2 = 185


# # # tower 1
# x1 = 63
# y1 = 53
# z1 = 221
# x2 = 71
# y2 = 87
# z2 = 227

# # # # lamp 1
# x1 = 145
# y1 = 49
# z1 = 195
# x2 = 147
# y2 = 57
# z2 = 197

# # # # lamp 2
# x1 = 143
# y1 = 53
# z1 = 187
# x2 = 145
# y2 = 60
# z2 = 189

file_name = "../schemes/tiny_house_1"
src.scheme_utils.download_schematic(x1, y1, z1, x2, y2, z2, file_name)
src.scheme_utils.download_schematic(x1, y1, z1, x2, y2, z2, file_name+"_flex", flexible_tiles=True, leave_dark_oak=False)
