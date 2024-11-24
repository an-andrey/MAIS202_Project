from app.extensions import db
from app.models.movie import Movies
from app.models.rating import Ratings
from scripts import get_top_n_recommendations, get_movie_info, get_popular_movies
from eventlet.greenpool import GreenPool
from sqlalchemy import or_, and_
import time
import pickle

class MovieService:
    def __init__(self):
        self.session = db.session
        self.model = self._load_model()

    def _load_model(self):
        model_path = "ml_model/svd_model.pkl"
        try:
            with open(model_path, "rb") as f:
                return pickle.load(f)
        except (FileNotFoundError, pickle.UnpicklingError) as e:
            print(f"Error loading model: {e}")
            raise RuntimeError("Failed to load recommendation model")

    async def get_movies(self, query, moviename, page, user_id):
        start = time.time()
        movies = []
        
        if query == "search":
            # Using direct query like in original app.py
            movies = self.session.query(Movies)\
                .filter(Movies.title.like(f"%{moviename}%"))\
                .order_by(Movies.release_year.desc())\
                .limit(10).all()
            movie_ids = [movie.movieId for movie in movies]
        
        elif query == "recommend":
            # Using your get_top_n_recommendations script
            movie_ids_with_scores = get_top_n_recommendations(db.engine, self.model, user_id, 10)
            movie_ids = [movie[0] for movie in movie_ids_with_scores]
            movies = self.session.query(Movies)\
                .filter(Movies.movieId.in_(movie_ids))\
                .order_by(Movies.release_year.desc())\
                .limit(10).all()
        
        elif query == "popular":
            # Using your get_popular_movies script
            movie_titles, movie_release_years = get_popular_movies(page)
            movies = self.session.query(Movies).filter(
                or_(
                    *[and_(Movies.title == title, Movies.release_year == year) 
                      for title, year in zip(movie_titles, movie_release_years)]
                )
            ).all()
            movies.reverse()  # Most recent first
            
        movie_ids = [movie.movieId for movie in movies]
        ratings = self.session.query(Ratings)\
            .filter(Ratings.userId == user_id, Ratings.movieId.in_(movie_ids)).all()
        ratings_dict = {rating.movieId: rating.rating for rating in ratings}

        # Using GreenPool for parallel movie info fetching
        pool = GreenPool(10)
        movie_infos = pool.imap(get_movie_info, movies)

        movies_list = []
        for movie, (poster, description) in zip(movies, movie_infos):
            movies_list.append({
                'movieId': movie.movieId,
                'title': movie.title,
                'release_year': movie.release_year,
                'img': poster,
                'description': description,
                'rating': ratings_dict.get(movie.movieId),
                'moviename': moviename,
            })

        print(f"Getting movie info time: {time.time() - start}")
        return movies_list

    def add_or_update_rating(self, user_id, movie_id, rating):
        existing_rating = self.session.query(Ratings)\
            .filter_by(userId=user_id, movieId=movie_id).first()
            
        if existing_rating:
            existing_rating.rating = rating
        else:
            new_rating = Ratings(userId=user_id, movieId=movie_id, rating=rating)
            self.session.add(new_rating)
            
        self.session.commit()