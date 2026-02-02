import pandas as pd
import csv
from pathlib import Path

class CsvReader:
    def _find_start_params(self, file_path: Path, keywords: list):
        """
        Enhanced detection: explicitly handles the UTF-16 BOM and 
        sniffs for headers using multiple encodings.
        """
        # Try UTF-16 first if you suspect many 5G/NR files, 
        # or stick to this order which is safest for Telecom data.
        for enc in ['utf-16', 'utf-8', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    # Read a small chunk to check if it's readable
                    first_chunk = f.read(1024)
                    if not first_chunk:
                        continue
                        
                    # Reset pointer to start scanning for keywords
                    f.seek(0)
                    for i, line in enumerate(f):
                        if any(k in line for k in keywords):
                            try:
                                dialect = csv.Sniffer().sniff(line)
                                return i, dialect.delimiter, enc
                            except:
                                return i, ';', enc
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        return 0, ';', 'utf-8'
    
    def read_pm_data(self, file_path: Path) -> pd.DataFrame:
        """Reads PM data using the detected encoding to prevent UnicodeDecodeErrors."""
        pm_keywords = ["Date", "ERBS Id", "EUtranCell Id"]
        
        # 1. Detect skip, separator, AND the successful encoding
        skip, sep, enc = self._find_start_params(file_path, pm_keywords)
        
        try:
            # 2. IMPORTANT: We pass the 'enc' variable to pd.read_csv
            df = pd.read_csv(
                file_path, 
                sep=sep, 
                skiprows=skip, 
                decimal=',', 
                encoding=enc,  # This fixes the '0xff' crash
                engine='python'
            )
            
            df = df.dropna(axis=1, how='all')
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            print(f"❌ Error loading {file_path.name} with {enc}: {e}")
            return None
    
    def read_design_data(self, file_path: Path) -> pd.DataFrame:
        """Reads Site Design / Cell Database files with special character support."""
        # Add 'Cell ID' to keywords as 2G/3G files often use it instead of Site_ID
        design_keywords = ["Site_ID", "Site Name", "Latitude", "Longitude", "Azimuth", "Cell ID"]
        
        skip, sep, enc = self._find_start_params(file_path, design_keywords)
        
        try:
            df = pd.read_csv(
                file_path, 
                sep=sep, 
                skiprows=skip, 
                encoding=enc, 
                engine='python',    # Better at handling mixed-character lines
                on_bad_lines='skip' # Skips rows with unexpected special symbols
            )
            df.columns = df.columns.str.strip()
            return df
        except UnicodeDecodeError:
            # Emergency Fallback: If it found headers with one encoding but fails on data,
            # Latin-1 (ISO-8859-1) is the universal safety net for European/African characters.
            return pd.read_csv(file_path, sep=sep, skiprows=skip, encoding='latin-1', engine='python')


    def read_cm_data(self, file_path: Path) -> pd.DataFrame:
        """Reads CM data, handling rows with inconsistent column counts."""
        cm_keywords = ["ManagedElement", "MO", "Parameter Name"]
        skip, sep, enc = self._find_start_params(file_path, cm_keywords)
        
        # Use engine='python' and on_bad_lines to handle telecom 'metadata' rows
        df = pd.read_csv(
            file_path, 
            sep=sep, 
            skiprows=skip, 
            encoding=enc, 
            engine='python', 
            on_bad_lines='skip'
        )
        df.columns = df.columns.str.strip()
        return df

    def read_rf_data(self, file_path: Path) -> pd.DataFrame:
        """Reads RF data with the same robustness as CM."""
        rf_keywords = ["Cell ID", "Latitude", "Longitude", "RSRP"]
        skip, sep, enc = self._find_start_params(file_path, rf_keywords)
        
        df = pd.read_csv(
            file_path, 
            sep=sep, 
            skiprows=skip, 
            encoding=enc, 
            engine='python', 
            on_bad_lines='skip'
        )
        df.columns = df.columns.str.strip()
        return df