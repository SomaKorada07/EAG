import os
from dotenv import load_dotenv
from google import genai
import asyncio
from concurrent.futures import TimeoutError

class Perception:
    def __init__(self, api_key=None):
        if not api_key:
            load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        
    async def generate_with_timeout(self, prompt, timeout=10):
        """Generate content with a timeout"""
        print("Starting LLM generation...")
        try:
            # Convert the synchronous generate_content call to run in a thread
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
                    None, 
                    lambda: self.client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=prompt
                    )
                ),
                timeout=timeout
            )
            print("LLM generation completed")
            return response
        except TimeoutError:
            print("LLM generation timed out!")
            raise
        except Exception as e:
            print(f"Error in LLM generation: {e}")
            raise
            
    def parse_response(self, response_text):
        """Parse the LLM response text into a structured format"""
        response_text = response_text.strip()
        
        # Extract function call if present
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith("FUNCTION_CALL:"):
                response_text = line
                break
                
        if response_text.startswith("FUNCTION_CALL:"):
            _, function_info = response_text.split(":", 1)
            parts = [p.strip() for p in function_info.split("|")]
            func_name, params = parts[0], parts[1:]
            return {
                "type": "function_call",
                "function": func_name,
                "parameters": params
            }
        elif response_text.startswith("FINAL_ANSWER:"):
            _, answer = response_text.split(":", 1)
            return {
                "type": "final_answer",
                "answer": answer.strip()
            }
        else:
            return {
                "type": "unknown",
                "raw_response": response_text
            }