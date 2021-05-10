# ! /usr/bin/python3
"""### Provides tools for maps and heightmaps.

This module contains functions to:
* Calculate a heightmap ideal for building
* Visualise numpy arrays
"""
__all__ = ['calcGoodHeightmap']
# __version__

import cv2
import matplotlib.pyplot as plt
import numpy as np


def calcGoodHeightmap(worldSlice):
    """**Calculate a heightmap ideal for building**.

    Trees are ignored and water is considered ground.

    Args:
        worldSlice (WorldSlice): an instance of the WorldSlice class
                                 containing the raw heightmaps and block data

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
                block = worldSlice.getBlockAt(
                    area[0] + x, y - 1, area[1] + z)
                if block[-4:] == '_log':
                    heightmapNoTrees[x, z] -= 1
                else:
                    break

    return np.array(np.minimum(hm_mbnl, heightmapNoTrees))


def visualize(*arrays, title=None, autonormalize=True):
    """**Visualizes one or multiple numpy arrays**.

    Args:
        title (str, optional): display title. Defaults to None.
        autonormalize (bool, optional): Normalizes the array to be between
                                        0 (black) and 255 (white).
                                        Defaults to True.
    """
    for array in arrays:
        if autonormalize:
            array = (normalize(array) * 255).astype(np.uint8)

        plt.figure()
        if title:
            plt.title(title)
        plt_image = cv2.cvtColor(array, cv2.COLOR_BGR2RGB)
        imgplot = plt.imshow(plt_image)  # NOQA
    plt.show()


def normalize(array):
    """**Normalize the array to contain values from 0 to 1**."""
    return (array - array.min()) / (array.max() - array.min())
