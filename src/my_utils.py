### returns a tuple of coordinates, with the lower x and z values first
def correct_area(area):
    if area[0] > area[2]:
        swap_array_elements(area, 0, 2)
    if area[1] > area[3]:
        swap_array_elements(area, 1, 3)
    return (area[0], area[1], area[2], area[3])


def swap_array_elements(arr, a, b):
    temp = arr[a]
    arr[a] = arr[b]
    arr[b] = temp

