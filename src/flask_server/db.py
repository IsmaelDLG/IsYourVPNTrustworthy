"""A simple module we use to store data temporally.

Currently using sqlite3. Sqlite3 comes with a :memory: param that creates the DB in RAM memory, but this is not used because Flask is multithreaded, and sqlite cursors cannot be shared among threads!
"""

import sqlite3
from pathlib import Path
import os

DB_PATH = str(Path(__file__).parent.absolute().resolve() / Path('db.sqlite3'))

ini_data = [('This is an article', 'Here we find a very long description. Every article should be like this one', str(Path('uploads/example.jpeg').absolute().resolve()), 'example.jpeg'),
             ('Another article', 'A short description is fine too', str(Path('uploads/example.jpeg').absolute().resolve()), 'example.jpeg'),            ]



def initialize():
    """Initializes the DB, creating tables and inserting necessary rows.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS posts
            (title text, desc text, path text, name text)''')
    c.executemany('INSERT INTO posts VALUES (?,?,?,?)', ini_data)
    conn.commit()

    conn.close()



def connect():
    """Connects to the DB.

    :return: (sqlite3.connection, sqlite3.connection.cursor)
    """

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    return conn, c



def get_all(c):
    """Gets all rows from the \"posts\" table.

    :param c: A cursor to a sqlite3 database.

    :return: list(row).
    """

    return list(c.execute('SELECT * FROM posts'))



def new_post(c, data):
    """Insers a \"post\" in the database.

    :param c: A cursor to a sqlite3 database.

    :param data: Values of the row to insert.
    """

    c.execute('INSERT INTO posts VALUES (?,?,?,?)', data)



def close(conn):
    """Closes the given connection connection.

    :param conn: A sqlite3.connection.
    """

    conn.close()



def delete():
    """Deletes the database from the file system. This is a workaround for an in-memory database.
    """
    os.remove(DB_PATH)

