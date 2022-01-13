# Split Cell Mode

See <https://github.com/LewisGaul/minegauler/issues/41>.

The idea is instead of beginner being 8 x 8 small cells it would start off being be 4 x 4 cells that are twice the size, but can be split into the underlying small cells.

The aim is still to reveal all safe cells - if a big cell is safe you can just click it to reveal a number, but if a big cell is unsafe you must right click it to split into the 4 small cells, and you then have to work out which of those is safe. This means that all big cells must be clicked to win - left click if safe (no mines in any of the 4 underlying small cells) to display a large number, or right click if not safe (at least one of the underlying small cells contains a mine) to split into the smaller cells.

It is a loss to right-click a big cell that does not contain any mines (to prevent simply reverting to a normal board by splitting all big cells at the start).


## Implementation

The basics of the minefield class do not need to change - the mines are placed in the underlying small-cell grid in the same way as for normal games. However, the concept of things like 3bv and openings will be a bit different.

One of the fundamental things that will be needed is a way to check whether a game has been won. This can actually be determined in the same way as before, since it's just a matter of checking that all unclicked small cells contain mines.

One of the biggest changes is that the numbers displayed on the board change dynamically depending on whether neighbouring cells are split. This means we can't simply use the pre-determined 'completed board' for selecting the number to display - they need to be recalculated every time a cell is split.
