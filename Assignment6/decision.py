class Decision:
    def __init__(self, perception, memory):
        self.perception = perception
        self.memory = memory
        
    async def decide_next_action(self, system_prompt, user_query):
        """Decide on the next action to take"""
        # Construct the prompt with system instructions and query
        current_query = self.memory.get_history_for_prompt(user_query)
        prompt = f"{system_prompt}\n\nQuery: {current_query}"
        
        try:
            # Generate response from the model
            response = await self.perception.generate_with_timeout(prompt)
            response_text = response.text.strip()
            print(f"LLM Response: {response_text}")
            
            # Parse the response to determine the action
            action_data = self.perception.parse_response(response_text)
            
            return action_data
            
        except Exception as e:
            print(f"Failed to decide next action: {e}")
            return {"type": "error", "message": str(e)}