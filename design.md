# Design


### Fundamental minesweeper classes

 - `Minefield`  
   Primarily contains the placement of mines in a grid of given dimensions.
   Also stores fundamental features of the minefield, including the 3bv, a list
   of openings and the completed board.
 - `Board`  
   A representation of the state of a minesweeper board at any point during
   play, with cell contents corresponding to how they are displayed
   (e.g. flagged, unclicked, ...).
   Does not contain any information about the game being played, only the state
   of the board as it is displayed.
 - `Game`  
   A minesweeper game. Stores a minefield and the state of the board, as well
   as game settings that are in use (e.g. max mines per cell).
   Provides methods to select or flag cells as well as to chord, but nothing
   that could be considered UI implementation.


### API to frontends

#### Discussion

There are a few options to consider here, with the decision depending on the
type of frontends we wish to support. To optimise performance there is a need
for the backend to be able to notify frontends when there are changes,
otherwise frontends will need to check the entire board state every time any
cell is selected (even if the click has no effect).

 - A frontend written in Python can directly use the backend library via
   imports. This is the simplest option, however any changes to the backend API
   then lead to changes being needed across the frontend's use of the API. For
   simplicity, the backend could offer an indicator of changes caused by the
   last interaction, allowing the frontend to check which updates are needed
   without having to check the whole board. 
 - A specialised backend API, acting as a wrapper around the implementation.
   This makes it the responsibility of the backend to define how and what to
   make public. With this option there is a decision to be made about whether
   the backend should be responsible for sending notifications, or whether a
   similar approach to the above option is taken in this regard. This is a
   slightly less straightforward alternative to the above, however it does
   provide the added layer of separation. 
 - Some form of JSON API. This allows a wider range of frontends to use the
   backend, e.g. a web UI. It would also allow a Python frontend to run in a
   separate process to the backend, although it is unclear the effect this
   would have on performance. In this case it would be entirely down to the
   backend to decide what information should be passed on.
 
One of key differences between the above options is whether the backend or
the frontend has control over the API. On one extreme the backend does
not have an active role - the frontend simply accesses information stored in
the backend objects. In the other extreme the backend has complete control
over what information is available to frontends, and has the responsiblity of
sending out notifications. There are also options that fall somewhere in
between those extremes.
 
 
#### Resulting decision

Logically, it seems sensible for the backend to define the API - seeing as the
backend has the general responsibility of handling all the game logic, it
makes sense for it to declare the information of interest to clients.
Furthermore, there is merit to introducing a layer of separation between the
internal logic and the user-facing elements of the game. The API will remain a
simple Python module, with the acknowledgement that this API could easily be
wrapped again to provide a different kind of interface (e.g. JSON API).
