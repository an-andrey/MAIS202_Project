import pymysql
import os
from dotenv import load_dotenv
import pandas as pd

#SCRIPT THAT CONVERTS CSV'S TO MYSQL TABLES

load_dotenv()

# Database connection details
timeout = 10
host = os.getenv("DATABASE_URL")
port = 16037
user = os.getenv("DATABASE_USER")
password = os.getenv("DATABASE_PWD")
database = "defaultdb"

ratings = pd.read_csv("MovieLensFinal/ratings.csv")
movies = pd.read_csv("MovieLensFinal/movies.csv")

# Connect to the database
try:
    connection = pymysql.connect(
        charset="utf8mb4",
        connect_timeout=timeout,
        cursorclass=pymysql.cursors.DictCursor,
        db=database,
        host=host,
        password=password,
        read_timeout=timeout,
        port=port,
        user=user,
        write_timeout=timeout,
    )


    
    with connection.cursor() as cursor:
        #creating the tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                userId INT,
                movieId INT,
                rating DECIMAL(2,1)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                movieId INT PRIMARY KEY,
                title VARCHAR(255),
                genres VARCHAR(255),
                release_year INT
            )
        """)

        #inserting csv rows into the tables
        for index, row in ratings.iterrows():
            cursor.execute("INSERT INTO ratings (userId, movieId, rating) VALUES (%s, %s, %s)",
                        (row['userId'], row['movieId'], row['rating']))
            
        for index, row in movies.iterrows():
            cursor.execute("INSERT INTO movies (movieId, title, genres, release_year) VALUES (%s, %s, %s, %s)",
                        (row['movieId'], row['title'], row['genres'], row['release_year']))
            
    # Commit changes 
    connection.commit()

except pymysql.Error as e:
    print(f"Error connecting to database: {e}")

finally:
    # Close the connection
    connection.close()