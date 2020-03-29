/*
 * probs.rs - Probability calculations
 *
 * Lewis Gaul, March 2020
 */

use bindings;
use std::ptr;

// ----------------
// Exposed C API

#[no_mangle]
pub unsafe extern "C" fn hello() {
    println!("Hello, world!");
}

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

fn calc_probs_impl(board: bindings::solver_board_t) -> Vec<f32> {
    vec![3.1, 4.5]
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
