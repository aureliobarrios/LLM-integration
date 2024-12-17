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

#create knowledge base database class
class KnowledgeBase:
    #build constructor
    def __init__(self):
        #establish connection details
        self.db_host = DATABASE_HOST
        self.db_name = DATABASE_NAME
        self.db_user = DATABASE_USER
        self.db_password = DATABASE_PASSWORD
        self.db_port = DATABASE_PORT
    
    #function to establish connection
    def start_session(self):
        #establish a connection
        self.conn_details = psycopg2.connect(
            host = self.db_host,
            database = self.db_name,
            user = self.db_user,
            password = self.db_password,
            port = self.db_port
        )
        print("-- DataBase Session Started --")
        #build cursor
        self.cursor = self.conn_details.cursor()

    #function to commit changes made in session
    def commit_session(self):
        #commit changes
        self.conn_details.commit()
        print("-- DataBase Changes Committed --")
    
    #function to end connection
    def end_session(self):
        #close cursor
        self.cursor.close()
        #close connection
        self.conn_details.close()
        print("-- DataBase Session Closed --")
    
    #function to query database
    def query(self, query):
        try:
            #execute the query
            self.cursor.execute(query)

            print("-- Query Success --")
        except Exception as e:
            print("Connection Error:", e)
    
    #function to build build tables query
    def build_tables(self):
        #create tables query
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
        try:
            #execute query
            self.cursor.execute(table_query)

            print("-- Successfully Created Tables --")
        except Exception as e:
            print("Connection Error:", e)

    #function to build insert learning path query
    def insert_learning_path(self, data):
        #build insert query
        insert_query = f"""
        INSERT INTO learning_paths (trial, topic)
        VALUES (
            '{data['trial']}', 
            '{data['topic']}'
        );
        """
        try:
            #execute query
            self.cursor.execute(insert_query)

            print("-- Successfully Inserted Learning Path --")
        except Exception as e:
            print("Connection Error:", e)
    

    def get_learning_path_by_topic(self, topic):
        #build get query
        get_query = f"""
        SELECT * FROM learning_paths
        WHERE topic = '{topic}';
        """
        try:
            #execute query
            self.cursor.execute(get_query)
            #get the rows
            rows = self.cursor.fetchall()
            print("-- Successfully Retrieved Rows By Topic --")
        except Exception as e:
            print("Connection Error:", e)
        return rows

    
if __name__ == "__main__":
    #build database
    db = KnowledgeBase()
    #start the session
    db.start_session()

    #loop through different topics
    # for topic in ["python", "javascript", "sql"]:
    #     #build current data
    #     curr_data = {
    #         "trial": "other",
    #         "topic": topic
    #     }
    #     #build query
    #     db.insert_learning_path(curr_data)

    #get rows
    rows = db.get_learning_path_by_topic("python")

    for row in rows:
        print(row)
   
        
    #commit changes made in session
    db.commit_session()
    #end session
    db.end_session()