class Action:
    def __init__(self, session, tools, memory):
        self.session = session
        self.tools = tools
        self.memory = memory
        
    async def execute(self, action_data):
        """Execute an action based on the decision"""
        try:
            if action_data["type"] == "function_call":
                return await self.call_function(action_data["function"], action_data["parameters"])
            elif action_data["type"] == "final_answer":
                print("\n=== Agent Execution Complete ===")
                return {"type": "final_answer", "content": action_data["answer"]}
            elif action_data["type"] == "error":
                return {"type": "error", "content": action_data["message"]}
            else:
                return {"type": "unknown", "content": "Unrecognized action type"}
        except Exception as e:
            print(f"Error executing action: {e}")
            import traceback
            traceback.print_exc()
            return {"type": "error", "content": str(e)}
    
    async def call_function(self, func_name, params):
        """Call an MCP tool with the given function name and parameters"""
        print(f"\nDEBUG: Function name: {func_name}")
        print(f"DEBUG: Raw parameters: {params}")
        
        try:
            # Find the matching tool to get its input schema
            tool = next((t for t in self.tools if t.name == func_name), None)
            if not tool:
                print(f"DEBUG: Available tools: {[t.name for t in self.tools]}")
                raise ValueError(f"Unknown tool: {func_name}")

            print(f"DEBUG: Found tool: {tool.name}")
            print(f"DEBUG: Tool schema: {tool.inputSchema}")

            # Prepare arguments according to the tool's input schema
            arguments = {}
            schema_properties = tool.inputSchema.get('properties', {})
            print(f"DEBUG: Schema properties: {schema_properties}")

            for param_name, param_info in schema_properties.items():
                if not params:  # Check if we have enough parameters
                    raise ValueError(f"Not enough parameters provided for {func_name}")
                    
                value = params.pop(0)  # Get and remove the first parameter
                param_type = param_info.get('type', 'string')
                
                print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                
                # Convert the value to the correct type based on the schema
                if param_type == 'integer':
                    arguments[param_name] = int(value)
                elif param_type == 'number':
                    arguments[param_name] = float(value)
                else:
                    arguments[param_name] = str(value)

            print(f"DEBUG: Final arguments: {arguments}")
            print(f"DEBUG: Calling tool {func_name}")
            
            # Call the tool
            result = await self.session.call_tool(func_name, arguments=arguments)
            print(f"DEBUG: Raw result: {result}")
            
            # Process the result
            if hasattr(result, 'content'):
                print(f"DEBUG: Result has content attribute")
                # Handle multiple content items
                if isinstance(result.content, list):
                    iteration_result = [
                        item.text if hasattr(item, 'text') else str(item)
                        for item in result.content
                    ]
                else:
                    iteration_result = str(result.content)
            else:
                print(f"DEBUG: Result has no content attribute")
                iteration_result = str(result)
                
            print(f"DEBUG: Final iteration result: {iteration_result}")
            
            # Store the result in memory
            self.memory.store_iteration_result(func_name, arguments, iteration_result)
            self.memory.increment_iteration()
            
            return {"type": "function_result", "content": iteration_result}
            
        except Exception as e:
            print(f"DEBUG: Error details: {str(e)}")
            print(f"DEBUG: Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            return {"type": "error", "content": f"Error calling function {func_name}: {str(e)}"}