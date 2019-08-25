# Design


### Fundamental minesweeper classes

 - `Minefield`  
 Primarily contains the placement of mines in a grid of given dimensions.
 Also stores fundamental features of the minefield, including the 3bv, a list
 of openings and the completed board.
 - `Board`  
 A representation of the state of a minesweeper board at any point during play,
 with cell contents corresponding to how they are displayed (e.g. flagged,
 unclicked, ...).
 Does not contain any information about the game being played, only the state
 of the board as it is displayed.
 - `Game`  
 A minesweeper game. Stores a minefield and the state of the board, as well as
 game settings that are in use (e.g. max mines per cell).
 Provides methods to select or flag cells as well as to chord, but nothing that
 could be considered UI implementation.
