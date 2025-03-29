import os
from typing import List, Dict
import requests
from app.tools.movie_tool import MovieTool
from app.tools.email_tool import EmailTool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MovieAgent:
    def __init__(self):
        self.movie_tool = MovieTool()
        self.email_tool = EmailTool()
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.smtp_email = os.getenv("SMTP_EMAIL")
        self.smtp_password = os.getenv("SMTP_APP_PASSWORD")
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        if not self.smtp_email or not self.smtp_password:
            raise ValueError("SMTP credentials not found in environment variables")

    def execute(self, email: str) -> str:
        try:
            logger.info(f"Starting execution for email: {email}")
            
            system_prompt = """
            You are a movie recommendation agent with access to these tools:
            1. get_top_movies() - Fetches a list of top rated movies from various OTT platforms
            2. send_email(recipient, subject, content) - Sends an email

            Given a user's email address, what steps should you take to send them movie recommendations?
            Respond with the exact tool name you want to use.
            """

            logger.info("Getting tool decision from Gemini")
            tool_to_use = self._get_tool_decision(system_prompt)
            logger.info(f"Tool decision received: {tool_to_use}")

            if "get_top_movies" in tool_to_use.lower():
                logger.info("Fetching movies")
                movies = self.movie_tool.fetch_top_movies()
                logger.info(f"Received {len(movies)} movies")
                
                content_prompt = f"""
                Create and send an engaging email about these movies:
                {[{
                    'title': m['title'],
                    'rating': m['rating'],
                    'platform': m['platform'],
                    'plot': m['plot']
                } for m in movies]}
                
                Format: Create a friendly email that includes:
                1. A warm greeting
                2. For each movie:
                   - Title and rating
                   - Where to watch (platform)
                   - Brief plot description
                3. A friendly closing
                
                Make it engaging and conversational.
                """
                
                logger.info("Getting email content from Gemini")
                email_content = self._get_tool_decision(content_prompt)
                logger.info("Email content received")

                email_prompt = f"""
                You have an email ready to send:
                Recipient: {email}
                Content: {email_content}

                What tool should you use to send this email? Respond with the exact tool name.

                You are a movie recommendation agent with access to these tools:
                1. get_top_movies() - Fetches a list of top rated movies from various OTT platforms
                2. send_email(recipient, subject, content) - Sends an email
                """
                
                logger.info("Getting final tool decision")
                next_action = self._get_tool_decision(email_prompt)
                logger.info(f"Final tool decision: {next_action}")

                if "send_email" in next_action.lower():
                    logger.info("Sending email")
                    self.email_tool.send_email(
                        email, 
                        "Your Personalized Movie Recommendations", 
                        email_content
                    )
                    return "Email sent successfully with movie recommendations!"
                else:
                    raise Exception(f"Invalid email action received: {next_action}")
            else:
                raise Exception(f"Invalid movie fetch action received: {tool_to_use}")
        except Exception as e:
            logger.error(f"Error in execute: {str(e)}", exc_info=True)
            raise

    def _get_tool_decision(self, prompt: str) -> str:
        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                json={
                    "contents": [{
                        "parts": [{"text": prompt}]
                    }]
                }
            )
            
            logger.info(f"Gemini API response status: {response.status_code}")
            
            if response.status_code != 200:
                error_content = response.text
                logger.error(f"Gemini API error: {error_content}")
                raise Exception(f"Failed to get tool decision from Gemini: {error_content}")
                
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            logger.error(f"Error in _get_tool_decision: {str(e)}", exc_info=True)
            raise 