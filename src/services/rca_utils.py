import json
import pandas as pd
from pathlib import Path

def map_cell_to_sector_id(cell_name):
    """
    Translates the last character of a Cell Name to an Ericsson Sector ID.
    Example: PLO125X -> S1, PLO125P -> S2, PLO125Q -> S3
    """
    last_char = str(cell_name)[-1].upper()
    
    mapping = {
        'X': 'S1', 'O': 'S1', 'A': 'S1',
        'Y': 'S2', 'P': 'S2', 'B': 'S2',
        'Z': 'S3', 'Q': 'S3', 'C': 'S3'
    }
    
    return mapping.get(last_char, None)

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
    
def fetch_cm_parameter(cell_name, site_id, parameter_keyword):
    """
    Advanced Parameter Lookup Engine.
    1. Finds the latest CM file.
    2. Maps Site/Cell anchors using aliases.
    3. Returns the parameter value if found.
    """
    cm_path = get_latest_clean_file("cm", "cm_")
    if not cm_path:
        return None

    try:
        # We use a smaller chunk or low_memory to handle large CM files
        df = pd.read_csv(cm_path, low_memory=False)
        df.columns = df.columns.str.strip().str.lower()
        
        # Define Aliases based on your requirements
        cell_aliases = ['eutrancellid', 'cellname', 'cell id', 'localcellid']
        site_aliases = ['node id', 'erbs id', 'site', 'siteid']
        
        # Identify columns present in THIS specific file
        cell_col = next((c for c in df.columns if any(a in c for a in cell_aliases)), None)
        site_col = next((c for c in df.columns if any(a in c for a in site_aliases)), None)
        param_col = next((c for c in df.columns if parameter_keyword.lower() in c), None)

        if not param_col:
            return None

        # Logic: Try Cell-level match first, then Site-level
        result = None
        if cell_col and cell_name:
            # Fuzzy match or exact match logic can be applied here
            match = df[df[cell_col].astype(str).str.contains(str(cell_name), na=False)]
            if not match.empty:
                result = match[param_col].iloc[0]

        if result is None and site_col and site_id:
            match = df[df[site_col].astype(str).str.contains(str(site_id), na=False)]
            if not match.empty:
                result = match[param_col].iloc[0]

        return result
    except Exception as e:
        print(f"⚠️ CM Lookup Error: {e}")
        return None

def fetch_ericsson_e_tilt_group(site_id, cell_name):
    """
    Fetches Tilt using AntennaUnitGroupId (Sector) and AntennaNearUnitId (Band).
    """
    from .rca_utils import get_latest_clean_file
    import pandas as pd

    # --- 1. Internal Logic: Map last char to Sector Group and Band Keyword ---
    last_char = str(cell_name)[-1].upper()
    
    # Sector Mapping (AntennaUnitGroupId)
    sector_map = {
        'X': 1, 'O': 1, 'L': 1, 'A': 1,
        'Y': 2, 'P': 2, 'M': 2, 'B': 2,
        'Z': 3, 'Q': 3, 'N': 3, 'C': 3
    }
    # Band Mapping (AntennaNearUnitId keyword)
    band_map = {
        'X': 'L2100', 'Y': 'L2100', 'Z': 'L2100',
        'L': 'L1800', 'M': 'L1800', 'N': 'L1800',
        'O': 'L800',  'P': 'L800',  'Q': 'L800'
    }

    target_sector = sector_map.get(last_char)
    target_band = band_map.get(last_char)

    if not target_sector or not target_band:
        return None

    cm_path = get_latest_clean_file("cm", "cm_")
    if not cm_path: return None

    try:
        df = pd.read_csv(cm_path, sep=None, engine='python')
        df.columns = df.columns.str.strip()
        
        # --- 2. Multi-Step Filtering ---
        # Filter by NodeId (Site)
        site_mask = df['NodeId'].astype(str).str.contains(str(site_id), na=False)
        site_data = df[site_mask]
        
        if not site_data.empty:
            # Match Sector Group AND Band Identifier
            match = site_data[
                (site_data['AntennaUnitGroupId'].astype(float) == float(target_sector)) & 
                (site_data['AntennaNearUnitId'].str.contains(target_band, na=False))
            ]
            
            if not match.empty:
                row = match.iloc[0]
                return {
                    'e_tilt': float(row.get('electricalAntennaTilt', 0)) / 10,
                    #'max_tilt': float(row.get('maxTilt', 0)) / 10,
                    #'min_tilt': float(row.get('minTilt', 0)) / 10,
                    'band_id': row.get('AntennaNearUnitId')
                }
    except Exception as e:
        print(f"⚠️ Precise e_tilt_group CM Fetch Error: {e}")
    
    return None