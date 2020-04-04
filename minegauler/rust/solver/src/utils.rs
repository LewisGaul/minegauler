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

    pub fn cells(&self) -> &Vec<T> {
        &self.cells
    }

    pub fn cells_mut(&mut self) -> &mut Vec<T> {
        &mut self.cells
    }
}

pub type Board = Grid<CellContents>;
pub type BoardProbs = Grid<f32>;

impl fmt::Display for Board {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        // The `f` value implements the `Write` trait, which is what the
        // write!() macro is expecting.
        for i in 0..self.y_size {
            for j in 0..self.x_size {
                let index = (i + j * self.y_size) as usize;
                let cell = &self.cells[index];
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
