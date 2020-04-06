/*
 * probs.rs - Probability calculations
 *
 * Lewis Gaul, March 2020
 */

use bindings;
use utils::{Board, BoardProbs, CellContents};

use std::convert::TryFrom;
use std::ptr;

// -----------------------------------------------------------------------------
// Exposed C API

/// See solver.h for the C API being implemented.
#[no_mangle]
pub unsafe extern "C" fn calc_probs(
    c_board: *const bindings::solver_board_t,
    c_probs: *mut f32,
) -> bindings::retcode {
    // Check args are non-null, and just hope the pointers are otherwise valid!
    if c_board.is_null() || c_probs.is_null() {
        eprintln!("ERROR: Invalid NULL pointer passed in");
        return bindings::RC_INVALID_ARG;
    }

    // Convert C board struct to Rust struct.
    let c_board: bindings::solver_board_t = c_board.read();
    if c_board.cells.is_null() {
        eprintln!("ERROR: Invalid board arg");
        return bindings::RC_INVALID_ARG;
    }

    let board = match Board::try_from(c_board) {
        Ok(b) => b,
        Err(_) => {
            eprintln!("ERROR: Invalid board arg");
            return bindings::RC_INVALID_ARG;
        }
    };
    // println!("Board: {} x {}", board.x_size, board.y_size);
    let probs: BoardProbs = board.calc_probs();

    // println!("Probs: ");
    for (i, (_, p)) in probs.iter_cells().enumerate() {
        // println!("{}- {}", i+1, p);
        ptr::write(c_probs.add(i), *p);
    }

    bindings::RC_SUCCESS
}

// -----------------------------------------------------------------------------
// Helpers

impl TryFrom<bindings::solver_cell_contents_t> for CellContents {
    type Error = ();

    fn try_from(c_contents: bindings::solver_cell_contents_t) -> Result<Self, Self::Error> {
        use bindings::*;
        match c_contents {
            SOLVER_CELL_UNCLICKED => Ok(Self::Unclicked),
            0..=SOLVER_CELL_EIGHT => Ok(Self::Num(c_contents)),
            SOLVER_CELL_ONE_MINE | SOLVER_CELL_TWO_MINE | SOLVER_CELL_THREE_MINE => {
                Ok(Self::Mine(c_contents - SOLVER_CELL_ONE_MINE + 1))
            }
            _ => Err(()),
        }
    }
}

impl TryFrom<bindings::solver_board_t> for Board {
    type Error = ();

    fn try_from(c_board: bindings::solver_board_t) -> Result<Self, Self::Error> {
        let mut board = Self::new(c_board.x_size as u32, c_board.y_size as u32);
        unsafe {
            for i in 0..(c_board.x_size * c_board.y_size) as usize {
                let c_contents = c_board.cells.add(i).read();
                let contents = CellContents::try_from(c_contents)?;
                board.set_cell(board.coord_from_index(i), contents);
            }
        }
        Ok(board)
    }
}

// -----------------------------------------------------------------------------
// Tests

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn calc_probs_invalid_args() {
        unsafe {
            let rc = super::calc_probs(ptr::null(), ptr::null_mut());
            assert_eq!(rc, bindings::RC_INVALID_ARG);
        }
    }

    // #[test]
    // fn calc_probs_valid_args() {
    //     unsafe {
    //         let rc = calc_probs();
    //         assert_eq!(rc, bindings::RC_SUCCESS);
    //     }
    // }
}
