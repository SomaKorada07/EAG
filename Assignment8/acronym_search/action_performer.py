import json
from ast import literal_eval

# Import our centralized logger
from log_config import get_logger

# Get a logger for this module
logger = get_logger(__name__)

async def execute_tool(session, tool, func_name, params):
    logger.info(f"params are: {params}")
    arguments = {}
    schema = tool.inputSchema.get('properties', {})
    
    for param_name, info in schema.items():
        logger.info(f"param_name: {param_name}, info: {info}")
        if not params:
            raise ValueError(f"Not enough parameters for {func_name}")
        logger.info(f"param type: {type(params)} value: {params}")
        value = params.pop(0)
        ptype = info.get('type', 'string')
        logger.info(f"ptype: {ptype}, value type: {type(value)} value: {value}")
        if ptype == 'integer':
            arguments[param_name] = int(value)
        elif ptype == 'number':
            arguments[param_name] = float(value)
        elif ptype == 'string':
            if isinstance(params, list) and len(params) > 0:
                # Create a complete list of items including the first value
                all_items = [value] + params
                # Remove duplicates while preserving order
                unique_items = []
                for item in all_items:
                    if item not in unique_items:
                        unique_items.append(item)
                # Format the list as bullet points
                bullet_points = "\n".join([f"• {item}" for item in unique_items])
                arguments[param_name] = bullet_points
            else:
                arguments[param_name] = value
            logger.info(f"string value: {arguments[param_name]}")
        elif ptype == 'object':
            arguments[param_name] = params
        elif ptype == 'array':
            arguments[param_name] = [int(v.strip()) for v in value.strip('[]').split(',')]
        else:
            arguments[param_name] = str(value)

    logger.info(f"Sending argument: {arguments}")
    result = await session.call_tool(func_name, arguments=arguments)
    
    try:
        return arguments, literal_eval(json.loads(json.dumps(result.content[0].text)))
    except Exception as e:
        return arguments, result.content[0].text