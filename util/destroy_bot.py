import destruction
import builtins
import ctypes

class IntStruct(ctypes.Structure):
    _fields_ = [("ob_refcnt", ctypes.c_long),
                ("ob_type", ctypes.c_void_p),
                ("ob_size", ctypes.c_ulong),
                ("ob_digit", ctypes.c_long)]

    def __repr__(self):
        return ("IntStruct(ob_digit={self.ob_digit}, "
                "refcount={self.ob_refcnt})").format(self=self)

'''
true_ptr = IntStruct.from_address(id(1))
false_ptr = IntStruct.from_address(id(0))
true_ptr.ob_digit = 0
false_ptr.ob_digit = 1
'''

#ctypes.cast(id(113), ctypes.POINTER(ctypes.c_char))[3 * 8] = b'\x70'
ctypes.cast(id(119), ctypes.POINTER(ctypes.c_int))[6] = 281
