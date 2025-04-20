# Agent Architecture Example

This project demonstrates a modular agent architecture organized into distinct layers. The agent can process user inputs, make decisions, and execute actions including interacting with external tools via the Model Context Protocol (MCP) framework.

## Architecture

The codebase is structured following a layered agent architecture:

1. **Perception Layer** (`perception.py`)
   - Translates raw user input into structured information
   - Manages LLM (Gemini) interactions
   - Parses responses from the language model

2. **Memory Layer** (`memory.py`)
   - Stores facts and state about interactions
   - Implements simple in-memory storage
   - Manages conversation history and iteration tracking

3. **Decision Layer** (`decision.py`)
   - Decides what to do based on current input and memory
   - Reasons about options and picks action plans
   - Constructs prompts and processes model responses

4. **Action Layer** (`action.py`)
   - Executes decisions
   - Calls external MCP tools
   - Handles error cases and result processing

5. **Main Coordinator** (`main.py`)
   - Sets up the agent components
   - Manages the interaction loop
   - Initializes tools and system prompts

## Setup and Usage

1. Create a `.env` file with your Gemini API key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the agent:
   ```bash
   python main.py
   ```

## Example Capabilities

The agent is configured to solve mathematical reasoning tasks using tools, with capabilities including:
- Breaking down problems into steps
- Showing reasoning before performing calculations
- Verifying calculation results
- Using appropriate tools to handle different tasks

## Requirements

- Python 3.8+
- Google Gemini API access
- MCP framework support