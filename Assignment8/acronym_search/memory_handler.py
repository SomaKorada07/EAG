import json
from pathlib import Path
import os
from log_config import get_logger

logger = get_logger(__name__)
STATE_FILE = Path("state.json")

def clear_state():
    if STATE_FILE.exists():
        try:
            os.remove(STATE_FILE)
            logger.info(f"State file {STATE_FILE} has been removed.")
        except Exception as e:
            logger.error(f"Error removing state file: {e}")
        
def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"iterations": []}

def save_state(state: dict):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def add_iteration(response):
    state = load_state()
    current_step = len(state["iterations"]) + 1

    iteration = {
        "iteration": current_step,
        "response": response
    }

    state["iterations"].append(iteration)
    save_state(state)
    return state