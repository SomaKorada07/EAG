# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from PIL import Image as PILImage
import math
import sys
import time
import os
import subprocess
import sympy
import numpy as np
from typing import List
from PIL import Image as PILImage, ImageDraw, ImageFont

# instantiate an MCP server client
mcp = FastMCP("Calculator")

# DEFINE TOOLS

#addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return int(a + b)

@mcp.tool()
def add_list(l: list) -> int:
    """Add all numbers in a list"""
    print("CALLED: add(l: list) -> int:")
    return sum(l)

# subtraction tool
@mcp.tool()
def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return int(a - b)

# multiplication tool
@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return int(a * b)

#  division tool
@mcp.tool() 
def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return float(a / b)

# power tool
@mcp.tool()
def power(a: int, b: int) -> int:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return int(a ** b)

# square root tool
@mcp.tool()
def sqrt(a: int) -> float:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return float(a ** 0.5)

# cube root tool
@mcp.tool()
def cbrt(a: int) -> float:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return float(a ** (1/3))

# factorial tool
@mcp.tool()
def factorial(a: int) -> int:
    """factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return int(math.factorial(a))

# log tool
@mcp.tool()
def log(a: int) -> float:
    """log of a number"""
    print("CALLED: log(a: int) -> float:")
    return float(math.log(a))

# remainder tool
@mcp.tool()
def remainder(a: int, b: int) -> int:
    """remainder of two numbers divison"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return int(a % b)

# sin tool
@mcp.tool()
def sin(a: int) -> float:
    """sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return float(math.sin(a))

# cos tool
@mcp.tool()
def cos(a: int) -> float:
    """cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return float(math.cos(a))

# tan tool
@mcp.tool()
def tan(a: int) -> float:
    """tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return float(math.tan(a))

# mine tool
@mcp.tool()
def mine(a: int, b: int) -> int:
    """special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return int(a - b - b)

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

@mcp.tool()
def strings_to_chars_to_int(string: str) -> list[int]:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return [int(ord(char)) for char in string]

@mcp.tool()
def int_list_to_exponential_sum(int_list: list) -> float:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return sum(math.exp(i) for i in int_list)

@mcp.tool()
def fibonacci_numbers(n: int) -> list:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    if n <= 0:
        return []
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return fib_sequence[:n]


# Global variables for drawing app
image = None
image_file = os.path.expanduser("~/Desktop/paint_canvas.png")
preview_process = None

