from states import *
import bitarray

class Directions(Enum):
    N  = 0
    E  = 1
    S  = 2
    W  = 3
    NE = 4
    ES = 5
    SW = 6
    WN = 7
    # N    E      S       W
cardinals = ([1,0],[0,1], [-1,0], [0,-1])
            # NE   ES     SW      WN
diagonals = ([1,1],[-1,1],[-1,-1],[1,-1])
## stored as N  E  S  W  NE ES SW WN
##           0  1  2  3  4  5  6  7


def get_all_legal_actions(blocks, vertical_ability, heightmap, actor_height, unwalkable_blocks):
    rx = len(blocks)
    rz = len(blocks[0][0])
    # print(rx)
    fill = bitarray.bitarray('00000000')
    result = np.full((rx,rz), fill_value=fill, dtype=bitarray.bitarray)
    for x in range(rx):
        for z in range(rz):
            pass
            # print(z)
            result[x][z] = get_legal_actions_from_block(blocks, x, z, vertical_ability, heightmap, actor_height, unwalkable_blocks)
            # ( get_legal_actions_from_block(blocks, x, z, vertical_ability, heightmap, actor_height, unwalkable_blocks))
    return result


def get_legal_actions_from_block(blocks, x, z, vertical_ability, heightmap, actor_height, unwalkable_blocks):
    result = bitarray.bitarray('00000000')
    # the choice of heightmap here is important. It should be the on the ground, not 1 block above imo
    y = heightmap[x][z]
    for n in range(len(cardinals)):
        cardinal = cardinals[n]
        if check_if_legal_move(blocks, x, y, z, *cardinal, vertical_ability, heightmap, actor_height, unwalkable_blocks):
            result[n] = True
    for n in range(len(diagonals)):
        if result[n] is True and result[(n+1) % len(cardinals)] is True:  # Make sure the surrounding walls of the diagonal are passable to avoid skipping
            diagonal = diagonals[n]
            if check_if_legal_move(blocks, x, y, z, *diagonal, vertical_ability, heightmap, actor_height, unwalkable_blocks):
                result[n + 4] = True
    return result


def check_if_legal_move(blocks, x, y, z, x_offset, z_offset, vertical_ability, heightmap, actor_height, unwalkable_blocks):
    target_x = x + x_offset
    target_z = z + z_offset
    if (target_x < 0 or target_z < 0 or target_x >= len(blocks) or target_z >= len(blocks[0][0])):
        return False
    target_y = heightmap[target_x][target_z]  # make sure that the heightmap starts from the ground
    target_block = blocks[target_x][target_y][target_z]
    if target_block in unwalkable_blocks: return False
    y_diff = abs(y - target_y)
    if y_diff > vertical_ability: return False
    is_legal = True
    for i in range(actor_height):
        target = blocks[x][target_y + 1 + i][z]  # the +1 to move to tile above groudn
        if not (target in Type_Tiles.tile_sets[Type.AIR.value]):
            is_legal = False
            break
    if is_legal:
        return True
    return False

