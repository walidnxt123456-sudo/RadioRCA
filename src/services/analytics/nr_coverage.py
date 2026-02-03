from ..rca_utils import get_latest_clean_file
import pandas as pd

def analyze(ctx):
    # 1. Performance Check
    rsrp = ctx.get('rsrp_nr')
    if rsrp:
        if rsrp < -115: print("❌ NR Coverage is CRITICAL.")
        elif rsrp < -105: print("⚠️ NR Coverage is WEAK.")
    
    # 2. Configuration Lookup
    pci = ctx.get('pci_nr')
    if pci:
        file_path = get_latest_clean_file("cm", "cm_nr_cell")
        if file_path:
            df = pd.read_csv(file_path)
            match = df[df['nRPCI'] == pci]
            if not match.empty:
                cell_name = match.iloc[0]['NRCellDUId']
                print(f"✅ Found NR Cell: {cell_name} on Node {match.iloc[0]['NodeId']}")
                ctx['found_nr_name'] = cell_name