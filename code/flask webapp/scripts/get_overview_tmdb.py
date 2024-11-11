import requests
import os 
from dotenv import load_dotenv

#script that gets the description of a movie from TMDb
load_dotenv()

# TMDb API configuration
bearer_token = os.getenv("TMDB_BEARER")
base_url = "https://api.themoviedb.org/3"

headers = {
    "accept": "application/json",
    "Authorization": bearer_token
}

def get_movie_description(movie_title, release_year):
    # Search for the movie title and release year on TMDb
    search_url = f"{base_url}/search/movie?query={movie_title}&year={release_year}"
    response = requests.get(search_url, headers=headers)
    
    # Check for response status and errors
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        return "None"
    
    response_json = response.json()
    
    # Check if 'results' key exists
    if 'results' in response_json and response_json['results'] and response_json['results'][0]["release_date"][:4] == str(release_year):
        # Display the list of movies found
        movies = response_json['results']
        
        description = movies[0]["overview"]

        return description
    else:
        print("No results found or invalid response format.")
        return "None"
