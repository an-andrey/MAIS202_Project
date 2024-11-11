import pandas as pd
import joblib
import surprise 
import numpy
import os
import time

#script that gets the top n recommendations for a user
def get_unwatched_movies(engine,userId):
    start = time.time()
    with engine.connect() as connection:
        movies_df = pd.read_sql("SELECT * FROM movies", connection)
        user_ratings_df = pd.read_sql(f"SELECT * FROM ratings WHERE userId = {userId}", connection)

    # Perform the left join to find unrated movies
    unrated_movies_df = movies_df.merge(user_ratings_df, on='movieId', how='left', indicator=True)
    
    # Filter out the movies that have been rated by the user (where merge is not 'left_only')
    unrated_movies_df = unrated_movies_df[unrated_movies_df['_merge'] == 'left_only']
    
    # Select only the 'movieId' column
    unrated_movies_df = unrated_movies_df[['movieId']]

    print(time.time()-start)
    return unrated_movies_df

def get_top_n_recommendations(engine,model,userId,n):
    start = time.time()
    unwatched_movies = get_unwatched_movies(engine,userId)
    top_n_movies = [[0,0] for _ in range(n)]

    #making a prediction for all the unwatched movies for the user, and trying to find the top n
    #recommendations
    for movieId in unwatched_movies["movieId"]: 
        #making a prediction
        # print(userId,movieId)
        prediction = model.predict(userId,movieId)

        for i in range(n-1,0,-1):
            # if the prediction is better than the next best prediction, swap them until you get
            #to the end of the list
            if prediction.est > top_n_movies[i-1][1]:
                top_n_movies[i][0] = top_n_movies[i-1][0]
                top_n_movies[i][1] = top_n_movies[i-1][1]

                top_n_movies[i-1][0] = movieId
                top_n_movies[i-1][1] = prediction.est

    print(time.time()-start)    
    return top_n_movies 