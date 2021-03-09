"""
Utilities for (height)maps
"""
import cv2
import matplotlib.pyplot as plt
import numpy as np

def normalize(array):
    """Normalizes the array so that the min value is 0 and the max value is 1
    """
    return (array - array.min()) / (array.max() - array.min())

def visualize(*arrays, title=None, autonormalize=True):
    """Uses pyplot and OpenCV to visualize one or multiple numpy arrays

    Args:
        title (str, optional): display title. Defaults to None.
        autonormalize (bool, optional): Normalizes the array to be between 0 (black) and 255 (white). Defaults to True.
    """
    for array in arrays:
        if autonormalize:
            array = (normalize(array) * 255).astype(np.uint8)

        plt.figure()
        if title:
            plt.title(title)
        plt_image = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
        imgplot = plt.imshow(plt_image)
    plt.show()

def calcGoodHeightmap(worldSlice):    
    """Calculates a heightmap that is well suited for building. It ignores any logs and leaves and treats water as ground.

    Args:
        worldSlice (WorldSlice): an instance of the WorldSlice class containing the raw heightmaps and block data

    Returns:
        any: numpy array containing the calculated heightmap
    """
    hm_mbnl = worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
    heightmapNoTrees = hm_mbnl[:]
    area = worldSlice.rect

    for x in range(area[2]):
        for z in range(area[3]):
            while True:
                y = heightmapNoTrees[x, z]
                block = worldSlice.getBlockAt((area[0] + x, y - 1, area[1] + z))
                if block[-4:] == '_log':
                    heightmapNoTrees[x,z] -= 1
                else:
                    break

    return np.array(np.minimum(hm_mbnl, heightmapNoTrees))
