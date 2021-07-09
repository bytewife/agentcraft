class RoadSegment:
    def __init__(self, rnode1, rnode2, nodes, type, rslist, state):
        self.start = rnode1
        self.end = rnode2
        self.type = type
        self.shape = []
        self.nodes = nodes

    def merge(self, rs2, match, rs_list, roadnodes):
        if self.type != rs2.mask_type:
            return
        if self.start == match:
            self.shape.reverse()
            self.start = self.end
        self.shape.append((match.x, match.y))
        self.nodes.append((match.x, match.y))
        if rs2.end == match:
            rs2.shape.reverse()
            rs2.end = rs2.start
        self.shape.extend(rs2.shape)
        self.nodes.extend(rs2.nodes)
        self.end = rs2.end
        rs_list.discard(rs2)
        roadnodes.remove(match)
        roadnodes.remove(match)

    def split(self, node, rs_list, roadnodes, state):
        roadnodes.append(node)
        roadnodes.append(node)

        i = 0
        while i < len(self.nodes) - 1:
            if self.nodes[i] == (node.center[0], node.center[1]):
                break
            i += 1
        nodes1 = self.nodes[:i]
        nodes2 = self.nodes[i + 1:]

        new_rs = RoadSegment(node, self.end, nodes2, self.type, roadnodes, state=state)
        rs_list.add(new_rs)

        self.nodes = nodes1
        self.end = node

