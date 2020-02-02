# Minegauler Bot


The bot has two modes:
 - Group chat  
   A group room expected to contain ~10 people, in which anyone can communicate with the bot by tagging it, and the bot can also post group notifications.

 - Individual chat  
   An individual conversation between a human user and the bot. This allows communicating with the bot without the interaction being public, and certain commands may only be available in this mode. The bot may also post individual notifications.



## General Interaction

Certain elements of the bot interaction are common between group and individual rooms. One unavoidable difference is that to communicate with the bot in a group room the bot must be tagged in any messages, otherwise it cannot access them.

The bot keeps a list of the names of everyone it comes into touch with, either by receiving a message or by someone entering the group room (assuming it is capable of being notified of this event - if not a message will be required). When someone new is recognised the bot will send a welcome message to that individual.

By default the bot assumes the username is the name they will be using when setting Minegauler highscores. However, it will be possible for users to set their nickname (see below), which will then be used instead of the username (only one nickname can be set, and nicknames cannot be used by multiple users).

In general there are the following actions performed by the bot: responding to query messages, sending notification messages, and accepting action messages. 

Below is a summary of query commands that are available in both the group and individual rooms, with responses going to the room the query was issued in. Note that in place of a 'name' it is also possible to use "me" (nicknames cannot be used). Duplicated names are ignored.


### Summary of commands

 - `help [<command>]` or `[<command>] ?`  
   Display a help message about the commands/options available.

 - `info`
   Display more detailed information about the game (e.g. how to get it).

 - `ranks [b[eginner] | i[ntermediate] | e[xpert] | m[aster] | combined | official] [drag-select {on | off}] [per-cell {1 | 2 | 3}]`  
   Display the ranks of tracked people for the given settings (default is the sum of the best time on beginner, intermediate and expert irrespective of drag select mode or number mines per cell). E.g. `ranks b drag-select on per-cell 2`.
   
 - `player <name> [b[eginner] | i[ntermediate] | e[xpert] | m[aster]] [drag-select {on | off}] [per-cell {1 | 2 | 3}]`  
   Display information about the given player, including nickname a summary of best times, and number of games played. E.g. `player richcoop b per-cell 1`.

 - `stats [b[eginner] | i[ntermediate] | e[xpert] | m[aster]] [drag-select {on | off}] [per-cell {1 | 2 | 3}]`  
   Display stats for the given settings. E.g. `stats expert`.

 - `stats players {all | <name> [<name> ...]} [b[eginner] | i[ntermediate] | e[xpert] | m[aster]] [drag-select {on | off}] [per-cell {1 | 2 | 3}]`  
   Display player stats for the given players and settings. E.g. `stats players all`.

 - `matchups <name> [<name> ...] [b[eginner] | i[ntermediate] | e[xpert] | m[aster]] [drag-select {on | off}] [per-cell {1 | 2 | 3}]`  
   Display all matchups involving the listed players. E.g. `matchups legaul tjohnes richcoop marholme`.

 - `best-matchups [<name> ...] [b[eginner] | i[ntermediate] | e[xpert] | m[aster]] [drag-select {on | off}] [per-cell {1 | 2 | 3}]`  
   Display the best matchups involving at least one of the listed players (if any) and anyone else in the group. E.g. `best-matchups me master per-cell 1`.



## Group Room

In the group room all members can see all messages. For this reason the bot should not send too many notifications here (i.e. they should scale well with the number of users), and it should be considered to make certain common query commands only work in individual chat to dissuade people from spamming the group chat.

Any action commands that result in other players being sent a message by the bot (either individually or tagged in a group message) are only available in the group room (so that users can see why they are getting the bot message).

There will also be various 'achievement' notifications sent to the group room, to notify users of other players' achievements and encourage them to play/compete.


### Summary of commands

 - `challenge <name> [<name> ...] [b[eginner] | i[ntermediate] | e[xpert] | m[aster]] [drag-select {on | off}] [per-cell {1 | 2 | 3}]`  
   Challenge player(s) to a game. This triggers the bot to send a response tagging all challenged players, displaying the matchups between the challenger and challengees.


### Summary of notifications

 - Whenever someone sets a new highscore on a given difficulty level, e.g. their best goes from 10.82s to 10.54s on beginner (regardless of the drag-select and per-cell settings).

 - Whenever someone goes up in the rankings for any given difficulty, per-cell and drag-select, e.g. their ranking on beginner with drag-select on and per-cell 1 goes from 5th to 4th.



## Individual Room

The individual converstion with the bot provides a private place to perform bot queries, as well as a private place for certain other bot interactions.

Note that individual notifications are only sent to users who are in the group room at the time when the notification would be sent.


### Summary of commands

 - `set nickname <name>`  
   Allows a user to set their nickname. Any highscores using the old nickname will no longer be associated with them.


### Summary of notifications

 - Welcome message when someone new gets in contact with the bot.
 
 - Whenever someone's ranking changes (up or down) for any given difficulty, per-cell and drag-select, e.g. someone overtook them on beginner with drag-select on and per-cell 1.
