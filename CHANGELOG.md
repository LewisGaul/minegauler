# Changelog

All notable changes to this project will be documented in this file.


## Planned

### Additions
 - Ability to pause a game
 - Option of having multiple lives
 - Probabilities
 - New 'split cell' mode


## 4.0

This first tracked version includes:
 - Basic functional game
 - Ability to specify custom board size/number of mines
 - Ability to replay a game
 - Mode to create boards
 - Ability to save and load created boards
 - Get current game information, including predicted completion time for lost game
 - Option of whether first click will guarantee an opening
 - Option to select cells by click-and-drag technique with the mouse
 - Option to allow multiple mines per cell
 - Local highscores for standard difficulty modes
 - Highscores uploaded to remote server when there is an internet connection
 - Custom cell styles
 - Option to change the cell size
 - Ability to reduce the window size and use scroll


### 4.0.4-a0 (2020-01-14)
 - Upload highscores to remote server
   - Only when there is an internet connection, not queued for later
   - View highscores e.g. at URL http://3.11.92.147:8080/api/highscores?per_cell=3&name=Siwel%20G&drag_select=1


### 4.0.3-a4 (2020-01-04)
 - Fix scrollbars always appearing


### 4.0.3-a3 (2020-01-02)
 - Option to get current game information, including predicted completion time for lost game


### 4.0.3-a2 (2020-01-02)
 - Allow reducing the size of the window which introduces scrollbars to the board


### 4.0.3-a1 (2020-01-02)
 - Add option to change the cell size


### 4.0.3-a0 (2020-01-02)
 - Add ability to save and load created boards


### 4.0.2-a1 (2020-01-01)
 - Add entries in the 'Help' menu


### 4.0.2-a0 (2019-12-31)
 - Local highscores
 - Custom cell styles
 - Fix main window sizing
 - Fix crash when exceeding number 18 in create mode


### 4.0.1-a0 (2019-12-09)
 - Ability to specify custom board sizes


### 4.0.0-a1 (2019-12-07)
 - Minor code/project improvements


### 4.0.0-a0 (2019-12-03)

First point of tracking for rewrite coming under version 4.0.


## History

There have been multiple rewrites of the project, and none have yet caught up with functionality of the original implementation. The head of the original implementation (`v1.2.2`) is included as a Python-independent executable application (see `releases/`). The first rewrite (`v2`) has been the most significant, migrating to Python 3 and from `Tkinter` to `PyQt5`. The main benefit this brought was improved performance, while also providing a framework more suitable for creating a modern-looking GUI (e.g. for highscores).

The `v3` and `v4` rewrites have continued to improve the codebase and some tests have been added. The stability is much improved since the original implementation, but the set of features is still catching up :)
