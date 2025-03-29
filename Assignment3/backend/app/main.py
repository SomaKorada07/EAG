import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.agents.movie_agent import MovieAgent
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

movie_agent = MovieAgent()

class EmailRequest(BaseModel):
    email: str

@app.post("/fetch-and-send")
async def fetch_and_send_movies(request: EmailRequest):
    try:
        logger.info(f"Received request for email: {request.email}")
        result = movie_agent.execute(request.email)
        logger.info("Request completed successfully")
        return {"status": "success", "message": result}
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 