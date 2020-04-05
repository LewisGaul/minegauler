#![allow(dead_code)]

use std::default::Default;
use std::fmt;

#[derive(Clone)]
pub enum CellContents {
    Unclicked,
    Num(u32),
    Mine(u32),
}

impl Default for CellContents {
    fn default() -> Self {
        Self::Unclicked
    }
}

pub struct Grid<T: Default + Clone> {
    x_size: u32,
    y_size: u32,
    cells: Vec<T>,
}

#[derive(Debug)]
pub struct Coord(u32, u32);

impl<T: Default + Clone> Grid<T> {
    pub fn coord_to_index(&self, coord: Coord) -> Option<usize> {
        if coord.0 < self.x_size && coord.1 < self.y_size {
            Some((coord.0 + coord.1 * self.x_size) as usize)
        } else {
            None
        }
    }
    pub fn index_to_coord(&self, index: usize) -> Option<Coord> {
        let index = index as u32;
        if index < self.num_cells() {
            Some(Coord(index % self.x_size, index / self.x_size))
        } else {
            None
        }
    }
}

impl<T: Default + Clone> Grid<T> {
    pub fn new(x_size: u32, y_size: u32) -> Self {
        Self {
            x_size,
            y_size,
            cells: vec![T::default(); (x_size * y_size) as usize],
        }
    }

    pub fn x_size(&self) -> u32 {
        self.x_size
    }

    pub fn y_size(&self) -> u32 {
        self.y_size
    }

    pub fn num_cells(&self) -> u32 {
        self.x_size * self.y_size
    }

    pub fn cell(&self, coord: Coord) -> Option<&T> {
        Some(&self.cells[self.coord_to_index(coord)?])
    }

    pub fn set_cell(&mut self, coord: Coord, contents: T) {
        let index = self.coord_to_index(coord).expect("Coord out of bounds");
        self.cells[index] = contents;
    }
}

pub type Board = Grid<CellContents>;
pub type BoardProbs = Grid<f32>;

impl fmt::Display for Board {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        // The `f` value implements the `Write` trait, which is what the
        // write!() macro is expecting.
        for j in 0..self.y_size {
            for i in 0..self.x_size {
                let cell = &self.cell(Coord(i, j)).unwrap();
                let ch: String; // Character representation
                match cell {
                    CellContents::Unclicked => ch = format!("#"),
                    CellContents::Num(0) => ch = format!("."),
                    CellContents::Num(n) => ch = format!("{}", n),
                    CellContents::Mine(_) => ch = format!("M"),
                }
                write!(f, "{} ", ch)?;
            }
            writeln!(f)?;
        }
        Ok(())
    }
}

// -----------------------------------------------------------------------------
// Tests

#[cfg(test)]
mod test {
    use super::*;

    #[test]
    fn board_coord_to_index() {
        let board = Board::new(5, 3);
        assert_eq!(board.coord_to_index(Coord(0, 0)), Some(0));
        assert_eq!(board.coord_to_index(Coord(3, 1)), Some(8));
        assert_eq!(board.coord_to_index(Coord(5, 1)), None);
        assert_eq!(board.coord_to_index(Coord(0, 3)), None);
        assert_eq!(board.coord_to_index(Coord(20, 20)), None);
    }
    #[test]
    fn board_index_to_coord() {
        let board = Board::new(5, 3);
        for index in &[0, 4, 8, 14 as usize] {
            assert_eq!(
                board
                    .index_to_coord(*index)
                    .and_then(|c| board.coord_to_index(c)),
                Some(*index)
            );
        }
        for index in &[15, 16, 200 as usize] {
            assert!(board.index_to_coord(*index).is_none());
        }
    }
}
