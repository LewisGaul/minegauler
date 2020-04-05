#![allow(dead_code)]

use utils::{Board, BoardProbs};

#[derive(Debug)]
struct Number {
    value: u32,
    groups: Vec<u32>,
}

struct Group {
    max: u32,
    numbers: Vec<Number>,
}

struct Config {
    _a: (),
}

#[derive(Debug)]
struct NumbersVec(Vec<Number>);
struct GroupsVec(Vec<Group>);
struct ConfigsVec(Vec<Config>);

impl Board {
    fn find_numbers(&self) -> NumbersVec {
        NumbersVec(vec![])
    }
}
impl NumbersVec {
    fn find_groups(&self) -> GroupsVec {
        GroupsVec(vec![])
    }
}

impl GroupsVec {
    fn find_configs(&self) -> ConfigsVec {
        ConfigsVec(vec![])
    }
}

impl ConfigsVec {
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
        let board = Board::new(5, 3);
        println!("{}", board);
        let numbers = board.find_numbers();
        println!("{:?}", numbers);
    }
}
