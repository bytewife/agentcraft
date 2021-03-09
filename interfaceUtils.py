import requests

def setOneBlock(x, y, z, str):
    url = 'http://localhost:9000/blocks?x=%i&y=%i&z=%i' % (x, y, z)
    # print('setting block %s at %i %i %i' % (str, x, y, z))
    try:
        response = requests.put(url, str)
    except ConnectionError:
        return "0"
    return response.text
    # print("%i, %i, %i: %s - %s" % (x, y, z, response.status_code, response.text))

def getBlock(x, y, z):
    url = 'http://localhost:9000/blocks?x=%i&y=%i&z=%i' % (x, y, z)
    # print(url)
    try:
        response = requests.get(url)
    except ConnectionError:
        return "minecraft:void_air"
    return response.text
    # print("%i, %i, %i: %s - %s" % (x, y, z, response.status_code, response.text))

# BLOCK BUFFER STUFF

blockBuffer = []

# clear the block buffer
def clearBlockBuffer():
    global blockBuffer
    blockBuffer = []

# write a block update to the buffer
def registerSetBlock(x, y, z, str):
    global blockBuffer
    # blockBuffer += () '~%i ~%i ~%i %s' % (x, y, z, str)
    blockBuffer.append((x, y, z, str))

# send the buffer to the server and clear it
def sendBlocks(x=0, y=0, z=0, retries=5):
    global blockBuffer
    body = str.join("\n", ('~%i ~%i ~%i %s' % bp for bp in blockBuffer))
    url = 'http://localhost:9000/blocks?x=%i&y=%i&z=%i' % (x, y, z)
    try:
        response = requests.put(url, body)
        clearBlockBuffer()
        return response.text
    except ConnectionError as e:
        print("Request failed: %s Retrying (%i left)" % (e, retries))
        if retries > 0:
            return sendBlocks(x,y,z, retries - 1)

## Accumulates blocks-to-send in a cache until the limit is reached, and then it sends that cache via the http
def placeBlockBatched(x, y, z, str, limit=50):
    registerSetBlock(x, y, z, str)  
    if len(blockBuffer) >= limit:
        return sendBlocks(0, 0, 0)
    else:
        return None

def runCommand(command):
    # print("running cmd %s" % command)
    url = 'http://localhost:9000/command'
    try:
        response = requests.post(url, bytes(command, "utf-8"))
    except ConnectionError:
        return "connection error"
    return response.text

def requestBuildArea():
    response = requests.get('http://localhost:9000/buildarea')
    if response.ok:
        return response.json()
    else:
        print(response.text)
        return -1
