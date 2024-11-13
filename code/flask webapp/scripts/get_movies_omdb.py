# import os 
# from dotenv import load_dotenv
# import requests
# import json

# load_dotenv()
# base_url = f"http://www.omdbapi.com/?apikey={os.getenv("OMDB_API_KEY")}&"
# def get_movie_info(movie_title, release_year):
#     full_url = base_url + f"t={movie_title}&y={release_year}"
#     movies = requests.get(full_url).json()
    
#     if movies["Response"] == "True":
#         return movies["Poster"],movies["Plot"]
#     else:
#         return "None","None"

import os
from dotenv import load_dotenv
import aiohttp
import asyncio

load_dotenv()
base_url = f"http://www.omdbapi.com/?apikey={os.getenv('OMDB_API_KEY')}&"

async def get_movie_info(movie_title, release_year):
    full_url = base_url + f"t={movie_title}&y={release_year}"
    async with aiohttp.ClientSession() as session:
        async with session.get(full_url) as response:
            movies = await response.json()
    
    if movies["Response"] == "True":
        return movies["Poster"], movies["Plot"]
    else:
        return "None", "None"