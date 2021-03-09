### makes sure buildarea is valid
def correct_area(area):
    if area[0] > area[2]:
        swap_array_elements(area, 0, 2)
    if area[1] > area[3]:
        swap_array_elements(area, 1, 3)


def swap_array_elements(arr, a, b):
    temp = arr[a]
    arr[a] = arr[b]
    arr[b] = temp

