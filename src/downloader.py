#! /usr/bin/python3
"""
Downloads buildings from a running MC world into a file
"""
__all__ = []
__author__ = "aith"
__version__ = "1.0"

import src.scheme_utils

areaFlex = [0, 0, 10, 10] # default build area
x1 = 296
y1 = 78
z1 = 810
x2 = 307
y2 = 93
z2 = 820

file_name = "../schemes/test_building"
src.scheme_utils.download_schematic(x1, y1, z1, x2, y2, z2, file_name)
src.scheme_utils.download_schematic(x1, y1, z1, x2, y2, z2, file_name+"_flex", flexible_tiles=True, leave_dark_oak=False)
