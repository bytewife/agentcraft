import src.movement

start = (100, 20)
targets = (
    (100, 20),
    (0,1),
    (2,0),
    (60, 20),
    (10, 10)
)
print(src.movement.sort_by_distance(*start, targets))