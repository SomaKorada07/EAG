class Memory:
    def __init__(self):
        self.last_response = None
        self.iteration = 0
        self.iteration_responses = []
        self.conversation_history = []
        
    def reset(self):
        """Reset all state variables to their initial state"""
        self.last_response = None
        self.iteration = 0
        self.iteration_responses = []
        self.conversation_history = []
        
    def store_iteration_result(self, func_name, arguments, result):
        """Store the result of a function call"""
        if isinstance(result, list):
            result_str = f"[{', '.join(result)}]"
        else:
            result_str = str(result)
            
        self.iteration_responses.append(
            f"In the {self.iteration + 1} iteration you called {func_name} with {arguments} parameters, "
            f"and the function returned {result_str}."
        )
        self.last_response = result
        
    def get_history_for_prompt(self, query):
        """Get the conversation history formatted for prompting"""
        if self.last_response is None:
            return query
        else:
            # Append iteration responses to the query
            return query + "\n\n" + " ".join(self.iteration_responses) + "  What should I do next?"
            
    def increment_iteration(self):
        """Increment the iteration counter"""
        self.iteration += 1
        
    def get_iteration(self):
        """Get current iteration"""
        return self.iteration