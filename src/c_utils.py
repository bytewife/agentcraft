import ctypes

def open_lib(lib_file):
    return ctypes.CDLL(lib_file)


def build_func(func, ret_type, arg_types):
    """
    Allow Python to use C/C++ function. Requires the lib be open with open_lib()
    :param ret_type: the return type
    :param arg_types: (Array of ctypes types) The types of each parameter
    :return:
    """
    func.restype = ret_type
    func.argtypes = arg_types

