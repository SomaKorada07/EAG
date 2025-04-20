import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio

from perception import Perception
from memory import Memory
from decision import Decision
from action import Action

# Load environment variables from .env file
load_dotenv()

# Configuration
max_iterations = 6

async def main():
    print("Starting main execution...")
    try:
        # Initialize components
        memory = Memory()
        perception = Perception()
        
        # Create MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["example2-3.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                
                try:
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                system_prompt = f"""
You are a mathematical reasoning agent that solves problems step-by-step using structured thinking and specialized tools. Your approach combines careful reasoning with computational verification.
Available Tools:
{tools_description}

Response Format:
You must respond with EXACTLY ONE line in one of these formats:

FUNCTION_CALL: function_name|param1|param2|...
FINAL_ANSWER: [answer]

Problem-Solving Process:

First identify the type of reasoning required
Break down the problem into clear logical steps
Show your reasoning before performing calculations
Calculate each step and verify the results
If you're uncertain or detect an error, use appropriate tools to handle it
Only provide the final answer when all steps are complete and verified

Error Handling:

If you're uncertain about an approach, use uncertainty_check() with your confidence level
If a calculation seems incorrect, use correction() to fix it
If you can't solve the problem completely, explain what you can determine in your final answer

Conversation Example:
User: Find the ASCII values of characters in INDIA and calculate the sum of exponentials of those values.
Assistant: FUNCTION_CALL: show_reasoning|["1. First, find ASCII values: I,N,D,I,A using strings_to_chars_to_int", "2. Then calculate exponentials and add the exponentials using int_list_to_exponential_sum"]
User: Next step?
Assistant: FUNCTION_CALL: strings_to_chars_to_int|I,N,D,I,A
User: Result is 5. Let's verify this step.
Assistant: FUNCTION_CALL: verify_ascii|I,N,D,I,A|73,78,68,73,65
User: Verified. Next step?
Assistant: FUNCTION_CALL: int_list_to_exponential_sum|73,78,68,73,65|7.599e+33
User: Result is 7.599e+33.
Assistant: FINAL_ANSWER: [7.599e+33]
"""

                # Initialize remaining components
                decision = Decision(perception, memory)
                action = Action(session, tools, memory)
                
                # User query
                query = """Find the ASCII values of characters in INDIA and calculate the sum of exponentials of those values. Wait for a second and then open Paint. 
                            Draw a rectangle and write the final answer inside it. After that, return FINAL ANSWER: COMPLETED."""
                
                # Reset memory state
                memory.reset()
                
                # Main agent loop
                while memory.get_iteration() < max_iterations:
                    print(f"\n--- Iteration {memory.get_iteration() + 1} ---")
                    
                    # Decide next action
                    action_data = await decision.decide_next_action(system_prompt, query)
                    
                    # Execute the action
                    result = await action.execute(action_data)
                    
                    # Check if we should exit the loop
                    if result["type"] == "final_answer" or result["type"] == "error":
                        break

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Reset state at the end
        if 'memory' in locals():
            memory.reset()

if __name__ == "__main__":
    asyncio.run(main())