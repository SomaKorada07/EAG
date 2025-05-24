from pydantic import BaseModel
import asyncio
# from google import genai
from concurrent.futures import TimeoutError
import json
from ast import literal_eval


import os
import paypal.aiplatform as paypal_aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig

# Import our centralized logger
from log_config import get_logger

# Get a logger for this module
logger = get_logger(__name__)

class Response(BaseModel):
    function_name: str
    params: list[str]
    final_ans: str
    reasoning_type: str


os.environ['CLOUD_ENV']='DEV51'

# Initialize SDK
paypal_aiplatform.init("paypal_genai_sdk_config.json")

PROJECT_ID = ""
vertexai.init(project=PROJECT_ID, location="us-central1")

client = GenerativeModel(
    model_name="gemini-2.0-flash"
)

async def generate_with_timeout(prompt, timeout=10):
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.generate_content(
                        contents=prompt,
                        generation_config=GenerationConfig(
                            response_mime_type='application/json',
                            response_schema=Response.model_json_schema()
                        )
                )
            ),
            timeout=timeout
        )
        return response
    except TimeoutError:
        logger.error("LLM generation timed out!")
        raise
    except Exception as e:
        logger.error(f"Error in LLM generation: {e}")
        raise

def validate_response(response_text):
    try:
        parsed = literal_eval(json.loads(json.dumps(response_text.strip())))
        if not isinstance(parsed, dict):
            logger.error("Response is not a valid JSON object")
            raise ValueError("Response is not a valid JSON object")
        Response(**parsed)
        return parsed
    except Exception as e:
        raise ValueError(f"Invalid response format: {e}")