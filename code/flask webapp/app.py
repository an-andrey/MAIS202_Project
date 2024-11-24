import eventlet
eventlet.monkey_patch()
from eventlet.greenpool import GreenPool

from flask import Flask, render_template, flash, redirect, url_for, request, session, make_response, jsonify
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, FloatField
from wtforms.validators import DataRequired
from sqlalchemy import create_engine, text, and_, or_
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from scripts.get_overview_tmdb import get_movie_description
from scripts.get_poster_tmdb import get_movie_poster
from scripts.get_recommendations import get_top_n_recommendations, get_unwatched_movies
from scripts.get_movies_omdb import get_movie_info
from scripts.get_popular import get_popular_movies
from sqlalchemy.orm import sessionmaker
import pandas as pd
from scripts.re_train import retrain_svd_model
import time
import os
import pickle
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.future import select
from flask_socketio import SocketIO
from flask import jsonify
import threading

task_status = {'done': False, 'redirect_url': None}

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "FLASK_SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DB_URL")
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {
        'ssl': {
            'ca': 'code/flask webapp/ca.pem'
        }
    }
}

# ASYNC_DB_URL = os.getenv("ASYNC_DB_URL")
# engine = create_async_engine(ASYNC_DB_URL, echo=True)
# async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

db = SQLAlchemy(app)

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='eventlet',
    ping_timeout=300,
    ping_interval=60,
    logger=True,
    engineio_logger=True
)

with open("code/flask webapp/models/svd_model.pkl", "rb") as f:
    model = pickle.load(f)

with app.app_context():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db.engine)
    Session = scoped_session(SessionLocal)

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

class Ratings(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    userId = db.Column(db.BigInteger, nullable=False, index=True)
    movieId = db.Column(db.BigInteger, nullable=False, index=True)
    rating = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Ratings(id={self.id}, userId={self.userId}, movieId={self.movieId}, rating={self.rating}>"

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Log-in")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/movies")
@login_required
async def movies():
    start = time.time()
    query = request.args.get("query", "")
    moviename = request.args.get("moviename", "")
    page_to_load = request.args.get("p", "1")
    movies =[]
    userId = current_user.id
    session = Session()
    try:
        if query == "search":
            movies = session.query(Movies)\
                .filter(Movies.title.like(f"%{moviename}%"))\
                .order_by(Movies.release_year.desc())\
                .limit(10).all()
            movie_ids = [movie.movieId for movie in movies]
        
        elif query == "recommend":
            movie_ids_with_scores = get_top_n_recommendations(db.engine, model, userId, 10)
            movie_ids = [movie[0] for movie in movie_ids_with_scores]
            movies = session.query(Movies)\
                .filter(Movies.movieId.in_(movie_ids))\
                .order_by(Movies.release_year.desc())\
                .limit(10).all()
        
        elif query == "popular":
            print("Getting popular movies on page", page_to_load)
            movie_titles, movie_release_years = get_popular_movies(page_to_load)
            movies = session.query(Movies).filter(
                or_(
                    *[and_(Movies.title == title, Movies.release_year == year) for title, year in zip(movie_titles, movie_release_years)]
                )
            ).all()
            movie_ids = [movie.movieId for movie in movies]

            movies.reverse()
            movie_ids.reverse()
                        
        ratings = session.query(Ratings).filter(Ratings.userId == userId, Ratings.movieId.in_(movie_ids)).all()
        ratings_dict = {rating.movieId: rating.rating for rating in ratings}

        # Initialize GreenPool
        pool = GreenPool(10)  # Adjust the pool size as needed
        movie_infos = pool.imap(get_movie_info, movies)

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
                'moviename': moviename,
            }

            movies_list.append(movie_dict)
        
        query_info = {
            'query': query,
            #display the next page that will be loaded if called. 
            'page_to_load': int(page_to_load) + 1
        }
    finally:
        session.close()
    print(f"Getting movie info time: {time.time() - start}")    
    return render_template("movie.html", movies=movies_list, query_info=query_info)

def fetch_movie_info(session, movie):
    poster, description = get_movie_info(session, movie.title, movie.release_year)
    return poster, description

@app.route("/add_rating", methods=["POST"])
@login_required
def add_rating():
    rating = float(request.form.get("rating"))
    movieId = request.form.get("movieId")
    query = request.form.get("query")
    moviename = request.form.get("moviename")
    page = request.form.get("p")

    session = Session()
    try:
        existing_rating = session.query(Ratings).filter_by(userId=current_user.id, movieId=movieId).first()

        if existing_rating:
            existing_rating.rating = rating
            session.commit()
            print("Rating updated successfully")
        else:
            new_rating = Ratings(userId=current_user.id, movieId=movieId, rating=rating)
            session.add(new_rating)
            session.commit()
            print("Rating added successfully")
    finally:
        session.close()

    # Redirect to loading page
    return redirect(url_for('start_task', query=query, moviename=moviename, page= page))

@app.route('/start_task')
@login_required
def start_task():
    query = request.args.get('query')
    moviename = request.args.get('moviename',"")
    page = request.args.get('page',"1")
    
    # Reset task status
    task_status['done'] = False
    task_status['redirect_url'] = None
    
    # Start background task
    thread = threading.Thread(target=background_task, args=(query, moviename, page))
    thread.start()
    
    return render_template('loading.html')

@app.route('/check_task_status')
@login_required
def check_task_status():
    return jsonify(task_status)

def background_task(query, moviename, page):
    with app.app_context():
        # Get ratings
        ratings_df = get_all_ratings()

        # Retrain model
        retrain_svd_model(ratings_df)

        task_status['done'] = True
        task_status['redirect_url'] = f"/movies?query={query}&moviename={moviename}&p={page}"

def get_all_ratings():
    with app.app_context():
        try:
            query = "SELECT userId, movieId, rating FROM ratings"
            start_time = time.time()
            print("Started getting ratings")
            ratings_df = pd.read_sql_query(query, db.engine)
            fetch_time = time.time() - start_time
            print(f"Ratings fetched in {fetch_time:.2f} seconds")
            return ratings_df
        except Exception as e:
            print(f"Error in get_all_ratings: {e}")
            return pd.DataFrame()

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

@app.route("/search_movie", methods=["GET"])
@login_required
def search_movie():
    word = request.args.get("searchbar")
    return redirect(url_for("movies",query="search", moviename=word) )

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
    socketio.run(app, debug=True, port=3000)