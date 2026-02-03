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