#![allow(dead_code)]

use utils::{Board, BoardProbs, CellContents, Coord};

// -----------------------------------------------------------------------------
// Types

#[derive(Debug)]
struct Number<'a> {
    value: u32,
    coord: Coord,
    groups: Vec<&'a Group<'a>>,
}

#[derive(Debug)]
struct Group<'a> {
    max: u32,
    numbers: Vec<&'a Number<'a>>,
}

#[derive(Debug)]
struct Config {
    _a: (),
}

// Define newtypes so that we can implement methods on them.

#[derive(Debug)]
struct Numbers<'a>(Vec<Number<'a>>);

#[derive(Debug)]
struct Groups<'a>(Vec<Group<'a>>);

#[derive(Debug)]
struct Configs(Vec<Config>);

// -----------------------------------------------------------------------------
// Internal logic

impl Board {
    fn find_numbers(&self) -> Numbers {
        let mut nrs = Vec::new();
        for (coord, contents) in self.iter_cells() {
            if let CellContents::Num(n) = contents {
                nrs.push(Number {
                    value: *n,
                    coord,
                    groups: vec![],
                });
            }
        }
        Numbers(nrs)
    }
}
impl<'a> Numbers<'a> {
    fn find_groups(&self) -> Groups<'a> {
        Groups(vec![])
    }
}

impl<'a> Groups<'a> {
    fn find_configs(&self) -> Configs {
        Configs(vec![])
    }
}

impl Configs {
    fn find_probs(&self) -> BoardProbs {
        BoardProbs::new(0, 0)
    }
}

// -----------------------------------------------------------------------------
// Public

impl Board {
    pub fn calc_probs(&self) -> BoardProbs {
        self.find_numbers()
            .find_groups()
            .find_configs()
            .find_probs()
    }
}

// -----------------------------------------------------------------------------
// Tests

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn find_numbers() {
        let mut board = Board::new(5, 3);
        board.set_cell(Coord(1, 1), CellContents::Num(1));
        board.set_cell(Coord(2, 1), CellContents::Num(2));
        board.set_cell(Coord(3, 1), CellContents::Num(3));
        board.set_cell(Coord(4, 2), CellContents::Num(1));
        println!("{}", board);
        let numbers = board.find_numbers();
        println!();
        println!("{:?}", numbers);
        println!();
    }
}
