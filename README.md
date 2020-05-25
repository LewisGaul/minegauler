# Minegauler v0!

This is a very old, early implementation of minesweeper, written with **Python 2.7**. This was my first ever substantial project, so it's quite entertaining to look back at!

It's so hard to know what's going on in places that I thought writing out some instructions would be useful...


## v0.1 - 166 LOC

The very first version! This runs entirely on the CLI (with very little guidance of how to use it and a strong tendency to bail out with an exception). Multiple mines per cell is an option from the start!

Steps to get going:
 - `pip install numpy`
 - `python oldversions/minesweeper.py`

This presents you with a beginner board (other boards are available, just not without interacting with the Python...). Indexing starts at (1, 1) in the top-left corner, that is (x, y) format.

Example:
```
$python oldversions/minesweeper.py
10 mines to find.
[[= = = = = = = =]
 [= = = = = = = =]
 [= = = = = = = =]
 [= = = = = = = =]
 [= = = = = = = =]
 [= = = = = = = =]
 [= = = = = = = =]
 [= = = = = = = =]]
1 1
[[1 = = = = = = =]
 [= = = = = = = =]
 [= = = = = = = =]
 [= = = = = = = =]
 [= = = = = = = =]
 [= = = = = = = =]
 [= = = = = = = =]
 [= = = = = = = =]]
1 2
You lose!
[[1 # # = = # = =]
 [= = = = = = = =]
 [# = # = = = = =]
 [= = # = = = = =]
 [= = = = = = = =]
 [= = # = = = = =]
 [# = = # = = = =]
 [= # = = = = = =]]
```


## v0.2 - 351 LOC

Big advancements - we have a functional GUI! We have:
 - a timer that only changes when the game is over
 - characters instead of images
 - coloured numbers!
 - no chording
 - very slow UI on game end/refresh
 - no way to change board size
 - perhaps the 'detection' option has been added?

Notice the name *MineGauler* is in use already!

To run, the same as above works:
 - `pip install numpy`
 - `python oldversions/minesweeper2.pyw`


## v0.3 - 412 LOC

The GUI [now?] supports multiple mines per cell (with the use of more characters!) and the timer works by running in a separate thread. Starting a new game seems to be broken on Linux though, due to using a colour name that only exists on Windows...

I think we can skip this version!


## v0.4 - 1075 LOC

Another big update!
 - Frame around the board
 - Button presses work
 - Chording works
 - Menus containing so many options!
    - New game
    - Replay game
    - Create board! (probably buggy)
    - Highscores!
    - Current game info
    - Custom boards
    - Lives
    - Multiple mines per cell
    - Detection
    - Drag-select!

See `Game.play():motion()` for some fun code that made button presses/mouse moves work!
    

## v0.5 - 1131 LOC

Seems like not much changed in the version, but it's actually a bit of a milestone - I finally achieved what I set out to! The 'current game info' feature now gives a predicted time upon losing.


## v0.6 - 1149 LOC

Another fairly minor update, with the addition of the 'zoom' option. Unfortunately settings from previous versions are not handled in this version, so the `Settings.txt` file may need deleting to get this version to work!


## v0.7 - 1190 LOC

Well, I think this was an attempt to add images... But it doesn't work, because the image files have been moved around! Skip this version...


## v0.8 - 1282 LOC

Now we have images working! With the caveat that you must first run `python create_images.py`, but after that there's faces, mines, and flags.

At this point the game looks good and is highly functional. There are a huge number of features jammed together, which means there are a number of slight annoyances and certainly bugs if you try to stretch it (e.g. buttons still appear clickable after the game is over.

This version also features the experimental 'distance-to' feature!

## v0.9 - abandoned

This appears to have been an early attempt at a major refactor, before the decision was made to make it a major *rewrite* instead, leading to the birth of v1.
