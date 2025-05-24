# Agentic AI System for acronym search

This project implements an agentic AI system that can interact with users through Slack, process natural language queries, make decisions using Large Language Models (LLMs), and perform actions through various tools. The system uses a structured, modular approach with a Model-Context-Protocol (MCP) based architecture and includes components for perception (LLM-based understanding), decision making, action execution, and memory persistence. Implements the Server-Sent Events protocol for communication between components.

## System Architecture

The project is built around several key components:

1. **SSE Server (`sse_server.py`)**: Provides a set of tools (acronym search, Slack messaging)

2. **SSE Client (`sse_client.py`)**: Handles user interactions and orchestrates the agent workflow

3. **LLM Perception (`llm_perception.py`)**: Handles communication with the Gemini 2.0 model for natural language understanding.

4. **Decision Maker (`decision_maker.py`)**: Processes user input and model responses to determine the next action.

5. **Action Performer (`action_performer.py`)**: Executes selected tools/actions based on decisions.

6. **Memory Handler (`memory_handler.py`)**: Maintains state across interactions, storing conversation history and results.

7. **Logging System (`log_config.py`)**: Centralized logging configuration that outputs to timestamped files in the `logs` directory.

## Key Components

### SSE Server (`sse_server.py`)

The server component provides the following tools via the Model-Context-Protocol (MCP):

- **acronym_search**: Fetches acronym definitions from a PayPal internal API
- **post_slack_message**: Sends messages to a specified Slack channel
- **finish_task**: Terminates the agent execution with a success/failure message

The server can run in two modes:
- Development mode: `python sse_server.py dev`
- Production mode: `python sse_server.py` (uses SSE transport)

### SSE Client (`sse_client.py`)

This component manages:

1. Interaction with the SSE server to access tools
2. Handling Slack events (particularly messages)
3. Orchestrating the agent's reasoning process through iterations
4. Managing the execution flow with a maximum of 5 iterations

The client also integrates with Slack's Socket Mode to listen for messages and process them asynchronously.

### LLM Perception (`llm_perception.py`)

This module handles:

1. Communication with Google's Vertex AI using the Gemini 2.0 Flash model
2. Response schema validation using Pydantic
3. Timeout handling for LLM requests
4. Error handling for malformed responses

### Decision Maker (`decision_maker.py`)

Responsible for:

1. Creating tool descriptions from the available tools
2. Constructing prompts by combining:
   - Tool descriptions
   - Base prompts from `prompt.py`
   - User query
   - Decision history

### Action Performer (`action_performer.py`)

Handles the execution of tools with:

1. Parameter type conversion based on tool schemas
2. Special handling for string parameters:
   - Formatting lists as bullet points
   - Removing duplicates while preserving order
3. Error handling during tool execution

### Memory Handler (`memory_handler.py`)

Manages the system's state:

1. Saves and loads state from a JSON file
2. Tracks iterations and responses
3. Provides functions to clear state between runs

### Logging System (`log_config.py`)

Provides centralized logging with:

1. Timestamp-based log filenames for each program run
2. Consistent log format across all components
3. Shared logger instance for all modules

## Prompt Templates

The system uses structured prompts (defined in `prompt.py`) with:

1. A prefix prompt explaining the agent's role and available tools
2. A main prompt with detailed instructions and JSON response formats
3. Step-by-step reasoning guides for the LLM
4. Example flows to guide the response structure

## Workflow

1. User sends a message to the Slack bot
2. Client processes the message and starts an iteration cycle
3. LLM generates a decision based on the prompt and available tools
4. The chosen tool is executed with the provided parameters
5. Results are stored in the state and used for the next iteration
6. The process continues until:
   - The task is completed successfully
   - The maximum number of iterations is reached
   - An unrecoverable error occurs

## Prerequisites

- Python 3.11 or higher
- Slack workspace with configured app (for Slack integration)
- PayPal AI Platform SDK credentials

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd test_proj
```

### 2. Environment Setup

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
1. pip install uv
2. uv init acronym_search
3. uv add paypal-aiplatform-sdk --index-url https://artifactory.paypalcorp.com/artifactory/api/pypi/paypal-python-all/simple --verbose
4. uv pip install mcp
5. uv pip install slack_bolt

#### Alternate Approach
The project uses `uv` for dependency management:

```bash
pip install uv
uv pip install -e .
```

This will install all dependencies listed in the `pyproject.toml` file.


### 4. Configuration

#### PayPal GenAI SDK Configuration

Ensure you have a valid `paypal_genai_sdk_config.json` file in the project root directory.

#### Environment Variables

Create a `.env` file in the project root with the following variables:

```
SLACK_BOT_TOKEN=your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
SLACK_APP_TOKEN=your-slack-app-token
SLACK_CHANNEL_ID=your-slack-channel-id
```

### 5. Starting the System

#### Start the SSE Server

```bash
uv run sse_server.py
```

Or for development mode:

```bash
uv run sse_server.py dev
```

#### Start the Slack Integration

In a separate terminal:

```bash
uv run sse_client.py
```

## Usage

Once the system is running, you can interact with it through your configured Slack workspace. The agent can:

1. Search for acronym definitions
2. Post messages to Slack channels
3. Process user queries and provide responses

The system maintains a state file (`state.json`) that tracks the conversation history and tool executions.

## Project Structure

```
test_proj/
├── action_performer.py    # Handles tool execution
├── decision_maker.py      # Determines next actions based on input
├── llm_perception.py      # Interfaces with LLM (Gemini)
├── log_config.py          # Centralized logging configuration
├── logs/                  # Directory containing log files
├── main.py                # Entry point for basic testing
├── memory_handler.py      # Manages state and conversation history
├── paypal_genai_sdk_config.json  # SDK configuration
├── prompt.py              # Prompt templates for LLM
├── pyproject.toml         # Project dependencies
├── README.md              # This documentation
├── sse_client.py          # Client for SSE communication
├── sse_server.py          # Server for SSE communication
└── state.json             # Current state of the system
```

## Error Handling

The system includes robust error handling:
1. LLM timeout and response validation
2. Tool execution error handling
3. State management error recovery
4. Logging of all errors for debugging

## Logging

The system uses a centralized logging configuration that saves logs to the `logs/` directory with timestamped filenames. Each log entry includes:
- Timestamp
- Process ID
- Module name
- File and line number
- Log level
- Message

## Development Guidelines

When extending the system:

1. Use the `get_logger` function from `log_config.py` to obtain a logger for new modules
2. Add new tools by implementing them in the SSE server
3. Update prompt templates in `prompt.py` if needed
4. Test changes incrementally

## Troubleshooting

Common issues:

1. **Connection Errors**: Ensure the SSE server is running before starting the client
2. **Authentication Failures**: Verify your Slack tokens and PayPal API credentials
3. **Log Issues**: Check the `logs` directory for detailed error information
