import requests
import os 
from dotenv import load_dotenv
#script that gets the description of a movie from TMDb
load_dotenv()

# TMDb API configuration
bearer_token = os.getenv("TMDB_BEARER")

headers = {
    "accept": "application/json",
    "Authorization": bearer_token
}

def get_popular_movies(page=1):
    base_url = f"https://api.themoviedb.org/3/discover/movie?include_adult=true&include_video=false&language=en-US&page={page}&sort_by=popularity.desc&year=2022"

    response = requests.get(base_url, headers=headers)

    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        return "None"
    
    response_json = response.json()
    movie_titles = []
    release_years = []
    for movie in response_json["results"]:
        movie_titles.append(movie["title"])
        release_years.append(movie["release_date"][:4])

    return movie_titles, release_years