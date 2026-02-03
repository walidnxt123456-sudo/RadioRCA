import shutil
import sys
from datetime import datetime
from pathlib import Path

# Infrastructure & Interfaces
from infrastructure.csv_reader import CsvReader
from interfaces.fwa_cli import get_fwa_input
from services.rca_engine import execute_selected_rca
from services.rca_utils import save_history, load_history

def process_files(reader, folder_path, prefix, read_func):
    """Processes all files matching the prefix: Archives RAW and saves a CLEAN copy."""
    # Look for multiple extensions
    extensions = ['*.csv', '*.xlsx', '*.xls']
    # FIX: Convert glob to a list so moving files doesn't break the loop
    files_to_process = []
    
    for ext in extensions:
        files_to_process.extend(list(folder_path.glob(f"{prefix}{ext}")))
        
    if not files_to_process:
        return

    for file_path in files_to_process:
        print(f"\n>>> Processing {prefix.upper()}: {file_path.name}")
        
        # 1. Read and Clean data
        df = read_func(file_path)
        
        if df is None or df.empty:
            print(f"⚠️  Skipping {file_path.name}: No data or read error.")
            continue

        # 2. Setup Archive Directory
        archive_dir = folder_path / "archive"
        archive_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 3. Standardize the output: always save the CLEAN version as a CSV
        clean_filename = f"clean_{timestamp}_{file_path.name}.csv"
        clean_path = archive_dir / clean_filename
        df.to_csv(clean_path, index=False, sep=',', decimal='.')
        print(f"Clean version saved: {clean_path.name}")

        # 4. MOVE ORIGINAL RAW (using shutil.move) Archive the original raw file (regardless of whether it was csv or xlsx)
        raw_filename = f"raw_{timestamp}_{file_path.name}"
        raw_path = archive_dir / raw_filename
        shutil.move(str(file_path), str(raw_path))
        print(f"Original RAW archived: {raw_path.name}")

def run_fwa_analysis(context):
    """Sub-menu for RCA checks."""
    while True:
        print("\n" + "="*40)
        print("      FWA RCA DIAGNOSTIC ENGINE")
        print("="*40)
        
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

        print("\nAvailable Analyses:")
        for i, (code, description) in enumerate(available_rcas, 1):
            print(f"{i}. [{code}] - {description}")
        
        back_opt = len(available_rcas) + 1
        print(f"{back_opt}. [BACK] - Return to Main Menu")
        
        choice = input("\nSelect an option: ").strip()

        if choice == str(back_opt) or choice.lower() == 'b':
            break
        
        if choice.isdigit() and int(choice) <= len(available_rcas):
            selected_code = available_rcas[int(choice)-1][0]
            execute_selected_rca(selected_code, context)
            input("\nPress Enter to continue...")
        else:
            print("❌ Invalid selection.")       

def show_history_menu(history, current_active):
    """Displays and loads from history."""
    if not history:
        print("\n📜 History is empty.")
        return current_active

    print("\n--- RECENT HISTORY (Last 10) ---")
    for i, ctx in enumerate(history, 1):
        summary = f"Lat: {ctx.get('latitude', 'N/A')}, Lon: {ctx.get('longitude', 'N/A')}, PCI: {ctx.get('pci_lte', 'N/A')}"
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
    history = load_history()
    current_ctx = {
        "longitude": None, "latitude": None, "pci_lte": None, "pci_nr": None,
        "rsrp_lte": None, "rsrq_lte": None, "rsrp_nr": None, "rsrq_nr": None,
        "snr_nr": None, "snr_lte": None
    }

    while True:    
        print("\n" + "="*40)
        print("   RadioRCA - FWA Diagnostic Tool")
        print("="*40)
        
        lat = current_ctx.get('latitude') or "---"
        lon = current_ctx.get('longitude') or "---"
        print(f"STATUS: Active Data [Lat: {lat}, Lon: {lon}]")
        print("-" * 40)
        print("1. Process & Clean Network Files")
        print("2. Edit / Load New Data")
        print("3. Show History (Last 10)")
        print("4. Run RCA Engine")
        print("5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            base_input = Path("data/input")
            reader = CsvReader()
            tasks = [
                (base_input / "pm", "pm_", reader.read_pm_data),
                (base_input / "cm", "cm_", reader.read_cm_data),
                (base_input / "database", "database_", reader.read_design_data),
                (base_input / "rf", "rf_", reader.read_rf_data),
            ]
            for folder, prefix, func in tasks:
                if folder.exists():
                    process_files(reader, folder, prefix, func)
                else:
                    folder.mkdir(parents=True, exist_ok=True)
            print("\n✅ Processing complete.")
            
        elif choice == "2":
            if any(v is not None for v in current_ctx.values()):
                history.insert(0, current_ctx.copy())
                history = history[:10]
                save_history(history)
            current_ctx = get_fwa_input(current_ctx)
            
        elif choice == "3":
            current_ctx = show_history_menu(history, current_ctx)
            
        elif choice == "4":
            if any(v is not None for v in current_ctx.values()):
                run_fwa_analysis(current_ctx)
            else:
                print("❌ No data loaded. Please use Option 2 first.")
                
        elif choice == "5" or choice.lower() in ['q', 'exit']:
            save_history(history)
            sys.exit()

if __name__ == "__main__":
    main()