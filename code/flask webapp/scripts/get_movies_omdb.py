# import os
# from dotenv import load_dotenv
# import aiohttp

# load_dotenv()
# base_url = f"http://www.omdbapi.com/?apikey={os.getenv('OMDB_API_KEY')}&"

# async def get_movie_info(session, movie_title, release_year):
#     full_url = base_url + f"t={movie_title}&y={release_year}"
#     try:
#         async with session.get(full_url) as response:
#             movies = await response.json()
#     except Exception as e:
#         print(f"Error fetching data for {movie_title}: {e}")
#         return "None", "None"

#     if movies.get("Response") == "True":
#         return movies.get("Poster", "None"), movies.get("Plot", "None")
#     else:
#         return "None", "None"
    
from dotenv import load_dotenv
import requests
import os
import eventlet

load_dotenv()
base_url = f"http://www.omdbapi.com/?apikey={os.getenv('OMDB_API_KEY')}&"

def get_movie_info(movie):
    movie_title = movie.title
    release_year = movie.release_year
    full_url = f"{base_url}t={movie_title}&y={release_year}"
    try:
        response = requests.get(full_url, timeout=5)
        response.raise_for_status()
        movies = response.json()
    except requests.RequestException as e:
        print(f"Error fetching data for {movie_title}: {e}")
        return "None", "None"

    if movies.get("Response") == "True":
        return movies.get("Poster", "None"), movies.get("Plot", "None")
    else:
        return "None", "None"