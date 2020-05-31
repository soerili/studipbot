import os
import sqlite3
from exceptions import DatabaseError


class DatabaseConnection:
    def __init__(self, data_directory, db_file):
        self.db_file = db_file
        self.data_directory = data_directory
        os.makedirs(self.data_directory, exist_ok=True)
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS courses (course_id text, number text, title text, lecturers text, UNIQUE(course_id))')
            conn.commit()
            cursor.execute(
                'CREATE TABLE IF NOT EXISTS users (discord_id text, studip_id text, UNIQUE(discord_id))')
            conn.commit()
        except sqlite3.Error as error:
            print(error)
        finally:
            if conn:
                conn.close()

    def get_db_connection(self):
        return sqlite3.connect(self.data_directory + self.db_file)

    def db_query(self, query, parameters=None, fetchall=False):
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            if parameters is not None:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)
            if fetchall:
                query_result = cursor.fetchall()
            else:
                query_result = cursor.fetchone()
            return query_result
        except sqlite3.Error as error:
            raise DatabaseError
        finally:
            if conn:
                conn.close()
