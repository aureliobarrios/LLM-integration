import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

DATABASE_NAME = os.environ["DATABASE_NAME"]

conn = sqlite3.connect(DATABASE_NAME)

cursor = conn.cursor()

