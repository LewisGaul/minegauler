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
    // Check args
    // if c_board.is_null() || c_probs.is_null() {
    //     return bindings::RC_INVALID_ARG;
    // }

    // We know the pointers are non-null, we just hope they are otherwise valid!
    let board = c_board; //.read();
    let probs: Vec<f32> = calc_probs_impl(board);

    print!("Probs: ");
    for p in probs {
        print!("{} ", p);
        // ptr::write(c_probs, p);
    }
    println!();

    bindings::RC_SUCCESS
}

// ----------------
// Rust implementation

fn calc_probs_impl(board: *const bindings::solver_board_t) -> Vec<f32> {
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
