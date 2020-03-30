/*
 * probs.rs - Probability calculations
 *
 * Lewis Gaul, March 2020
 */

use bindings;
use std::ptr;

// ----------------
// Exposed C API

/// See solver.h for the C API being implemented.
#[no_mangle]
pub unsafe extern "C" fn calc_probs(
    c_board: *const bindings::solver_board_t,
    c_probs: *mut f32,
) -> bindings::retcode {
    // Check args are non-null, and just hope the pointers are otherwise valid!
    if c_board.is_null() || c_probs.is_null() {
        eprintln!("Invalid NULL pointer passed in");
        return bindings::RC_INVALID_ARG;
    }

    let board = c_board.read();
    if board.x_size <= 0 || board.y_size <= 0 || board.cells.is_null() {
        eprintln!("Invalid board arg");
        return bindings::RC_INVALID_ARG;
    }

    // println!("Board: {} x {}", board.x_size, board.y_size);
    let probs: Vec<f32> = calc_probs_impl(board);

    // println!("Probs: ");
    for (i, p) in probs.iter().enumerate() {
        // println!("{}- {}", i+1, p);
        ptr::write(c_probs.add(i), *p);
    }

    bindings::RC_SUCCESS
}

// ----------------
// Rust implementation

/// Rust implementation of `calc_probs()`.
fn calc_probs_impl(board: bindings::solver_board_t) -> Vec<f32> {
    print_board(board);
    vec![3.1, 4.5]
}

// ----------------
// Helpers

fn print_board(board: bindings::solver_board_t) {
    for i in 0..board.x_size {
        for j in 0..board.y_size {
            let offset = (i + board.x_size * j) as usize;
            // print!("{} ", offset);
            let val: bindings::solver_cell_contents_t;
            unsafe {
                val = board.cells.add(offset).read();
            }
            if val == 0 {
                print!(". ");
            } else if val >= 1 && val <= 8 {
                print!("{} ", val);
            } else if val == bindings::SOLVER_CELL_ONE_MINE {
                print!("M ");
            } else if val == bindings::SOLVER_CELL_UNKNOWN {
                print!("# ");
            } else {
                print!("@ ");
            }
        }
        println!();
    }
}

// ----------------
// Tests

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn calc_probs_invalid_args() {
        unsafe {
            let rc = calc_probs(ptr::null(), ptr::null_mut());
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
