#![allow(dead_code, unused_variables)]

use utils::{Board, BoardProbs, CellContents, Coord};

use std::collections::HashSet;

// -----------------------------------------------------------------------------
// Types

/// A number on a board.
#[cfg_attr(test, derive(Debug))]
struct Number<'a> {
    /// Value of the number, as shown.
    value: u32,
    /// Coordinate of the cell the number is shown in.
    coord: Coord,
    /// Neighbouring clickable cells.
    nbrs: HashSet<Coord>,
    /// Groups the number has next to it.
    groups: Vec<&'a Group<'a>>,
}

#[cfg_attr(test, derive(Debug))]
struct Group<'a> {
    max: u32,
    numbers: Vec<&'a Number<'a>>,
}

#[cfg_attr(test, derive(Debug))]
struct Config {
    _a: (),
}

// -----------------------------------------------------------------------------
// Internal logic

/// Find the numbers on a board.
fn find_numbers(board: &Board) -> Vec<Number> {
    let mut nums = Vec::new();
    // Iterate over cells that contain a number.
    let iter_num_cells = board.iter_cells().filter_map(|(c, v)| {
        if let CellContents::Num(n) = v {
            Some((c, *n))
        } else {
            None
        }
    });
    for (coord, orig_value) in iter_num_cells {
        let all_nbrs = board.get_neighbours(coord);
        // Reduce number value based on neighbouring mines.
        let value = orig_value;
        let mines: u32 = all_nbrs
            .iter()
            .filter_map(|c| {
                if let &CellContents::Mine(n) = board.cell(*c) {
                    Some(n)
                } else {
                    None
                }
            })
            .sum();
        if value < mines {
            panic!(
                "Number {} in cell {} has too many neighbouring mines",
                orig_value, coord
            )
        }
        let value = value - mines;
        // Get the neighbouring clickable cells.
        let clickable_nbrs = all_nbrs
            .into_iter()
            .filter(|c| *board.cell(*c) == CellContents::Unclicked)
            .collect::<HashSet<Coord>>();

        nums.push(Number {
            value,
            coord,
            nbrs: clickable_nbrs,
            groups: vec![],
        });
    }
    nums
}

fn find_groups<'a>(numbers: &Vec<Number<'a>>) -> Vec<Group<'a>> {
    vec![]
}

fn find_configs<'a>(numbers: &Vec<Number<'a>>, groups: &Vec<Group<'a>>) -> Vec<Config> {
    vec![]
}

fn find_probs(board: &Board, configs: &Vec<Config>) -> BoardProbs {
    BoardProbs::new(0, 0)
}

// -----------------------------------------------------------------------------
// Public

impl Board {
    pub fn calc_probs(&self) -> BoardProbs {
        let numbers = find_numbers(self);
        let groups = find_groups(&numbers);
        let configs = find_configs(&numbers, &groups);
        find_probs(self, &configs)
    }
}

// -----------------------------------------------------------------------------
// Tests

#[cfg(test)]
mod test {
    use super::*;

    fn make_board() -> Board {
        let mut board = Board::new(5, 3);
        board.set_cell(Coord(1, 1), CellContents::Num(5));
        board.set_cell(Coord(2, 0), CellContents::Mine(1));
        board.set_cell(Coord(0, 1), CellContents::Mine(1));
        board.set_cell(Coord(0, 0), CellContents::Mine(1));
        board.set_cell(Coord(2, 1), CellContents::Num(2));
        board
    }

    #[test]
    fn find_numbers() {
        let board = make_board();
        println!();
        println!("{}", board);
        let numbers = super::find_numbers(&board);
        println!("{:#?}", numbers);
        println!();
    }

    #[test]
    fn find_groups() {
        let board = make_board();
        let numbers = super::find_numbers(&board);
        let groups = super::find_groups(&numbers);
        println!("{:#?}", groups);
        println!();
    }
}
