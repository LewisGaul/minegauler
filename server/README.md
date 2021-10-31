
## Minegauler Server

The server can be run with:  
`BOT_ACCESS_TOKEN=<token> SQL_DB_PASSWORD=<password> python3 -m server [--bot] [--port 8080]`

If '`--bot`' is given then the bot is served from the same process, see the `bot/` directory.

Aside from the bot, the server provides the `/api/v1/highscores` REST API:
 - POST: store new highscores
 - GET: return stored highscores
