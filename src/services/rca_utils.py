import json
import pandas as pd
from pathlib import Path

def get_latest_clean_file(folder_name, pattern):
    """Finds the most recent 'clean' CSV in the specified archive folder."""
    # This matches the folder structure used in your main.py process_files logic
    path = Path(f"data/input/{folder_name}/archive")
    if not path.exists():
        return None
    
    # Sort by filename (timestamp) to get the newest clean file
    files = sorted(path.glob(f"clean_*{pattern}*.csv"), reverse=True)
    return files[0] if files else None
    
# Define the path for the history file
HISTORY_FILE = Path("data/rca_history.json")
def save_history(history):
    """Saves the last 10 contexts to a local JSON file."""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4)
    except Exception as e:
        print(f"⚠️ Warning: Could not save history - {e}")

def load_history():
    """Loads history from the local JSON file if it exists."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            # If file is corrupted or empty, return empty list
            return []
    return []