@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle in the image from (x1,y1) to (x2,y2)"""
    global image, image_file, preview_process
    
    try:
        if image is None:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Canvas is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Create a drawing context
        draw = ImageDraw.Draw(image)
        
        # Draw a rectangle with a red outline and light yellow fill
        draw.rectangle([(x1, y1), (x2, y2)], outline="red", fill="lightyellow", width=5)
        
        # Save the updated image
        image.save(image_file)
        
        # Close Preview
        try:
            subprocess.run(["pkill", "-f", "Preview"], stderr=subprocess.DEVNULL)
            time.sleep(0.5)
        except:
            pass
        
        # Reopen Preview with the updated image
        preview_process = subprocess.Popen(["open", "-a", "Preview", image_file])
        
        # Wait for Preview to open
        time.sleep(1)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def add_text_in_paint(text: str, x1: int = None, y1: int = None, x2: int = None, y2: int = None) -> dict:
    """Add text to the image, optionally within a specified rectangle"""
    global image, image_file, preview_process
    
    try:
        if image is None:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Canvas is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Create a drawing context
        draw = ImageDraw.Draw(image)
        
        # Try to get a font (try several options that should be available on macOS)
        font = None
        font_size = 20
        
        for font_path in [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Times.ttc"
        ]:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        # Break text into multiple lines if needed
        max_width = 300 if all(param is not None for param in [x1, y1, x2, y2]) else 700
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            # Get the width of the text
            text_width = font.getlength(test_line) if hasattr(font, "getlength") else len(test_line) * (font_size // 2)
            
            if text_width <= max_width:
                current_line.append(word)
            else:
                if current_line:  # Add the current line if it's not empty
                    lines.append(" ".join(current_line))
                current_line = [word]  # Start a new line with the current word
        
        if current_line:  # Add the last line
            lines.append(" ".join(current_line))
        
        # If no lines were created, use the original text
        if not lines:
            lines = [text]
        
        # Calculate position for text
        if all(param is not None for param in [x1, y1, x2, y2]):
            # Center text in the rectangle
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
        else:
            # Center text in the canvas
            center_x = image.width // 2
            center_y = image.height // 2
        
        # Calculate total height of all lines
        line_height = font_size + 5  # Add spacing between lines
        total_height = len(lines) * line_height
        
        # Calculate starting y position to center text block
        start_y = center_y - (total_height // 2)
        
        # Draw each line of text
        for i, line in enumerate(lines):
            # Calculate position for this line
            y_position = start_y + (i * line_height)
            
            # Calculate width of this line to center it horizontally
            line_width = font.getlength(line) if hasattr(font, "getlength") else len(line) * (font_size // 2)
            x_position = center_x - (line_width // 2)
            
            # Draw the text
            draw.text((x_position, y_position), line, fill="black", font=font)
        
        # Save the updated image
        image.save(image_file)
        
        # Close Preview
        try:
            subprocess.run(["pkill", "-f", "Preview"], stderr=subprocess.DEVNULL)
            time.sleep(0.5)
        except:
            pass
        
        # Reopen Preview with the updated image
        preview_process = subprocess.Popen(["open", "-a", "Preview", image_file])
        
        # Wait for Preview to open
        time.sleep(1)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text added successfully within the specified area"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error adding text: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def open_paint() -> dict:
    """Create a blank canvas image and open it with Preview on macOS"""
    global image, image_file, preview_process
    
    try:
        # Close any existing Preview process
        if preview_process is not None:
            try:
                subprocess.run(["pkill", "-f", "Preview"], stderr=subprocess.DEVNULL)
                time.sleep(0.5)
            except:
                pass
        
        # Create a new blank canvas (1024x768 with white background)
        image = PILImage.new('RGB', (1024, 768), color='white')
        
        # Add a title to the canvas
        draw = ImageDraw.Draw(image)
        
        # Try to get a font
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
        except:
            font = ImageFont.load_default()
        
        # Add a title at the top
        draw.text((512, 30), "MacOS Paint Equivalent", fill="black", font=font, anchor="mm")
        
        # Save the image to disk
        image.save(image_file)
        
        # Open the image with Preview
        preview_process = subprocess.Popen(["open", "-a", "Preview", image_file])
        
        # Wait for Preview to open
        time.sleep(1)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Canvas created and opened with Preview at {image_file}"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error creating canvas: {str(e)}"
                )
            ]
        }


# Core reasoning tools
@mcp.tool()
def show_reasoning(steps: List[str]) -> str:
    """
    Display step-by-step reasoning process
    
    Parameters:
    - steps: List of reasoning steps as strings
    
    Returns:
    - Confirmation that reasoning steps are recorded
    """
    steps_formatted = "\n".join([f"Step {i+1}: {step}" for i, step in enumerate(steps)])
    return f"Reasoning steps recorded:\n{steps_formatted}"


# Calculation tools
@mcp.tool()
def calculate(expression: str) -> str:
    """
    Calculate the result of a mathematical expression
    
    Parameters:
    - expression: Mathematical expression as a string
    
    Returns:
    - The computed result
    """
    try:
        # Replace common mathematical symbols for evaluation
        prepared_expr = expression.replace("^", "**").replace("√", "math.sqrt")
        
        # For simple expressions, use eval with the math library
        result = eval(prepared_expr, {"math": math, "np": np, "sympy": sympy})
        
        return f"Result of {expression} = {result}"
    except Exception as e:
        return f"Error calculating {expression}: {str(e)}"


@mcp.tool()
def verify_ascii(character: str, expected_ascii: int) -> str:
    """
    Verify if a character has the expected ASCII value.
    
    Parameters:
    - character: The character to check (should be a single character)
    - expected_ascii: The expected ASCII value as an integer
    
    Returns:
    - Verification result as a string
    """
    if len(character) != 1:
        return f"Error: Expected a single character but got '{character}' (length: {len(character)})"
    
    actual_ascii = ord(character)
    is_correct = (actual_ascii == expected_ascii)
    
    if is_correct:
        return f"Verification passed: ASCII of '{character}' is {expected_ascii} ✓"
    else:
        return f"Verification failed: ASCII of '{character}' is {actual_ascii}, not {expected_ascii} ✗"


@mcp.tool()
def verify(expression: str, expected: float) -> str:
    """
    Verify if a calculation is correct
    
    Parameters:
    - expression: The expression to verify
    - expected: The expected result
    
    Returns:
    - Verification result
    """
    try:
        # Replace common mathematical symbols for evaluation
        prepared_expr = expression.replace("^", "**").replace("√", "math.sqrt")
        
        # Calculate the actual result
        actual = eval(prepared_expr, {"math": math, "np": np, "sympy": sympy})
        
        # Check if the results match (with some tolerance for floating point)
        is_correct = math.isclose(float(actual), float(expected), rel_tol=1e-10)
        
        if is_correct:
            return f"Verification passed: {expression} = {expected} ✓"
        else:
            return f"Verification failed: {expression} = {actual}, not {expected} ✗"
    except Exception as e:
        return f"Error during verification of {expression}: {str(e)}"


# Error handling tools
@mcp.tool()
def uncertainty_check(confidence: int, issue: str) -> str:
    """
    Report when the agent is uncertain about a step or approach
    
    Parameters:
    - confidence: Integer from 1-10 representing confidence level
    - issue: Description of the uncertainty
    
    Returns:
    - Acknowledgment of the uncertainty
    """
    if not (1 <= confidence <= 10):
        return "Confidence level must be between 1 and 10"
    
    uncertainty_record = {
        "confidence": confidence,
        "issue": issue,
        "timestamp": "current_step"
    }
    
    confidence_level = "Very Low" if confidence <= 2 else \
                      "Low" if confidence <= 4 else \
                      "Moderate" if confidence <= 6 else \
                      "High" if confidence <= 8 else "Very High"
    
    return f"Noted uncertainty: {issue} (Confidence: {confidence_level})"


@mcp.tool()
def correction(previous_step: str, corrected_step: str) -> str:
    """
    Correct a previous step that had an error
    
    Parameters:
    - previous_step: The incorrect step
    - corrected_step: The corrected version
    
    Returns:
    - Confirmation of the correction
    """
    
    return f"Correction applied:\nFrom: {previous_step}\nTo: {corrected_step}"

# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
