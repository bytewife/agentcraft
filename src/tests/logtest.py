import src.states
import src.scheme_utils
import src.manipulation

state = src.states.State(blocks_file="logtest.in")
# print(state.assets[1][3][1])
# print(state.assets)

src.manipulation.cut_tree_at(state, 1, 3, 1, 1)
src.scheme_utils.array_XYZ_to_schema(state.blocks, state.len_x, state.len_y, state.len_z, "logtest.out")
print("logtest complete")
