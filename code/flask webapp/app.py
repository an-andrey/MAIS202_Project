from flask import Flask, render_template, flash, redirect, url_for, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from scripts.get_overview_tmdb import get_movie_description
from scripts.get_poster_tmdb import get_movie_poster
from scripts.get_recommendations import get_top_n_recommendations, get_unwatched_movies
from sqlalchemy.orm import sessionmaker
import pandas as pd
import pickle 

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

#Flask_login 
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

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

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/movies")
@login_required
def movies():
    search = request.args.get("search", "False")
    moviename = request.args.get("moviename", "")
    movies =[]
    userId = current_user.id
    if search == "True":
        movies = Movies.query.filter(Movies.title.like(f"%{moviename}%")).all()
    elif search == "False":
        
        movie_ids = get_top_n_recommendations(db.engine,model,userId,10)
        movies = Movies.query.filter(Movies.movieId.in_([movie[0] for movie in movie_ids])).all()
        
    # Convert the movies to a list of dictionaries
    movies_list = []
    for movie in movies:

        rating = Ratings.query.filter_by(userId=userId, movieId=movie.movieId).first()
        current_rating = rating.rating if rating else None

        movie_dict = {
            'movieId':movie.movieId,
            'title': movie.title,
            'release_year': movie.release_year,
            'img' : get_movie_poster(movie.title, movie.release_year),
            'description' : get_movie_description(movie.title, movie.release_year),
            'rating': current_rating
        }
        movies_list.append(movie_dict)
     
    
    return render_template("movie.html", movies=movies_list)

@app.route("/search_movie", methods=["GET"])
@login_required
def search_movie():
    word = request.args.get("searchbar")
    return redirect(url_for("movies",search="True", moviename=word) )

@app.route("/add_review",methods=["GET","POST"])
def rate_movie():
    rating = int(request.form.get("rating"))
    movieId = request.form.get("movieId")
    print(rating,movieId)

    return redirect(url_for("movies"))

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
