import shutil
import sys
from datetime import datetime
from pathlib import Path
from infrastructure.csv_reader import CsvReader
from interfaces.fwa_cli import get_fwa_input
from services.rca_engine import execute_selected_rca  # Import the new engine

def process_files(reader, folder_path, prefix, read_func):
    """Processes files: Archives the original RAW and saves a CLEAN copy."""
    for file_path in folder_path.glob(f"{prefix}*.csv"):
        print(f"\n>>> Processing {prefix.upper()}: {file_path.name}")
        
        # 1. Read and Clean the data into memory
        df = read_func(file_path)
        
        if df is None or df.empty:
            print(f"⚠️  Skipping {file_path.name}: No data or read error.")
            continue

        # 2. Setup Archive Directory
        archive_dir = folder_path / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 3. SAVE THE CLEAN VERSION
        clean_filename = f"clean_{timestamp}_{file_path.name}"
        clean_path = archive_dir / clean_filename
        df.to_csv(clean_path, index=False, sep=',', decimal='.')
        print(f"Clean version saved: {clean_path.name}")

        # 4. MOVE THE ORIGINAL RAW FILE
        # We use shutil.move so the 'input' folder stays empty
        raw_filename = f"raw_{timestamp}_{file_path.name}"
        raw_path = archive_dir / raw_filename
        shutil.move(str(file_path), str(raw_path))
        print(f"Original RAW archived: {raw_path.name}")


def run_fwa_analysis(context):
    """
    Evaluates available context and stays in a loop to allow 
    multiple sequential RCA checks.
    """
    while True:
        print("\n" + "="*40)
        print("      FWA RCA DIAGNOSTIC ENGINE")
        print("="*40)
        
        # 1. Determine available paths
        available_rcas = []
        if context.get('latitude') and context.get('longitude'):
            available_rcas.append(("GEO_DIST", "Geospatial Distance to Nearest Site"))
        if context.get('pci_lte') is not None:
            available_rcas.append(("LTE_COV", "4G Anchor Stability & Cell Lookup"))
        if context.get('pci_nr') is not None:
            available_rcas.append(("NR_COV", "5G Coverage & Configuration Check"))
        if context.get('pci_lte') is not None and context.get('pci_nr') is not None:
            available_rcas.append(("ENDC_FAIL", "EN-DC Relation & Neighbor Analysis"))
        
        available_rcas.append(("GEN_INT", "General Interference / SNR Analysis"))

        # 2. Present the Menu
        print("\nAvailable Analyses:")
        for i, (code, description) in enumerate(available_rcas, 1):
            print(f"{i}. [{code}] - {description}")
        
        print(f"{len(available_rcas) + 1}. [BACK] - Return to Main Menu")
        
        choice = input("\nSelect an option: ").strip()

        # Handle "Back" option
        if choice == str(len(available_rcas) + 1) or choice.lower() == 'b':
            print("Exiting diagnostic engine...")
            break
        
        # Handle RCA Selection
        if choice.isdigit() and int(choice) <= len(available_rcas):
            selected_code = available_rcas[int(choice)-1][0]
            # Execute the routed RCA logic
            execute_selected_rca(selected_code, context)
            
            # Pause so the user can read the output before the menu redraws
            input("\nPress Enter to continue...")
        else:
            print("❌ Invalid selection. Try again.")       


def show_history_menu(history, current_active):
    if not history:
        print("\n📜 History is empty.")
        return current_active

    print("\n--- RECENT HISTORY (Last 10) ---")
    for i, ctx in enumerate(history, 1):
        # Display a short summary for each history item
        summary = f"Lat: {ctx['latitude']}, Lon: {ctx['longitude']}, PCI: {ctx['pci_lte']}"
        print(f"{i}. {summary}")

    print(f"{len(history) + 1}. [BACK]")
    
    choice = input("\nSelect a configuration to LOAD: ").strip()
    
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(history):
            print(f"✅ Loaded context from history index {choice}.")
            return history[idx].copy()
            
    return current_active
    

def main():
    # Store the last 10 contexts in a list
    history = []
    # This is the "active" context we are working on right now
    current_ctx = {
        "longitude": None, "latitude": None, "pci_lte": None, "pci_nr": None,
        "rsrp_lte": None, "rsrq_lte": None, "rsrp_nr": None, "rsrq_nr": None,
        "snr_nr": None, "snr_lte": None
    }

    while True:    
        print("\n" + "="*40)
        print("   RadioRCA - FWA Diagnostic Tool")
        print("="*40)
        
        # Show a summary of the current data loaded
        lat = current_ctx.get('latitude') or "---"
        lon = current_ctx.get('longitude') or "---"
        pci = current_ctx.get('pci_lte') or "---"
        print(f"STATUS: Active Data [Lat: {lat}, Lon: {lon}, PCI: {pci}]")
        print("-" * 40)
        print("1. Process & Clean Network Files")
        print("2. Edit / Load New Data")
        print("3. Show History (Last 10)")
        print("4. Run RCA Engine")
        print("5. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "1":
            # ... existing process_files code ...
            pass
            
        elif choice == "2":
            # Save the current state to history before editing if it's not empty
            if any(v is not None for v in current_ctx.values()):
                # Insert at the beginning, keep only last 10
                history.insert(0, current_ctx.copy())
                history = history[:10]
            
            # Now edit the current context
            current_ctx = get_fwa_input(current_ctx)
            
        elif choice == "3":
            current_ctx = show_history_menu(history, current_ctx)
            
        elif choice == "4":
            if any(v is not None for v in current_ctx.values()):
                run_fwa_analysis(current_ctx)
            else:
                print("❌ No data loaded. Please use Option 2 first.")
                
        elif choice == "5" or choice.lower() == 'q':
            sys.exit()

if __name__ == "__main__":
    main()