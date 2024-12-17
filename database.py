import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DATABASE_NAME = os.environ["DATABASE_NAME"]

conn = sqlite3.connect(DATABASE_NAME)

cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS test (
    id INTEGER PRIMARY KEY,
    name TEXT
)
''')

# cursor.execute("INSERT INTO test (name) VALUES ('Python')")
# cursor.execute("INSERT INTO test (name) VALUES ('Javascript')")

conn.commit()

# cursor.execute("SELECT * FROM test WHERE name == 'Python'")
cursor.execute("SELECT * FROM test")
for row in cursor.fetchall():
    print(row)