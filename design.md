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


### High-level APIs

There are two parts to the API. Firsly there is the matter of receiving user
input and changing the state of the game in response, which can be considered
a notification from the frontend to the backend. Secondly there is the need to
update the display to reflect the changes in the game state - a notification
from the backend to the frontend. In terms of the MVC (model view controller)
design pattern, the model would store the game state, the controller would
update the game state (in response to a user action), and the view would be
updated when the game state changes.

As an alternative, one option would be for the frontend to fetch the game
state after every user input. The issue with this is that it shouldn't be the
responsibility of the frontend to know when a user input might change the
display, and it doesn't make sense to be checking on every call as opposed to
being notified when a change has occurred.

Python APIs will be used for simplicity, however it should be noted that this
could in the future be wrapped to provide a different kind of interface
(e.g. JSON API) to allow communicating with an alternative frontend
implementation, e.g. a web UI.


#### Notification from frontend to backend

The backend will define a controller class, an instance of which should be
used by a frontend to control the game state (everything including selecting a
cell, starting a new game, changing game settings, ...). Any user input should
be translated into a call on the controller, which will then notify all
registered frontends with any game state changes.


#### Notification from backend to frontend

The backend will provide an API to register/unregister listeners, where a
'listener' is defined via an abstract class (acting as an interface) and
should define methods to receive all game updates.
