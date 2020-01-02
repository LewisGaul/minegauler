# Changelog

All notable changes to this project will be documented in this file.


## Planned

### Additions
 - Ability to pause a game
 - Ability to change size of minefield cells
 - Option of having multiple lives

### Fixes
 - Remove ability to maximise the main window


## 4.0

This first tracked version includes:
 - Basic functional game
 - Ability to specify custom board size/number of mines
 - Ability to replay a game
 - Mode to create boards
 - Ability to save and load created boards
 - Option of whether first click will guarantee an opening
 - Option to select cells by click-and-drag technique with the mouse
 - Option to allow multiple mines per cell
 - Local highscores for standard difficulty modes
 - Custom cell styles


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
