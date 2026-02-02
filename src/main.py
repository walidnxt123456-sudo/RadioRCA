import shutil
from datetime import datetime
from pathlib import Path
from infrastructure.csv_reader import CsvReader

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

def main():
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
            (folder / "archive").mkdir(exist_ok=True)

if __name__ == "__main__":
    main()