from .minefield import RegularMinefield


mf = RegularMinefield.from_dimensions(4, 6, mines=5, per_cell=3)
mf.populate()
print(mf)
print("3bv:", mf.bbbv)
print("Completed board:", mf.completed_board, sep="\n")
