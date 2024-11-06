import requests
import os 
import dotenv

load_env()

# TMDb API configuration
bearer_token = os.get_env("TMDB_BEARER")
base_url = "https://api.themoviedb.org/3"
image_base_url = "https://image.tmdb.org/t/p/w500"  # Adjust size if needed

headers = {
    "accept": "application/json",
    "Authorization": bearer_token
}

def get_movie_options(movie_title):
    # Search for the movie title on TMDb
    search_url = f"{base_url}/search/movie?query={movie_title}"
    response = requests.get(search_url, headers=headers)
    
    # Check for response status and errors
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        print("Response:", response.json())  # Print the full response for debugging
        return []
    
    response_json = response.json()
    
    # Check if 'results' key exists
    if 'results' in response_json and response_json['results']:
        # Display the list of movies found
        movies = response_json['results']
        for i, movie in enumerate(movies):
            title = movie.get('title', 'Unknown Title')
            release_date = movie.get('release_date', 'Unknown Date')
            print(f"{i + 1}. {title} ({release_date[:4]})")
        return movies
    else:
        print("No results found or invalid response format.")
        return []

def get_poster_url(movie_id):
    # Get the movie details by ID
    details_url = f"{base_url}/movie/{movie_id}"
    response = requests.get(details_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        print("Response:", response.json())  # Print the full response for debugging
        return "No poster available due to an error."

    movie_data = response.json()
    
    # Retrieve and return the poster URL if available
    poster_path = movie_data.get('poster_path')
    if poster_path:
        return f"{image_base_url}{poster_path}"
    else:
        return "No poster available for this movie."

# Main program
movie_title = input("Enter the movie title: ")
movie_options = get_movie_options(movie_title)

if movie_options:
    choice = input("Select the number of the movie you want, or press Enter for the top result: ")
    try:
        selected_movie = movie_options[int(choice) - 1] if choice else movie_options[0]
        poster_url = get_poster_url(selected_movie['id'])
        print(f"Poster URL: {poster_url}")
    except (IndexError, ValueError):
        print("Invalid selection. Please try again.")
