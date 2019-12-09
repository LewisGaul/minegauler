# Changelog

All notable changes to this project will be documented in this file.


## Planned

### Additions
 - Ability to save and load created boards
 - Option of having multiple lives
 - Entries in the 'Help' menu
 - Button styles

### Fixes
 - Ensure GUI window is the correct size for beginner mode


## 4.0.1-a0 (2019-12-09)
 - Ability to specify custom board sizes


## 4.0.0-a1 (2019-12-07)
 - Minor code/project improvements


## 4.0.0-a0 (2019-12-03)

First point of tracking for rewrite coming under version 4.0.

There have been multiple rewrites of the project, and none have yet caught up with functionality of the original implementation. The head of the original implementation (`v1.2.2`) is included as a Python-independent executable application (see `releases/`). The first rewrite (`v2`) has been the most significant, migrating to Python 3 and from `Tkinter` to `PyQt5`. The main benefit this brought was improved performance, while also providing a framework more suitable for creating a modern-looking GUI (e.g. for highscores).

The `v3` and `v4` rewrites have continued to improve the codebase and some tests have been added. The stability is much improved since the original implementation, but the set of features is still catching up :)

This initial tracked version includes:
 - Basic functional game
 - Ability to replay a game
 - 'Create' mode
 - Option of whether first click will guarantee an opening
 - Option to select cells by click-and-drag technique with the mouse
 - Option to have multiple mines per cell
