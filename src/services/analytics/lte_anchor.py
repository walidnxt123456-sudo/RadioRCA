from ..rca_utils import get_latest_clean_file
import pandas as pd

def analyze(ctx):
    pci = ctx.get('pci_lte')
    if pci is None:
        print("❌ No LTE PCI provided for lookup.")
        return

    file_path = get_latest_clean_file("cm", "cm_lte_cell")
    if file_path:
        df = pd.read_csv(file_path)
        # Match physicalLayerCellIdGroup * 3 + physicalLayerSubCellId == pci
        match = df[(df['physicalLayerCellIdGroup'] * 3 + df['physicalLayerSubCellId']) == pci]
        
        if not match.empty:
            cell_id = match.iloc[0]['EUtranCellFDDId']
            print(f"✅ Found LTE Anchor: {cell_id} (Node: {match.iloc[0]['NodeId']})")
            ctx['found_lte_name'] = cell_id
        else:
            print(f"❓ PCI {pci} not found in database.")