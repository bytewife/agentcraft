
## do we wanna cache tree locations? I don't want them to cut down buildings lol
def check_if_tree(state, x, y, z):
    block = state[x][y][z]
    if block[-3:] == 'log':
        return True
    return False

## assumes there's a tree at the location
def cut_tree_at(state, x, y, z):
    state[x][y][z] = "minecraft:air"
    pass
    # if check_if_tree(state, x, y, z)

def get_adjacent_block(x_off, y_off, z_off)