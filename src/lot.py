import src.my_utils

class Lot:
    def __init__(self, state, points):
        self.state = state
        self.get_lot(points)

    def get_pt_avg(self, points):
        x = sum(x for (x, y) in points) / len(points)
        y = sum(y for (x, y) in points) / len(points)
        return (x, y)

    def get_lot(self, points):
        [pt1, pt2] = points

        (ax, ay) = self.get_pt_avg(points)
        bx, by = (int(ax), int(ay))
        self.center = (cx, cy) = self.state.node_pointers[(bx, by)]
        center_node = self.state.nodes(cx, cy)

        lot = set([center_node])
        self.border = set()
        while True:
            neighbors = set([e for n in lot for e in n.adjacent() if \
                             e not in lot and e.lot is None and e.center[0] != pt1[0] and e.center[0] != pt2[0] and
                             e.center[1] != pt1[1] and e.center[1] != pt2[1] \
                             and src.my_utils.TYPE.WATER.name not in e.mask_type])
            if len(neighbors) > 0:
                lot.update(neighbors)
                self.border = neighbors
            else:
                break

        for node in lot:
            node.lot = self
        self.nodes = lot
