from mcp.server.fastmcp import FastMCP
import os
import mcp
import sys
from dotenv import load_dotenv
import requests
from slack_bolt import App

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="logs.log",
    format='%(asctime)s - %(process)d - %(name)s - %(filename)s:%(lineno)d - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO)

mcp = FastMCP(
    name="Slack",
    host="0.0.0.0",  # only used for SSE transport (localhost)
    port=3000,  # only used for SSE transport (set this to any port)
)

@mcp.tool()
async def acronym_search(ACRONYM) -> dict:
    """Fetches the the acronym details. Returns the acronym details nicely formatted."""
    import requests
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    url = f"https://phx-pccas-u04.paypalcorp.com:9000/domportal/apiv1/misc/Acronyms/{ACRONYM.upper()}"

    response = requests.get(url, verify=False, headers={'Content-Type': 'application/json'})

    if response.status_code == 200:
        acronym_details = response.json()
        
        data = {}
        for i, detail in enumerate(acronym_details):
            definition = detail['definition']
            
            data[i] = definition

        logger.info(f"Acronym details fetched: {data}")

        return data
    else:
        logger.error(f"Failed to fetch data. Status code: {response.status_code}")
        return {}


@mcp.tool()
async def post_slack_message(data) -> str:
    """Posts the data to Slack channel."""
    logger.info(f"data in post_slack_message: {data}, type: {type(data)}")
    
    # Load environment variables from .env file
    load_dotenv()

    # Initialize your Slack Bolt app with your bot token and signing secret
    app = App(
        token=os.getenv("SLACK_BOT_TOKEN"),
        signing_secret=os.getenv("SLACK_SIGNING_SECRET")
    )

    # Send the response
    result = app.client.chat_postMessage(
        channel=os.getenv("SLACK_CHANNEL_ID"),
        text=data
    )
    logger.info(f"Message sent successfully: {result}")
    return "Message sent successfully" 


@mcp.tool()
async def finish_task(message: str) -> dict:
    """Terminates the agent execution by either saying if the search was sucessfull or not."""
    return {"response": message}

if __name__ == "__main__":
    logger.info("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="sse")  # Run with stdio for direct execution
