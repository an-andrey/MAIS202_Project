import pandas as pd
from sklearn.model_selection import train_test_split

ratings = pd.read_csv("MovieLens32M/ratings.csv")
movies = pd.read_csv("MovieLens32M/movies.csv")

########################
# SHRINKING RATING CSV #
########################
# train_ratings, test_ratings = train_test_split(ratings, test_size=0.95, random_state=42)
# train_ratings = train_ratings[["userId","movieId","rating"]]
# train_ratings.to_csv("ratings.csv",index=False)

#######################
# POLISHING MOVIE CSV #
#######################
movies["release_year"] = movies["title"].str.extract(r'\((\d{4})\)')
movies["title"] = movies["title"].str.replace(r'\s*\(\d{4}\)', '', regex=True)
movies = movies.dropna()

movies.to_csv("movies.csv",index=False)


