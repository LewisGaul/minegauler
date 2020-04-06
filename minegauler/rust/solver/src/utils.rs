#![allow(dead_code)]

use std::cmp::min;
use std::collections::HashSet;
use std::default::Default;
use std::fmt;
use std::vec;

#[derive(Clone, Copy, Eq, PartialEq)]
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

pub struct Grid<T: Clone + Default> {
    x_size: u32,
    y_size: u32,
    cells: Vec<T>,
}

#[derive(Clone, Copy, Eq, Hash, PartialEq)]
pub struct Coord(pub u32, pub u32);

impl fmt::Display for Coord {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "({}, {})", self.0, self.1)
    }
}

#[cfg(test)]
impl fmt::Debug for Coord {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "Coord({}, {})", self.0, self.1)
    }
}

/// Grid implementation
///
/// Methods that accept an index or coordinate will panic if the given arg is
/// out of bounds.
impl<T: Clone + Default> Grid<T> {
    pub fn new(x_size: u32, y_size: u32) -> Self {
        if x_size < 1 || y_size < 1 {
            panic!("Both dimensions must be nonzero");
        }
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

    pub fn cell(&self, coord: Coord) -> &T {
        self.check_coord(&coord);
        &self.cells[self.coord_to_index(&coord)]
    }

    pub fn iter_coords(&self) -> Vec<Coord> {
        let mut vec = Vec::new();
        for y in 0..self.y_size {
            for x in 0..self.x_size {
                vec.push(Coord(x, y));
            }
        }
        vec
    }

    pub fn iter_cells(&self) -> vec::IntoIter<(Coord, &T)> {
        let mut vec = Vec::new();
        for y in 0..self.y_size {
            for x in 0..self.x_size {
                let coord = Coord(x, y);
                vec.push((coord, self.cell(coord)));
            }
        }
        vec.into_iter()
    }

    pub fn has_coord(&self, coord: &Coord) -> bool {
        coord.0 < self.x_size && coord.1 < self.y_size
    }

    fn check_coord(&self, coord: &Coord) {
        if !self.has_coord(coord) {
            panic!("Coord out of bounds");
        }
    }

    pub fn set_cell(&mut self, coord: Coord, contents: T) {
        let index = self.coord_to_index(&coord);
        self.cells[index] = contents;
    }

    pub fn coord_to_index(&self, coord: &Coord) -> usize {
        self.check_coord(coord);
        (coord.0 + coord.1 * self.x_size) as usize
    }

    pub fn coord_from_index(&self, index: usize) -> Coord {
        let index = index as u32;
        let coord = Coord(index % self.x_size, index / self.x_size);
        self.check_coord(&coord);
        coord
    }

    /// Get a list of the coordinates of neighbouring cells.
    pub fn get_neighbours(&self, coord: Coord) -> HashSet<Coord> {
        self.check_coord(&coord);
        let Coord(x, y) = coord;
        let x_min = if x >= 1 { x - 1 } else { 0 };
        let x_max = min(self.x_size - 1, x + 1);
        let y_min = if y >= 1 { y - 1 } else { 0 };
        let y_max = min(self.y_size - 1, y + 1);

        let mut nbrs = HashSet::new();
        for j in y_min..=y_max {
            for i in x_min..=x_max {
                if (x, y) != (i, j) {
                    nbrs.insert(Coord(i, j));
                }
            }
        }
        nbrs
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
                let cell = &self.cell(Coord(i, j));
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
    extern crate cool_asserts;

    use self::cool_asserts::assert_panics;
    use super::*;

    mod grid {
        use super::*;
        use std::iter::FromIterator;

        #[test]
        fn coord_to_index() {
            let grid = Grid::<u32>::new(5, 3);
            assert_eq!(grid.coord_to_index(&Coord(0, 0)), 0);
            assert_eq!(grid.coord_to_index(&Coord(3, 1)), 8);
        }

        #[test]
        fn coord_to_index_panic() {
            let grid = Grid::<u32>::new(5, 3);
            for c in &[(5, 0), (0, 3), (5, 3), (6, 20), (100, 100)] {
                assert_panics!(grid.coord_to_index(&Coord(c.0, c.1)));
            }
        }

        #[test]
        fn coord_from_index() {
            let grid = Grid::<u32>::new(5, 3);
            for index in &[0, 4, 8, 14 as usize] {
                assert_eq!(grid.coord_to_index(&grid.coord_from_index(*index)), *index);
            }
        }

        #[test]
        fn coord_from_index_panic() {
            let grid = Grid::<u32>::new(5, 3);
            for index in &[15, 16, 20, 100 as usize] {
                assert_panics!(grid.coord_from_index(*index));
            }
        }

        #[test]
        fn get_neighbours() {
            let grid = Grid::<u32>::new(5, 3);
            assert_eq!(
                grid.get_neighbours(Coord(0, 0)),
                HashSet::from_iter(vec![Coord(1, 0), Coord(0, 1), Coord(1, 1)])
            );
            assert_eq!(
                grid.get_neighbours(Coord(2, 1)),
                HashSet::from_iter(vec![
                    Coord(1, 0),
                    Coord(1, 1),
                    Coord(1, 2),
                    Coord(2, 0),
                    Coord(2, 2),
                    Coord(3, 0),
                    Coord(3, 1),
                    Coord(3, 2),
                ])
            );
            assert_eq!(
                grid.get_neighbours(Coord(4, 1)),
                HashSet::from_iter(vec![
                    Coord(3, 0),
                    Coord(3, 1),
                    Coord(3, 2),
                    Coord(4, 0),
                    Coord(4, 2),
                ])
            );
        }
    }
}
