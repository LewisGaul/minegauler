"""
utils.py - General utilities

March 2018, Lewis Gaul
"""

from os.path import dirname, abspath, join


def absdir(fpath):
    return dirname(abspath(fpath))

root_dir = dirname(absdir(__file__))
files_dir = join(root_dir, 'files')



class Struct(dict):
    # Mapping of elements to their defaults.
    elements = {}
    def __init__(self, **kwargs):
        super().__init__()
        for k, v in kwargs.items():
            self[k] = v
        for k, v in self.elements.items():
            if k not in self:
                self[k] = v
                
    def __getitem__(self, name):
        if name in self.elements:
            if name in self:
                return super().__getitem__(name)
            else:
                return None
        else:
            raise KeyError("Unexpected element")
            
    def __setitem__(self, name, value):
        if name in self.elements:
            super().__setitem__(name, value)
        else:
            raise KeyError("Unexpected element")
            
    def __getattr__(self, name):
        if name in self.elements:
            return self[name]
        else:
            raise AttributeError("Unexpected element")
            
    def __setattr__(self, name, value):
        if name in self.elements:
            self[name] = value
        else:
            raise AttributeError("Unexpected element")
        
        
