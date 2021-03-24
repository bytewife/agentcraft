from src.http_framework.worldLoader import WorldSlice
from src.my_utils import *
from src.scheme_utils import *
from src.states import *
areaFlex = [0, 0, 10, 10] # default build area
# you can set a build area in minecraft using the /setbuildarea command
buildArea = requestBuildArea()
if buildArea != -1:
    x1 = buildArea["xFrom"]
    z1 = buildArea["zFrom"]
    x2 = buildArea["xTo"]
    z2 = buildArea["zTo"]
    areaFlex = [x1, z1, x2-x1, z2-z1]

area = correct_area(areaFlex)
worldSlice = WorldSlice(area)  #_so area is chunks?

area = (0,0,128,128)

download_schematic(293, 62, 844, 300, 65, 839, "market_tent_1")
place_schematic_in_world("market_tent_1", 293, 62, 855)
