from flask import Blueprint, render_template, request, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from app.services.movie_service import MovieService
from app.extensions import db
import threading
from scripts import get_all_ratings, retrain_svd_model

movie = Blueprint('movie', __name__)

@movie.route("/movies")
@login_required
async def movies():
    service = MovieService()
    query = request.args.get("query", "")
    moviename = request.args.get("moviename", "")
    page = request.args.get("p", "1")
    
    movies_list = await service.get_movies(query, moviename, page, current_user.id)
    query_info = {
        'query': query,
        'page_to_load': int(page) + 1
    }

    return render_template("movie.html", movies=movies_list, query_info=query_info)

@movie.route("/add_rating", methods=["POST"])
@login_required
def add_rating():
    service = MovieService()
    rating = float(request.form.get("rating"))
    movieId = request.form.get("movieId")
    query = request.form.get("query")
    moviename = request.form.get("moviename")
    page = request.form.get("p")
    
    service.add_or_update_rating(current_user.id, movieId, rating)
    return redirect(url_for('movie.start_task', query=query, moviename=moviename, page=page))

@movie.route("/search_movie", methods=["GET"])
@login_required
def search_movie():
    word = request.args.get("searchbar")
    return redirect(url_for("movie.movies", query="search", moviename=word))

task_status = {'done': False, 'redirect_url': None}

@movie.route('/start_task')
@login_required
def start_task():
    query = request.args.get('query')
    moviename = request.args.get('moviename', "")
    page = request.args.get('p', "1")
    
    # Reset task status
    task_status['done'] = False
    task_status['redirect_url'] = None
    
    # Start background task
    thread = threading.Thread(target=background_task, args=(query, moviename, page, current_app._get_current_object()))
    thread.start()
    
    return render_template('loading.html')

@movie.route('/check_task_status')
@login_required
def check_task_status():
    return jsonify(task_status)

def background_task(query, moviename, page, app):
    with app.app_context():
        ratings_df = get_all_ratings()
        retrain_svd_model(ratings_df)
        
        task_status['done'] = True
        task_status['redirect_url'] = f"/movies?query={query}&moviename={moviename}&p={page}"
