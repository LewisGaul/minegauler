# Solver Design

This document contains an implementation-level design of the Minegauler solver package.


## Probability Calculation

### Finding Equivalence Groups

TODO


### Finding Mine Configurations

TODO


### Calculating the Probabilities

TODO


## Sketch Implementation

A sketch of the implementation is given below, using a Rust-like syntax to give a view of relevant APIs and their usage.


There's an underlying grid type to model the 2-dimensional grid. There are then two types wrapping this: the board that we're working out probabilities for and the grid of probabilities for the board. At the highest-level view this is enough to encapsulate what we want to achieve: to map an in-progress game board to a grid of probabilities.

```rust
struct Grid<T> {
    fn cell(coord: Coord) -> T;
    fn all_coords() -> Vec<Coord>;
    fn nbr_coords(coord: Coord) -> Vec<Coord>;
}

struct Board : Grid<BoardCellContents> {
    mines: u32,    // number of mines
    per_cell: u32, // max mines per cell
    // 'Inherit' Grid methods
}

type ProbabilityGrid = Grid<f32>;
```


The first step in the process is to reduce the board into a structure that can be worked with more easily. We create a new type to represent this restructured data, which has been decomposed from grid form.

\[Note: We're actually skipping an optional step here of reducing the board by applying solver logic, e.g. if a number '1' is only next to one unclicked cell.\]

```rust
struct DecomposedBoard {
    mines: u32,
    // Note the per_cell restriction is encapsulated in the groups.
    groups: Vec<BoardGroup>,
    numbers: Vec<BoardNumber>,
    
    fn get_group(coord: Coord) -> Option<&BoardGroup>;
    fn get_number(coord: Coord) -> Option<&BoardNumber>;
}

struct BoardGroup {
    // Coordinates of the unclicked cells in the equivalence group.
    coords: Vec<Coord>,
    // Neighbouring cells displaying a number.
    nbr_numbers: Vec<&Number>,
    // Max number of mines that can be contained in the group.
    max_mines: u32,
}

struct BoardNumber {
    coord: Coord,            // coord of the number cell
    value: u32,              // value of the number
    nbr_groups: Vec<&Group>, // neighbouring groups
}
```

```rust
fn decompose_board(board: &Board) -> DecomposedBoard {
    let mut decomp = DecomposedBoard::new(board.mines);
    
    // This will be a mapping of unclicked cell coords to coords of
    // neighbouring numbers: {(x, y): [(a, b), (c, d), ...], ... }
    let mut unclicked_cell_nbr_nums = HashMap::new();
    
    for (num_coord, num_val) in board.iter_num_cells() {
        // We only care about numbers next to unclicked cells.
        for unclicked in board.unclicked_nbr_coords() {
            unclicked_cell_nbr_nums[unclicked].push(num_coord)
        }
    }

    // Remap to {[(a, b), ...]: [(x, y), ...], ... }
    let nums_to_groups = unclicked_cell_nbr_nums.group_by_value();
    for (num_coords, group_coords) in nums_to_groups {
        let mut group = BoardGroup::new(group_coords);
        for num_coord in num_coords {
            // Create BoardNumber if not yet created.
            let mut number: &BoardNumber = decomp.get_or_add_number(num_coord);
            // Store references between numbers and groups.
            group.numbers.push(number);
            number.groups.push(&group);
        }
        decomp.groups.push(group);
    }
    
    decomp
}
```


Now the most complex (and compuatationally slow) step - we need to take this reduced representation and find all possible ways to place mines in the equivalence groups of unclicked cells.

```rust
struct Combinations {
    // Equivalence groups (to be moved from ReducedBoard).
    groups: Vec<Vec<Coord>>,     // X cells, Y groups
    // A single combination has length equal to the number of groups.
    combinations: Vec<Vec<u32>>, // Y groups, Z combinations
}
```

```rust
fn find_combinations(board: DecomposedBoard) -> Combinations {
    /*
     * Example of what we have here:
     *
     *   # 2 # # #       . 2 . . M .
     *   # # # # #       . M M . . .
     *   # 3 # # #       . 3 . M M .
     *   # 2 # 4 #       M 2 . 4 M .
     *   # # # # #       . . M . . .
     *
     * DecomposedBoard {
     *   mines: 8,
     *   numbers: [
     *     {(1,0), 2, groups: [0, 1]},
     *     {(1,2), 3, groups: [1, 2, 4]},
     *     {(1,3), 2, groups: [2, 3, 4, 5]},
     *     {(3,3), 4, groups: [4, 5, 6]},
     *   ],
     *   groups: [
     *     {[(0,0), (2,0)], numbers: [0], max: 2},
     *     {[(0,1), (1,1), (2,1)], numbers: [0, 1], max: 2},
     *     {[(0,2), (0,3)], numbers: [1, 2], max: 2},
     *     {[(0,4), (1,4)], numbers: [2], max: 2},
     *     {[(2,2), (2,3)], numbers: [1, 2, 3], max: 2},
     *     {[(2,4)], numbers: [2, 3], max: 2},
     *     {[(3,2), (3,4), (4,2), (4,3), (4,4)], numbers: [3], max: 4},
     *   ],
     * }
     *
     * There are 7 groups, meaning combinations will have 7 slots to fill.
     * Combinations: [
     *   (0, 2, 0, 0, 1, 1, 2),
     *   (0, 2, 0, 1, 1, 0, 3),
     *   (0, 2, 1, 0, 0, 1, 3),   # shown above
     *   (0, 2, 1, 1, 0, 0, 4),
     *   (1, 1, 0, 0, 2, 0, 2),
     *   (1, 1, 1, 0, 1, 0, 3),
     *   (1, 1, 2, 0, 0, 0, 4),
     * ]
     *
     * These are actually just non-negative integer solutions to the following
     * simultaneous equations:
     *  1) g0 + g1 = 2
     *  2) g1 + g2 + g4 = 3
     *  3) g2 + g3 + g4 + g5 = 2
     *  4) g4 + g5 + g6 = 4
     * subject to:
     *  0 <= g0 <= 2
     *  0 <= g1 <= 2
     *  0 <= g2 <= 2
     *  0 <= g3 <= 2
     *  0 <= g4 <= 2
     *  0 <= g5 <= 2
     *  0 <= g6 <= 4
     *
     * This can alternatively be written as the matrix equation:
     *  |1, 1, 0, 0, 0, 0, 0|        |2|
     *  |0, 1, 1, 0, 1, 0, 0|        |3|
     *  |0, 0, 1, 1, 1, 1, 0|  x g = |2|
     *  |0, 0, 0, 0, 1, 1, 1|        |4|
     *
     * Reducing these equations down gives:
     * (2) - (3): g1 = g3 + g5 + 1  =>  g1 >= 1  and  g3, g5 <= 1
     * (4) - (3): g6 = g2 + g3 + 2  =>  g6 >= 2
     */
}
```


Finally we need to convert these combinations into a grid of probabilities.

```rust
fn find_probabilities(combs: &Combinations, per_cell: u32) -> ProbabilityGrid {
    
}
```
