import src.movement_backup

start = (100, 20)
targets = (
    (100, 20),
    (0,1),
    (2,0),
    (60, 20),
    (10, 10)
)
print(src.movement_backup.sort_by_distance(*start, targets))