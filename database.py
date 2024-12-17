import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

#load environment variables
DATABASE_HOST = os.environ["DATABASE_HOST"]
DATABASE_NAME = os.environ["DATABASE_NAME"]
DATABASE_USER = os.environ["DATABASE_USER"]
DATABASE_PASSWORD = os.environ["DATABASE_PASSWORD"]
DATABASE_PORT = os.environ["DATABASE_PORT"]

def establish_connection():
    #establish a connection
    conn_details = psycopg2.connect(
        host = DATABASE_HOST,
        database = DATABASE_NAME,
        user = DATABASE_USER,
        password = DATABASE_PASSWORD,
        port = DATABASE_PORT
    )
    #return connection
    return conn_details

#function to build tables for database
def create_tables():
    #create table query
    table_query = """
    CREATE TABLE learning_paths (
        id SERIAL PRIMARY KEY,
        trial TEXT,
        topic TEXT
    );
    CREATE TABLE resource_links (
        id SERIAL PRIMARY KEY,
        resource TEXT,
        title TEXT,
        description TEXT,
        topic TEXT,
        difficulty TEXT,
        validated BOOLEAN,
        avg_rating REAL,
        found_time TIMESTAMP
    );
    """
    #get connection
    conn_details = establish_connection()
    #build server cursor
    cursor = conn_details.cursor()
    #build tables in server
    cursor.execute(table_query)
    #print message
    print("-- Successfully Created Tables --")
    #commit changes
    conn_details.commit()
    #close cursor
    cursor.close()
    #close connection
    conn_details.close()

def insert_learning_path(data):
    #build insert query
    insert_query = f"""
    INSERT INTO learning_paths (trial, topic)
    VALUES (
        '{data['trial']}', 
        '{data['topic']}'
    );
    """
    #get connection
    conn_details = establish_connection()
    #build server cursor
    cursor = conn_details.cursor()
    #build tables in server
    cursor.execute(insert_query)
    #print message
    print("-- Successfully Updated Learning Paths Table --")
    #commit changes
    conn_details.commit()
    #close cursor
    cursor.close()
    #close connection
    conn_details.close()

def insert_resource_link():
    return None

if __name__ == "__main__":
    #add row to table
    data = {
        "trial": "test_1",
        "topic": "python"
    }
    insert_learning_path(data)