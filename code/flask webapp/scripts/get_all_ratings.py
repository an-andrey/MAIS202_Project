import pandas as pd
from app.extensions import db

def get_all_ratings():
    try:
        query = "SELECT userId, movieId, rating FROM ratings"
        ratings_df = pd.read_sql_query(query, db.engine)
        return ratings_df
    except Exception as e:
        print(f"Error in get_all_ratings: {e}")
        return pd.DataFrame()