# ! /usr/bin/python3
"""### Provide tools for placing and getting blocks and more.
This module contains functions to:
* Request the build area as defined in-world
* Run Minecraft commands
* Get the name of a block at a particular coordinate
* Place blocks in the world
"""
__all__ = ['requestBuildArea', 'runCommand',
           'setBlock', 'getBlock',
           'placeBlockBatched', 'sendBlocks', 'setBlockWithData']
# __version__

import requests


def requestBuildArea():
    """**Requests a build area and returns it as an dictionary containing
    the keys xFrom, yFrom, zFrom, xTo, yTo and zTo**"""
    response = requests.get('http://localhost:9000/buildarea')
    if response.ok:
        return response.json()
    else:
        print(response.text)
        return -1


def runCommand(command):
    """**Executes one or multiple minecraft commands (separated by newlines).**"""
    # print("running cmd " + command)
    url = 'http://localhost:9000/command'
    try:
        response = requests.post(url, bytes(command, "utf-8"))
    except ConnectionError:
        return "connection error"
    return response.text

# --------------------------------------------------------- get/set block


def getBlock(x, y, z, includeState = "true"):
    """**Returns the namespaced id of a block in the world.**"""
    url = 'http://localhost:9000/blocks?x={}&y={}&z={}&includeState={}'.format(x, y, z, includeState)
    # print(url)
    try:
        response = requests.get(url)
    except ConnectionError:
        return "minecraft:void_air"
    return response.text
    # print("{}, {}, {}: {} - {}".format(x, y, z, response.status_code, response.text))


def setBlock(x, y, z, str, includeState="true"):
    """**Places a block in the world.**"""
    url = 'http://localhost:9000/blocks?x={}&y={}&z={}&includeState={}'.format(x, y, z, includeState)
    # print('setting block {} at {} {} {}'.format(str, x, y, z))
    try:
        response = requests.put(url, str)
    except ConnectionError:
        return "0"
    return response.text
    # print("{}, {}, {}: {} - {}".format(x, y, z, response.status_code, response.text))


# --------------------------------------------------------- block buffers

blockBuffer = []


def placeBlockBatched(x, y, z, str, limit=50):
    """**Place a block in the buffer and send if the limit is exceeded.**"""
    registerSetBlock(x, y, z, str)
    if len(blockBuffer) >= limit:
        return sendBlocks(0, 0, 0)
    else:
        return None


def sendBlocks(x=0, y=0, z=0, retries=5):
    """**Sends the buffer to the server and clears it.**"""
    global blockBuffer
    body = str.join("\n", ['~{} ~{} ~{} {}'.format(*bp) for bp in blockBuffer])  # where bp has xyz and type
    url = 'http://localhost:9000/blocks?x={}&y={}&z={}'.format(x, y, z)
    try:
        response = requests.put(url, body)
        clearBlockBuffer()
        return response.text
    except ConnectionError as e:
        print("Request failed: {} Retrying ({} left)".format(e, retries))
        if retries > 0:
            return sendBlocks(x, y, z, retries - 1)


def registerSetBlock(x, y, z, str):
    """**Places a block in the buffer.**"""
    global blockBuffer
    # blockBuffer += () '~{} ~{} ~{} {}'.format(x, y, z, str)
    blockBuffer.append((x, y, z, str))


def clearBlockBuffer():
    """**Clears the block buffer.**"""
    global blockBuffer
    blockBuffer = []


# use this if designated in file by {}
def setBlockWithData(abs_x, abs_y, abs_z, data):
    command = "setblock {} {} {} {}".format(abs_x, abs_y, abs_z, data)
    return runCommand(command)


