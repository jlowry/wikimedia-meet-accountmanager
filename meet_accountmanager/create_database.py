import sqlite3
from contextlib import closing

sql = """
BEGIN;
DROP TABLE IF EXISTS tokens;
CREATE TABLE tokens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  token TEXT NOT NULL,
  expiry TIMESTAMP NOT NULL
);
COMMIT;
"""

def init_db():
    with closing(sqlite3.connect( "state.sqlite3", detect_types=sqlite3.PARSE_DECLTYPES)) as db:
        with closing(db.cursor()) as cursor:
            cursor.executescript(sql)

if __name__ == "__main__":
    init_db()
