import heapq
from math import sqrt

def get_path(x1, z1, x2, z2):
    pass

def heuristic(self, x1, z1, x2, z2):
    return round(sqrt((x1 - x2) ** 2 + (z1 - z2) ** 2) * self.basecost)
