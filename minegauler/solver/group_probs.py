"""
group_probs.py - Calculate probabilities and combinations in groups of cells

June 2019, Lewis Gaul

Exports:
get_unsafe_probs (function)
    Get probability of a single cell containing a mine in a group of cells.
calculate_arrangements (function)
    Get number of arrangements for mines in a group of cells.
generate_arrangements (function)
    Get list of arrangements for mines in a group of cells.
"""

from math import exp, factorial, log
from typing import List


def get_unsafe_prob(mines: int, cells: int, per_cell: int = 1) -> float:
    """
    Get the probability that a single cell in a group of cells contains a mine, given a number of
    mines, number of cells and maximum number of mines per cell.

    Arguments:
    mines (int >= 0)
        The number of mines.
    cells (int > 0)
        The number of cells.
    per_cell (int > 0)
        The maximum number of mines allowed in any single cell.

    Return: 0 <= float <= 1
        The probability that a single cell in the group contains a mine.

    Raise:
    ValueError
        If the number of mines is too high for the amount of space in the cells.
    """
    if mines > cells*per_cell:
        raise ValueError(
            f"Too many mines for the space in the cells - {mines} mines, {cells} cells and "
            f"{per_cell} max per cell ({cells*per_cell} spaces)")
    # Not possible for a cell not to contain a mine.
    elif mines > per_cell*(cells - 1):
        return 1
    # Simple calculation with only 1 mine allowed per cell.
    elif per_cell == 1:
        return mines / cells
    # Max per cell effectively infinite - makes calculation straightforward.
    elif per_cell >= mines:
        return 1 - (1 - 1/cells)**mines
    # Otherwise have to do the slow counting operation...
    else:
        # Use exp and log to avoid having to divide large integers - equivalent to
        # 1 - calc(m, c-1, p)/calc(m, c, p). This works because the probability of a cell containing
        # a mine is equal to 1 - [probability of a cell being safe].
        return 1 - exp(log(calculate_arrangements(mines, cells-1, per_cell)) -
                       log(calculate_arrangements(mines, cells, per_cell)))


def calculate_arrangements(mines: int, cells: int, per_cell: int = 1) -> int:
    """
    Calculate the number of ways to arrange mines in a number of cells (each mine treated as
    distinct).

    Arguments:
    mines (int >= 0)
        The number of mines.
    cells (int > 0)
        The number of cells.
    per_cell (int > 0)
        The maximum number of mines allowed in any single cell.

    Return: int >= 0
        The number of ways to arrange the mines.
    """
    # More mines than there's space for.
    if mines > cells*per_cell:
        return 0
    # No mines or all mines in the same cell.
    elif mines == 0 or cells == 1:
        return 1
    # Simple calculation for one mine max per cell.
    elif per_cell == 1:
        return factorial(cells) // factorial(cells - mines)
    # Simple calculation if there's effectively no limit to number of mines per cell.
    elif per_cell >= mines:
        return cells**mines
    # Otherwise have to do the slow counting operation...
    else:
        ret = 0
        cells_numerator = factorial(cells)
        mines_numerator = factorial(mines)
        for comb in generate_combinations(mines, cells, per_cell):
            # Count the occurrences of each number across all cells for this combination to
            # calculate the number of ways to arrange the numbers in the cells.
            # E.g. [3, 3, 0, 0, 0] has the number '3' accurring twice and the number '0' three
            # times, so there are 5!/(2!3!) ways of arranging these numbers in these cells.
            numbers_in_cells_arrangements = cells_numerator
            for count in [comb.count(n) for n in set(comb)]:
                numbers_in_cells_arrangements //= factorial(count)
            # Calculate the number of ways to arrange the mines in the numbers of this combination.
            # E.g. [4, 2, 0] has 6 mines which are arranged into a cell of 4 and a cell of 2, so
            # there are 6!/(4!2!) ways of arranging the mines in this way.
            mines_in_numbers_arrangements = mines_numerator
            for num in comb:
                mines_in_numbers_arrangements //= factorial(num)

            ret += numbers_in_cells_arrangements * mines_in_numbers_arrangements

        return ret


def generate_combinations(mines, cells, max_per_cell, *, min_per_cell=1) -> List[List[int]]:
    """
    Get the list of unique ways to arrange a number of mines in a number of cells.

    Note that (max_per_cell=infinity, min_per_cell=1) gives all possibilities, and this is bisected
    with (max_per_cell=x, min_per_cell=1) and (max_per_cell=infinity, min_per_cell=x+1). Depending
    on which gives less combinations, and given that the number of combinations with no restriction
    may be a trivial calculation, one of the bisection options may be more performant than the
    other.

    Arguments:
    mines (int >= 0)
        The number of mines.
    cells (int > 0)
        The number of cells.
    max_per_cell (int > 0)
        The maximum number of mines allowed in any single cell.
    min_per_cell (int > 0)
        The minimum number of mines that must exist in at least one of the cells.

    Return: [[int >= 0, ...], ...]
        The ways to arrange the mines, represented as a list of assignments of a number of mines to
        each cell, e.g. [[2, 1, 1], [2, 2, 0], [3, 1, 0], [4, 0, 0]] for 4 mines in 3 cells.

    Raise:
    ValueError
        If the number of mines is too high for the space in the cells.
    """
    # Note: Could be sped up by using bytearrays if required?
    if mines > cells * max_per_cell:
        raise ValueError(
            f"Too many mines for the max allowed in the cells - mines: {mines}, cells: {cells}, "
            f"max_per_cell: {max_per_cell}")
    if cells == 1:
        return [[mines]]
    if mines == 0:
        return [[0]*cells]
    ret = []
    # Loop over possible numbers of mines in the next cell.
    range_min = max(min_per_cell, (mines - 1) // cells + 1)
    range_max = min(mines, max_per_cell)
    for n in range(range_min, range_max + 1):
        # Recurse.
        new_max_per_cell = min(max_per_cell, n)
        ret += [[n] + ns for ns in generate_combinations(mines - n, cells - 1, new_max_per_cell)]

    return ret
