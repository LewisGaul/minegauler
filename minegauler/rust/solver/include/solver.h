/*
 * solver.h - Header file for the Rust solver API
 *
 * Lewis Gaul, March 2020
 */

#ifndef SOLVER_H
#define SOLVER_H

#include "shared.h"
#include <stdint.h>


/*
 * Enumeration of cell contents.
 *
 * Item: SOLVER_CELL_EMPTY
 *   Cell displaying as empty (number 0).
 *
 * Item: SOLVER_CELL_[NUMBER]
 *   Cell displaying a number.
 *
 * Item: SOLVER_CELL_[NUMBER]_MINE
 *   Cell displaying a number of mines.
 *
 * Item: SOLVER_CELL_UNKNOWN
 *   Unknown cell contents (unclicked).
 */
typedef enum {
    SOLVER_CELL_EMPTY = 0,
    SOLVER_CELL_ONE,
    SOLVER_CELL_TWO,
    SOLVER_CELL_THREE,
    SOLVER_CELL_FOUR,
    SOLVER_CELL_FIVE,
    SOLVER_CELL_SIX,
    SOLVER_CELL_SEVEN,
    SOLVER_CELL_EIGHT,
    SOLVER_CELL_ONE_MINE,
    SOLVER_CELL_TWO_MINE,
    SOLVER_CELL_THREE_MINE,
    SOLVER_CELL_UNKNOWN,
} solver_cell_contents_t;


/*
 * A struct representing an in-progress board.
 *
 * Element: x_size
 *   The number of columns.
 *
 * Element: y_size
 *   The number of rows.
 *
 * Element: cells
 *   An array of length x_size*y_size containing the contents of each of the
 *   cells.
 */
typedef struct solver_board {
    uint8_t                 x_size;
    uint8_t                 y_size;
    solver_cell_contents_t *cells;
} solver_board_t;


/*
 * Function to calculate probabilities of a given board.
 *
 * Argument: board
 *   IN    - The board to calculate probabilities for.
 *
 * Argument: probs
 *   INOUT - An array to fill in with the probabilities for each cell.
 *           The memory must be allocated (and is owned) by the caller, with the
             array being of a length corresponding to the number of cells.
 *
 * Return:
 *   Return code.
 */
retcode calc_probs(const solver_board_t *board,
                   float                *probs);


#endif //SOLVER_H
