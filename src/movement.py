from setup import BUILD_DIR
import ctypes
from src.c_utils import open_lib, build_func
from glob import glob

import numpy


class Movement:
    file_name = "movement"
    file = glob("{b}/*/{f}*.so".format(b=BUILD_DIR,f=file_name))[0]

    def __init__(self):
        lib = open_lib(self.file)
        build_func(lib.mysum,ctypes.c_longlong, [ctypes.c_int,
                        numpy.ctypeslib.ndpointer(dtype=numpy.int32)] )
        self.mysum = lib.mysum


        array = numpy.arange(0, 100000000, 1, numpy.int32)
        # 3. call function mysum
        array_sum = lib.mysum(len(array), array)
        print('sum of array: {}'.format(array_sum))

