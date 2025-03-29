import os
import requests
from typing import List, Dict

class MovieTool:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    def fetch_top_movies(self) -> List[Dict]:
        """Fetch top-rated movies using Gemini"""
        prompt = """
        Generate a list of 5 top-rated movies across different OTT platforms (Netflix, Prime, Disney+).
        For each movie, provide:
        1. Title
        2. Rating (out of 10)
        3. Platform where it's available
        4. Brief plot summary

        Format the response as a list of JSON objects with keys: title, rating, platform, plot
        Example format:
        [
            {
                "title": "Movie Name",
                "rating": 9.2,
                "platform": "Netflix",
                "plot": "Brief plot summary"
            }
        ]
        """

        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
            )

            if response.status_code != 200:
                raise Exception("Failed to fetch movies from Gemini")

            # Extract and parse the response
            content = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            
            # Clean up the response to get just the JSON part
            json_str = content.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].strip()
            
            # Convert string to Python list of dictionaries
            import json
            movies = json.loads(json_str)
            
            # Validate and format the response
            formatted_movies = []
            for movie in movies:
                formatted_movies.append({
                    "title": movie.get("title", "Unknown"),
                    "rating": float(movie.get("rating", 0.0)),
                    "platform": movie.get("platform", "Unknown"),
                    "plot": movie.get("plot", "No plot available")
                })

            return formatted_movies

        except Exception as e:
            # Fallback to default movies in case of error
            print(f"Error fetching movies from Gemini: {str(e)}")
            return [
                {
                    "title": "The Shawshank Redemption",
                    "rating": 9.3,
                    "platform": "Netflix",
                    "plot": "A banker is sentenced to life in Shawshank State Penitentiary."
                },
                {
                    "title": "The Godfather",
                    "rating": 9.2,
                    "platform": "Prime",
                    "plot": "The aging patriarch of an organized crime dynasty transfers control."
                }
            ] 