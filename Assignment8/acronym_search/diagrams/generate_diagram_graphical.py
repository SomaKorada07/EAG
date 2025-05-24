#!/usr/bin/env python3
"""
Generate a graphical architecture diagram using matplotlib.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def create_diagram():
    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Remove axis ticks
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Set title
    ax.set_title('Agentic AI System Architecture', fontsize=16)
    
    # Components
    components = {
        'slack': {'name': 'Slack Users', 'pos': (0.5, 0.9), 'color': 'lightblue'},
        'sse_client': {'name': 'SSE Client', 'pos': (0.5, 0.7), 'color': 'skyblue'},
        'sse_server': {'name': 'MCP SSE Server', 'pos': (0.2, 0.5), 'color': 'lightgreen'},
        'llm': {'name': 'LLM Perception', 'pos': (0.8, 0.5), 'color': 'lightyellow'},
        'decision': {'name': 'Decision Maker', 'pos': (0.5, 0.5), 'color': 'lightcoral'},
        'action': {'name': 'Action Performer', 'pos': (0.8, 0.3), 'color': 'peachpuff'},
        'apis': {'name': 'External APIs', 'pos': (0.2, 0.3), 'color': 'lightgreen'},
        'memory': {'name': 'Memory Handler', 'pos': (0.5, 0.3), 'color': 'thistle'},
        'logging': {'name': 'Logging System', 'pos': (0.8, 0.1), 'color': 'lightgrey'}
    }
    
    # Draw boxes
    for name, comp in components.items():
        rect = patches.FancyBboxPatch(
            (comp['pos'][0] - 0.1, comp['pos'][1] - 0.05),
            0.2, 0.1,
            boxstyle=patches.BoxStyle("Round", pad=0.02),
            facecolor=comp['color'],
            edgecolor='black'
        )
        ax.add_patch(rect)
        ax.text(comp['pos'][0], comp['pos'][1], comp['name'], 
                ha='center', va='center', fontsize=10)
    
    # Draw arrows
    arrows = [
        ('slack', 'sse_client'),
        ('sse_client', 'llm'),
        ('sse_client', 'decision'),
        ('sse_client', 'sse_server'),
        ('llm', 'action'),
        ('decision', 'memory'),
        ('action', 'decision'),
        ('sse_server', 'apis'),
        ('memory', 'decision')
    ]
    
    for start, end in arrows:
        start_pos = components[start]['pos']
        end_pos = components[end]['pos']
        
        # Calculate arrow positions
        if start_pos[1] > end_pos[1]:  # Arrow going down
            start_y = start_pos[1] - 0.05
            end_y = end_pos[1] + 0.05
        elif start_pos[1] < end_pos[1]:  # Arrow going up
            start_y = start_pos[1] + 0.05
            end_y = end_pos[1] - 0.05
        else:  # Arrow horizontal
            start_y = start_pos[1]
            end_y = end_pos[1]
            
        if start_pos[0] > end_pos[0]:  # Arrow going left
            start_x = start_pos[0] - 0.1
            end_x = end_pos[0] + 0.1
        elif start_pos[0] < end_pos[0]:  # Arrow going right
            start_x = start_pos[0] + 0.1
            end_x = end_pos[0] - 0.1
        else:  # Arrow vertical
            start_x = start_pos[0]
            end_x = end_pos[0]
            
        ax.annotate("", 
                   xy=(end_x, end_y), 
                   xytext=(start_x, start_y),
                   arrowprops=dict(arrowstyle="->", lw=1.5, color="black"))
    
    # Add legend for data flow
    textstr = '''Data Flow:
1. User sends message to Slack Bot
2. SSE Client processes message
3. LLM generates decision
4. Decision Maker determines next action
5. Action Performer executes tool
6. Memory Handler maintains state
7. Logging System records activities'''
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    ax.text(0.05, 0.05, textstr, transform=ax.transAxes, fontsize=10,
            verticalalignment='bottom', bbox=props)
    
    # Set limits
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    
    # Add border
    for spine in ax.spines.values():
        spine.set_visible(True)
    
    # Save figure
    plt.tight_layout()
    plt.savefig("/Users/sokorada/Documents/AgenticAI_Learning/test_uv/test_proj/diagrams/architecture_diagram.png", dpi=300)
    print("Graphical diagram saved as diagrams/architecture_diagram.png")

if __name__ == "__main__":
    create_diagram()
