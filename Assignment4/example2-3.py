# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
import time
import subprocess
import os
from PIL import ImageDraw, ImageFont, Image as PILImage

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
canvas_image = None
canvas_file_path = "/tmp/drawing_canvas.png"
preview_process = None

@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle in the canvas from (x1,y1) to (x2,y2)"""
    global canvas_image, canvas_file_path
    try:
        if canvas_image is None:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Canvas is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Create a drawing context
        draw = ImageDraw.Draw(canvas_image)
        
        # Draw rectangle with outline (make it thicker and use a more visible color)
        draw.rectangle([(x1, y1), (x2, y2)], outline="red", width=5)
        
        # Also fill with a light color to make it more visible
        draw.rectangle([(x1+5, y1+5), (x2-5, y2-5)], fill="lightyellow")
        
        # Save the image (just update the file without closing Preview)
        canvas_image.save(canvas_file_path)
        
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
    """Add text to the canvas, optionally within a specified rectangle"""
    global canvas_image, canvas_file_path
    try:
        if canvas_image is None:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Canvas is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Create a drawing context
        draw = ImageDraw.Draw(canvas_image)
        
        # Try to load a font - try several system fonts that should be available on macOS
        font = None
        font_size = 26  # Larger font for better visibility
        
        for font_path in [
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
        ]:
            try:
                font = ImageFont.truetype(font_path, font_size)
                break
            except:
                continue
        
        if font is None:
            font = ImageFont.load_default()
        
        # If the text is too long, break it into multiple lines
        max_width = 400  # Maximum width for text in pixels
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = " ".join(current_line + [word])
            test_width = font.getlength(test_line) if hasattr(font, "getlength") else len(test_line) * (font_size / 2)
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(" ".join(current_line))
        
        # If no lines were created (e.g., for very long words), use the original text
        if not lines:
            lines = [text]
        
        # Calculate text dimensions
        line_height = font_size + 5  # Add some padding between lines
        text_height = len(lines) * line_height
        text_width = max([font.getlength(line) if hasattr(font, "getlength") else len(line) * (font_size / 2) for line in lines])
        
        # If rectangle coordinates are provided, center text within that rectangle
        if all(param is not None for param in [x1, y1, x2, y2]):
            rect_width = x2 - x1
            rect_height = y2 - y1
            
            # Center text in the rectangle
            start_x = x1 + (rect_width - text_width) / 2
            start_y = y1 + (rect_height - text_height) / 2
        else:
            # Center text in the entire canvas
            width, height = canvas_image.size
            start_x = (width - text_width) / 2
            start_y = (height - text_height) / 2
        
        # Draw each line of text
        for i, line in enumerate(lines):
            y_position = start_y + i * line_height
            draw.text((start_x, y_position), line, fill="black", font=font)
        
        # Save the image
        canvas_image.save(canvas_file_path)
        
        # Refresh Preview by closing and reopening it
        try:
            subprocess.run(["killall", "Preview"], stderr=subprocess.DEVNULL)
            time.sleep(0.5)
        except:
            pass
        
        # Reopen the file with Preview
        subprocess.Popen(["open", "-a", "Preview", canvas_file_path])
        time.sleep(1)  # Wait for Preview to open
        
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
                    text=f"Error adding text: {str(e)}\n{type(e)}"
                )
            ]
        }

@mcp.tool()
async def open_paint() -> dict:
    """Create a new canvas and open it with Preview on macOS"""
    global canvas_image, canvas_file_path, preview_process
    try:
        # Create user's Desktop folder path for better visibility
        desktop_path = os.path.expanduser("~/Desktop")
        canvas_file_path = os.path.join(desktop_path, "drawing_canvas.png")
        
        # Create a new blank white canvas (1024x768 pixels)
        canvas_image = PILImage.new('RGB', (1024, 768), color='white')
        
        # Save the canvas to the file
        canvas_image.save(canvas_file_path)
        
        # Make sure Preview is closed first (if it's already open)
        try:
            subprocess.run(["killall", "Preview"], stderr=subprocess.DEVNULL)
            time.sleep(0.5)
        except:
            pass
        
        # Open the file with Preview app
        preview_process = subprocess.Popen(["open", "-a", "Preview", canvas_file_path])
        time.sleep(1)  # Wait for Preview to fully open
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Canvas created and opened with Preview at {canvas_file_path}"
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
