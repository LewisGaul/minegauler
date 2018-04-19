"""
stubs.py - Stubs for the core to use replicating a UI

April 2018, Lewis Gaul
"""


class StubUI:
    def __init__(self, procr):
        self.procr = procr
        procr.ui = self


class StubMinefieldUI:
    def __init__(self, procr):
        self.procr = procr
        procr.mf_ui = self
    def split_cell(self, x, y):
        pass
    def set_cell_image(self, x, y, state):
        pass