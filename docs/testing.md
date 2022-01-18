# Testing

Some notes on cases that should be covered in tests... For now may want to run through these manually after any significant backend changes!

- Lose by hitting mines in multiple cells (with wrong flags and chording)
- Load board with different mines/per-cell to current settings
  - From different game states
- Set highscore from loaded board/replayed game
- Changing settings mid game (should use frontend pending state)
- Completed current game highscore being highlighted in the UI
- Changing name in name bar
- Persisting settings
- Setting menubar radiobuttons correctly on startup (e.g. difficulty, per-cell, ...)
- Current game info data should match highscore data
