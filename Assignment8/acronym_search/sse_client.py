import traceback
from mcp.client.sse import sse_client
from mcp import ClientSession

import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

from llm_perception import generate_with_timeout, validate_response
from decision_maker import create_tool_descriptions, construct_prompt
from action_performer import execute_tool
from memory_handler import add_iteration, clear_state

# Import our centralized logger
from log_config import get_logger

# Get a logger for this module
logger = get_logger(__name__)

# Load environment variables from .env file
load_dotenv()

MAX_ITERATIONS = 5

# Initialize your Slack Bolt app with your bot token and signing secret
app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET")
)

# Get the app token from the .env file
app_token = os.getenv("SLACK_APP_TOKEN")
if not app_token:
    raise ValueError("SLACK_APP_TOKEN is not set in the environment variables.")

async def client(query):
    clear_state()
    iteration_count = 0

    async with sse_client("http://localhost:3000/sse") as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            tool_desc = create_tool_descriptions(tools)

            while iteration_count < MAX_ITERATIONS:
                logger.info(f"\n--- Iteration {iteration_count + 1} ---")
                
                prompt = construct_prompt(tool_desc, query)

                try:
                    response = await generate_with_timeout(prompt)
                    parsed_llm_response = validate_response(response.text)
                except Exception as e:
                    add_iteration(f"Issue in JSON response schema from LLM as: {e}")
                    iteration_count += 1
                    continue
                
                logger.info(f"Parsed llm response: {parsed_llm_response}")
                func_name = parsed_llm_response.get("function_name")
                if func_name and func_name != "None":
                    try:
                        tool = next(t for t in tools if t.name == func_name)
                        args, output = await execute_tool(session, tool, func_name, parsed_llm_response["params"])
                        
                        result = {
                            "llm_response": parsed_llm_response,
                            "tool": func_name,
                            "params": args,
                            "result": output,
                        }
                        logger.info(f"Tool execution result: {result}")
                        # Add the result to the state
                        add_iteration(result)

                        if func_name == "finish_task":
                            return output
                    except Exception as e:
                        traceback.print_exc()
                        add_iteration(f"Error executing {func_name}: {e}")
                        return str(e)
                else:
                    add_iteration({"Exception": parsed_llm_response})

                iteration_count += 1


# Listen for messages in channels
@app.event("message")
def handle_messages(body, logger):
    """Handle messages in any channel type"""
    event = body.get("event", {})
    
    # Ignore messages from bots to prevent loops
    if event.get("bot_id"):
        return
    
    # Get the message details
    text = event.get("text", "")
    user = event.get("user", "")
    channel = event.get("channel", "")
    channel_type = event.get("channel_type", "")
    
    if channel_type == "im":
        logger.info(f"Received DM from {user} in {channel}: {text}")
    else:
        logger.info(f"Received message from {user} in {channel} (type: {channel_type}): {text}")
    
    # For async handling, we need to use the app.client's async methods
    # or process in a non-blocking way
    import asyncio
    
    # Run the async client in a separate thread
    def run_async_client():
        logger.info(f"Running async client for user {user} in channel {channel}")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(client(text))
        if response:
            logger.info(f"Response from async client: {response}")
        loop.close()
    
    # Start the async processing in a separate thread
    import threading
    thread = threading.Thread(target=run_async_client)
    thread.start()

def main():
    # Register the message handler
    handler = SocketModeHandler(app, app_token)
    handler.start()

    print("Bot is running...")

if __name__ == "__main__":
    main()