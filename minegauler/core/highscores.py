import sqlite3
from sqlite3 import Error
import attr
from .. import ROOT_DIR
from ..utils import get_difficulty


@attr.attrs(auto_attribs=True)
class HighscoreStruct:

    elapsed: float
    timestamp: int
    difficulty: str
    per_cell: int
    bbbvps: float

def init_db():
    db_file = ROOT_DIR / "data" / "highscores.db"    
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS highscores (
            id integer PRIMARY KEY,
            elapsed real NOT NULL, 
            timestamp integer,
            difficulty text,
            per_cell integer,
            bbbvps real
    );"""
    #add drag select check
    cursor.execute(create_table_sql)
    
    return conn


def get_data(difficulty, per_cell):
    conn = init_db()
    cursor = conn.cursor()
    query = "SELECT elapsed, timestamp, difficulty, per_cell, bbbvps FROM highscores WHERE difficulty = '" + difficulty + "' AND per_cell = " + str(per_cell) + " ORDER BY elapsed DESC;"
    result_list = cursor.execute(query).fetchall()
    return [HighscoreStruct(*result) for result in result_list]
    


def check_highscore(game):
    conn = init_db()
    cursor = conn.cursor()
    game_difficulty = get_difficulty(game.mf.x_size, game.mf.y_size, game.mf.nr_mines)
    record_time = game.get_elapsed()
    timestamp = game.start_time
    per_cell = game.mf.per_cell
    bbbvps = game.get_3bvps()
    insert_sql = "INSERT INTO highscores (elapsed, timestamp, difficulty, per_cell, bbbvps) VALUES (?, ?, ?, ?, ?);"
    to_beat_sql = "SELECT id, elapsed FROM highscores WHERE difficulty = '" + game_difficulty + "' ORDER BY elapsed DESC;"
    to_beat_size = cursor.execute(to_beat_sql).fetchall()
    check_size = len(to_beat_size)
    if check_size < 3:
        cursor.execute(insert_sql, (record_time, timestamp, game_difficulty, per_cell, bbbvps))
    else:
        to_beat = cursor.execute("SELECT id, elapsed FROM highscores WHERE difficulty = '" + game_difficulty + "' ORDER BY elapsed DESC;")
        to_beat_query = to_beat.fetchone()
        if to_beat_query[1] > record_time:
            print("New highscore!")
            update_sql = "UPDATE highscores SET elapsed = ? , date = ? , bbbvps = ? WHERE id = ?;"
            cursor.execute(update_sql, (record_time, timestamp, bbbvps, to_beat_query[0]))
    
    conn.commit()
    print(cursor.execute("SELECT * FROM highscores;").fetchall())


            
            
            










    