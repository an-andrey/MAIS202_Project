from scripts.get_recommendations import get_top_n_recommendations
from scripts.get_movies_omdb import get_movie_info
from scripts.get_popular import get_popular_movies
from scripts.re_train import retrain_svd_model
from scripts.get_all_ratings import get_all_ratings

__all__ = [
    'get_top_n_recommendations',
    'get_movie_info',
    'get_popular_movies',
    'retrain_svd_model',
    'get_all_ratings'
]