import pandas as pd
import csv
from pathlib import Path

class CsvReader:
    def _find_start_params(self, file_path: Path, keywords: list):
        """
        Detects the header start row, the correct separator, and encoding.
        Adaptive for both PM (Comma/Semicolon) and CM (Tab) formats.
        """
        # Priority order for Telecom encodings
        for enc in ['utf-16', 'utf-8', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    # Validate encoding readability
                    if not f.read(1024): continue
                    f.seek(0)
                    
                    for i, line in enumerate(f):
                        if any(k in line for k in keywords):
                            # PRIORITY 1: Check for Tab (Common in CM exports)
                            if '\t' in line:
                                return i, '\t', enc
                            
                            # PRIORITY 2: Use Sniffer for PM/Database (Comma/Semicolon)
                            try:
                                dialect = csv.Sniffer().sniff(line)
                                return i, dialect.delimiter, enc
                            except:
                                # Fallback detection
                                sep = ';' if ';' in line else ','
                                return i, sep, enc
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        return 0, ';', 'utf-8'

    def read_cm_data(self, file_path: Path) -> pd.DataFrame:
        """
        Reads CM files. 
        Detects 'NodeId' to skip Ericsson metadata and handles Tab separators.
        """
        # NodeId is the best marker for the start of actual data in CM files
        cm_keywords = ["NodeId", "EquipmentId", "ENodeBFunctionId", "GNBCUCPFunctionId"]
        skip, sep, enc = self._find_start_params(file_path, cm_keywords)
        
        try:
            df = pd.read_csv(
                file_path, 
                sep=sep, 
                skiprows=skip, 
                encoding=enc, 
                engine='python', 
                on_bad_lines='skip'
            )
            # Standardize headers
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            print(f"❌ Error reading CM {file_path.name}: {e}")
            return None

    def read_pm_data(self, file_path: Path) -> pd.DataFrame:
        """Reads PM data using commas for decimals (e.g., 70,39)."""
        pm_keywords = ["Date", "ERBS Id", "EUtranCell Id", "Object"]
        skip, sep, enc = self._find_start_params(file_path, pm_keywords)
        
        try:
            df = pd.read_csv(
                file_path, 
                sep=sep, 
                skiprows=skip, 
                decimal=',', 
                encoding=enc, 
                engine='python',
                on_bad_lines='skip'
            )
            df = df.dropna(axis=1, how='all')
            df.columns = df.columns.str.strip()
            return df
        except Exception as e:
            print(f"❌ Error reading PM {file_path.name}: {e}")
            return None
    
    def read_design_data(self, file_path: Path) -> pd.DataFrame:
        """Reads Site Design / Cell Database files with fallback for special characters."""
        design_keywords = ["Site_ID", "Site Name", "Latitude", "Longitude", "Cell ID"]
        skip, sep, enc = self._find_start_params(file_path, design_keywords)
        
        try:
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
        except UnicodeDecodeError:
            return pd.read_csv(file_path, sep=sep, skiprows=skip, encoding='latin-1', engine='python')

    def read_rf_data(self, file_path: Path) -> pd.DataFrame:
        """Reads RF measurement data."""
        rf_keywords = ["Cell ID", "Latitude", "Longitude", "RSRP"]
        skip, sep, enc = self._find_start_params(file_path, rf_keywords)
        
        return pd.read_csv(file_path, sep=sep, skiprows=skip, encoding=enc, engine='python', on_bad_lines='skip')