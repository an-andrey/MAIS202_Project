from flask import Flask, render_template, flash, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FloatField
from wtforms.validators import DataRequired
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from scripts.get_overview_tmdb import get_movie_description
from scripts.get_poster_tmdb import get_movie_poster
from scripts.get_recommendations import get_top_n_recommendations, get_unwatched_movies
from scripts.get_movies_omdb import get_movie_info
from sqlalchemy.orm import sessionmaker
import pandas as pd
import pickle
from scripts.re_train import async_retrain_svd_model
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import aiohttp

load_dotenv()

app = Flask(__name__)

#using joblib
#model = joblib.load("code/flask webapp/scripts/svd_model.joblib")

#using pickle
with open("code/flask webapp/models/svd_model.pkl", "rb") as f:
    model = pickle.load(f)

# Secret Key Configuration
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "FLASK_SECRET_KEY")

# Database URI and SSL Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL")
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {
        'ssl': {
            'ca': 'code/flask webapp/ca.pem'  
        }
    }
}

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Set up the session factory
with app.app_context():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db.engine)
    Session = scoped_session(SessionLocal)

#Flask_login 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    session = Session()
    try:
        user = session.query(Users).filter(Users.id == int(user_id)).first()
        return user
    finally:
        session.close()

####################
# MODEL RETRAINING #
####################

def get_all_ratings():
    query = text("SELECT userId, movieId, rating FROM ratings")
    with db.engine.connect() as connection:
        result = connection.execute(query)
        ratings = result.fetchall()
    ratings_df = pd.DataFrame(ratings, columns=["userId", "movieId", "rating"])
    print("got all the ratings")
    return ratings_df

################
#CLASSES FOR DB#
################
class Ratings(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    userId = db.Column(db.BigInteger, nullable=False)
    movieId = db.Column(db.BigInteger, nullable=False)
    rating = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Ratings(id={self.id}, userId={self.userId}, movieId={self.movieId}, rating={self.rating}>"

class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return "<Name %r>" %self.username

class Movies(db.Model):
    __tablename__ = "movies"

    movieId = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    genres = db.Column(db.String(200), nullable=False)
    release_year = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Movies(movieId={self.movieId}, title={self.title}, genres={self.genres}>"
    
class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Log-in")

##########
# ROUTES #
##########
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/movies")
@login_required
async def movies():
    start = time.time()
    search = request.args.get("search", "False")
    moviename = request.args.get("moviename", "")
    movies =[]
    userId = current_user.id
    session = Session()
    try:
        if search == "True":
            movies = session.query(Movies)\
                .filter(Movies.title.like(f"%{moviename}%"))\
                .order_by(Movies.release_year.desc())\
                .limit(10).all()
            movie_ids = [movie.movieId for movie in movies]
        else:
            movie_ids_with_scores = get_top_n_recommendations(db.engine, model, userId, 10)
            movie_ids = [movie[0] for movie in movie_ids_with_scores]
            movies = session.query(Movies)\
                .filter(Movies.movieId.in_(movie_ids))\
                .order_by(Movies.release_year.desc())\
                .limit(10).all()
            
        # Fetch all ratings in a single query
        ratings = session.query(Ratings).filter(Ratings.userId == userId, Ratings.movieId.in_(movie_ids)).all()
        ratings_dict = {rating.movieId: rating.rating for rating in ratings}

        # Fetch movie info asynchronously
        async with aiohttp.ClientSession() as aio_session:
            tasks = [fetch_movie_info(aio_session, movie) for movie in movies]
            movie_infos = await asyncio.gather(*tasks)

        # Convert the movies to a list of dictionaries
        movies_list = []
        for movie, (poster, description) in zip(movies, movie_infos):
            current_rating = ratings_dict.get(movie.movieId, None)

            movie_dict = {
                'movieId':movie.movieId,
                'title': movie.title,
                'release_year': movie.release_year,
                'img' : poster,
                'description' : description,
                'rating': current_rating,
                'search': search,
                'moviename': moviename
            }

            movies_list.append(movie_dict)

        
    finally:
        session.close()
    print(f"Getting movie info time: {time.time() - start}")    
    return render_template("movie.html", movies=movies_list)

#getting all posters/descriptions asynchronously
async def fetch_movie_info(aio_session, movie):
    # Ensure this function is asynchronous and returns a coroutine
    poster, description = await get_movie_info(movie.title, movie.release_year) 
    return poster, description

@app.route("/search_movie", methods=["GET"])
@login_required
def search_movie():
    word = request.args.get("searchbar")
    return redirect(url_for("movies",search="True", moviename=word) )

@app.route("/add_rating", methods=["GET", "POST"])
@login_required
def add_rating():
    rating = float(request.form.get("rating"))
    movieId = request.form.get("movieId")
    search = request.form.get("search")
    moviename = request.form.get("moviename")

    session = Session()
    try:
        # Check if the user has already rated this movie
        existing_rating = session.query(Ratings).filter_by(userId=current_user.id, movieId=movieId).first()

        if existing_rating:
            # Update the existing rating
            existing_rating.rating = rating
            session.commit()
            print("Rating updated successfully")
        else:
            # Add the new review to the database
            new_rating = Ratings(userId=current_user.id, movieId=movieId, rating=rating)
            session.add(new_rating)
            session.commit()
            print("Rating added successfully")
    finally:
        session.close()
   
    ratings_df = get_all_ratings()
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # No event loop in the current thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    loop.run_in_executor(None, asyncio.run, async_retrain_svd_model(ratings_df))
    
    return redirect(url_for("movies", search=search, moviename=moviename))

@app.route("/db")
def get_db():
    with db.engine.connect() as connection:
        try:
            # Execute query and fetch results
            result = connection.execute(text("SELECT * FROM movies LIMIT 10;"))
            rows = result.fetchall()  # Fetch all rows from the result
            print(rows)

        except Exception as e:
            print(f"An error occurred: {e}")
    return "db!"

#login page
@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()

        #If the user exists
        if user: 
            if user.password == form.password.data:
                login_user(user)
                return redirect(url_for("dashboard"))
            else: 
                flash("incorrect password, please try again")
        else: 
            flash("user does not exist")


    return render_template("login.html", form=form)

@app.route("/logout",methods=["GET","POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

#dashboard page
@app.route("/dashboard",methods=["GET","POST"])
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    
    if form.validate_on_submit():
        # Check if the username already exists
        user = Users.query.filter_by(username=form.username.data).first()
        if user:
            flash("Username already exists. Please choose a different one.", "danger")
            # Don't redirect; render the template again with the form and error message
            return render_template("register.html", form=form, our_users=Users.query.all())
        else:
            # Create a new user
            new_user = Users(username=form.username.data, password=form.password.data)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for("dashboard", user=new_user))

    # Render the form with the current data if the user submits an invalid form
    return render_template("register.html", form=form, our_users=Users.query.all())

if __name__ == "__main__":
    app.run(debug=True)
