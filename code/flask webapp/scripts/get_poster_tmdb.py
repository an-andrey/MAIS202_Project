import requests
import os 
from dotenv import load_dotenv

#script that gets the movie poster from TMDb
load_dotenv()

# TMDb API configuration
bearer_token = os.getenv("TMDB_BEARER")
base_url = "https://api.themoviedb.org/3"
image_base_url = "https://image.tmdb.org/t/p/w500"  # Adjust size if needed

headers = {
    "accept": "application/json",
    "Authorization": bearer_token
}

def get_movie_poster(movie_title, release_year):
    # Search for the movie title on TMDb
    search_url = f"{base_url}/search/movie?query={movie_title}&release_year={release_year}"
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
        url = movies[0]["backdrop_path"]
        if url != "None":
            url = f"{image_base_url}{movies[0]["backdrop_path"]}"
        
        return url
    
    else:
        print("No results found")
        return "None"
    