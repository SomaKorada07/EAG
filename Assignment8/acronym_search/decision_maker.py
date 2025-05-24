from prompt import prefix_prompt, main_prompt
from memory_handler import load_state
from log_config import get_logger

# Get a logger for this module
logger = get_logger(__name__)

def create_tool_descriptions(tools):
    descriptions = []
    for i, tool in enumerate(tools):
        try:
            name = getattr(tool, 'name', f'tool_{i}')
            desc = getattr(tool, 'description', 'No description available')
            props = tool.inputSchema.get('properties', {})
            param_details = [f"{p}: {info.get('type', 'unknown')}" for p, info in props.items()]
            params_str = ', '.join(param_details) if param_details else 'no parameters'
            descriptions.append(f"{i+1}. {name}({params_str}) - {desc}")
        except Exception as e:
            descriptions.append(f"{i+1}. Error processing tool")
    return "\n".join(descriptions)

def construct_prompt(tools_desc: str, original_query: str) -> str:
    context = f"{prefix_prompt}: {tools_desc} \
                {main_prompt}"
    history = load_state()
    return f"Context: {context} \
             User Query: {original_query} \
             Decision History which has been taken for this task: {history}\
             The response from previous tool is present under 'result' which needs to be used for next iteration. \
             Now what should I do next? "