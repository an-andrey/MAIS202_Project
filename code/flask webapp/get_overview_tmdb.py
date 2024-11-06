import requests

# TMDb API configuration
bearer_token = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI4MTgzYjNhYjE0OGE3MDMxYWI0NzIyMDBiNzhjZTgxNCIsIm5iZiI6MTczMDU5NjE1My4wNDg5NTg4LCJzdWIiOiI2NzI2Y2M3ZDlkY2MyZGQ1MzQ3NDNlMTEiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.YdKyl45flLsUrluQf2XwFgJHaZ_ctDC_kyCrhzSTJYc"
base_url = "https://api.themoviedb.org/3"

headers = {
    "accept": "application/json",
    "Authorization": bearer_token
}

def get_movie_options(movie_title, release_year):
    # Search for the movie title and release year on TMDb
    search_url = f"{base_url}/search/movie?query={movie_title}&year={release_year}"
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

def get_movie_description(movie_id):
    # Get the movie details by ID
    details_url = f"{base_url}/movie/{movie_id}"
    response = requests.get(details_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: Received status code {response.status_code}")
        print("Response:", response.json())  # Print the full response for debugging
        return "No description available due to an error."

    movie_data = response.json()
    
    # Retrieve and return the movie description if available
    description = movie_data.get('overview')
    if description:
        return description
    else:
        return "No description available for this movie."

# Main program
movie_title = input("Enter the movie title: ")
release_year = input("Enter the release year: ")
movie_options = get_movie_options(movie_title, release_year)

if movie_options:
    selected_movie = movie_options[0]  # Select the top result
    description = get_movie_description(selected_movie['id'])
    print(f"Description: {description}")
else:
    print("No exact match found for the given title and release year.")
