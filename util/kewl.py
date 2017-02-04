import builtins

real_dict = builtins.dict
class dict(real_dict):
    def __getattr__(self, an):
        return self[an]

builtins.dict = dict
