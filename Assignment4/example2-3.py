# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
import time
import os
import tkinter as tk
from tkinter import font as tkfont
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
paint_window = None
canvas = None
root = None
output_file = os.path.expanduser("~/Desktop/paint_output.html")

@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle in the HTML canvas from (x1,y1) to (x2,y2)"""
    global output_file
    try:
        # Read the current HTML file
        with open(output_file, "r") as f:
            html_content = f.read()
        
        # Create a rectangle element
        rectangle_style = f"""
            position: absolute;
            left: {x1}px;
            top: {y1}px;
            width: {x2-x1}px;
            height: {y2-y1}px;
            border: 3px solid red;
            background-color: lightyellow;
        """
        
        rectangle_html = f'<div id="rectangle" style="{rectangle_style}"></div>'
        
        # Insert the rectangle before the closing div tag
        html_content = html_content.replace('</div>', f'{rectangle_html}</div>')
        
        # Write the updated HTML
        with open(output_file, "w") as f:
            f.write(html_content)
        
        # The browser will automatically refresh the file
        
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
    """Add text to the HTML canvas, optionally within a specified rectangle"""
    global output_file
    try:
        # Read the current HTML file
        with open(output_file, "r") as f:
            html_content = f.read()
        
        # Calculate text position
        if all(param is not None for param in [x1, y1, x2, y2]):
            # Position text in the center of the rectangle
            left = x1 + ((x2 - x1) / 2)
            top = y1 + ((y2 - y1) / 2)
            width = x2 - x1 - 20  # Allow some padding
        else:
            # Position text in the center of the canvas
            left = 500  # Half of canvas width
            top = 350   # Half of canvas height
            width = 800  # Default width
        
        # Create a text element
        text_style = f"""
            position: absolute;
            left: {left - width/2}px;
            top: {top - 20}px;
            width: {width}px;
            text-align: center;
            font-family: Arial, sans-serif;
            font-size: 18px;
            color: black;
            word-wrap: break-word;
        """
        
        # Escape any HTML in the text
        safe_text = text.replace('<', '&lt;').replace('>', '&gt;')
        
        text_html = f'<div id="text" style="{text_style}">{safe_text}</div>'
        
        # Insert the text before the closing div tag
        html_content = html_content.replace('</div>', f'{text_html}</div>')
        
        # Write the updated HTML
        with open(output_file, "w") as f:
            f.write(html_content)
        
        # Trigger a refresh of the browser by adding a small script
        refresh_script = """
        <script>
        // This script forces a refresh of the page
        setTimeout(function() { 
            document.location.reload(true); 
        }, 100);
        </script>
        """
        
        # Add the script to force a refresh
        html_content = html_content.replace('</body>', f'{refresh_script}</body>')
        
        with open(output_file, "w") as f:
            f.write(html_content)
        
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
    """Create a new HTML-based canvas for drawing"""
    global output_file
    try:
        # Create a simple HTML file with a canvas-like area
        html_content = """<!DOCTYPE html>
<html>
<head>
    <title>MacOS Paint Equivalent</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
        }
        .canvas-container {
            width: 1000px;
            height: 700px;
            margin: 0 auto;
            background-color: white;
            border: 1px solid #ccc;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
            position: relative;
            overflow: hidden;
        }
        h1 {
            text-align: center;
            color: #333;
        }
    </style>
</head>
<body>
    <h1>MacOS Paint Equivalent</h1>
    <div class="canvas-container" id="canvas">
        <!-- Elements will be added here -->
    </div>
</body>
</html>
"""
        
        # Write the HTML file
        with open(output_file, "w") as f:
            f.write(html_content)
        
        # Open the file in the default browser
        import subprocess
        subprocess.Popen(["open", output_file])
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Paint equivalent opened at {output_file}"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error creating paint equivalent: {str(e)}"
                )
            ]
        }
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
