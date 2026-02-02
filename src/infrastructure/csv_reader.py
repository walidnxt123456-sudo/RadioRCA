import pandas as pd
import csv
from pathlib import Path

class CsvReader:
    def _find_start_params(self, file_path: Path, keywords: list):
        """
        Internal Helper:
        Loops through the file to find the header row containing specific keywords.
        Returns the row index to skip and the detected separator.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                # Check if any of our identifying keywords are in this line
                if any(k in line for k in keywords):
                    # Use Sniffer to detect if the separator is ; or ,
                    try:
                        dialect = csv.Sniffer().sniff(line)
                        return i, dialect.delimiter
                    except csv.Error:
                        # Fallback if sniffing fails but keywords were found
                        return i, ';'
        return 0, ';' # Fallback if keywords are never found

    def read_pm_data(self, file_path: Path) -> pd.DataFrame:
        # HARDCODED KEYWORDS for PM: These are specific to your KPI files
        pm_keywords = ["Date", "ERBS Id", "EUtranCell Id"]
        
        skip, sep = self._find_start_params(file_path, pm_keywords)
        
        # We use decimal=',' because PM data (like 70,39) uses commas
        df = pd.read_csv(file_path, sep=sep, skiprows=skip, decimal=',', engine='python')
        
        # Clean up: remove columns that are entirely empty
        df = df.dropna(axis=1, how='all')
        df.columns = df.columns.str.strip()
        return df
    
    def read_design_data(self, file_path: Path) -> pd.DataFrame:
        # Keywords usually found in a Site Design / Cell Database
        design_keywords = ["Site_ID", "Site Name", "Latitude", "Longitude", "Azimuth"]
        skip, sep = self._find_start_params(file_path, design_keywords)
        df = pd.read_csv(file_path, sep=sep, skiprows=skip)
        df.columns = df.columns.str.strip()
        return df

    def read_cm_data(self, file_path: Path) -> pd.DataFrame:
        # HARDCODED KEYWORDS for CM: (Adjust these based on your CM file headers)
        cm_keywords = ["ManagedElement", "MO", "Parameter Name"]
        
        skip, sep = self._find_start_params(file_path, cm_keywords)
        return pd.read_csv(file_path, sep=sep, skiprows=skip)

    def read_rf_data(self, file_path: Path) -> pd.DataFrame:
        # HARDCODED KEYWORDS for RF: (Adjust these based on your RF file headers)
        rf_keywords = ["Cell ID", "Latitude", "Longitude", "RSRP"]
        
        skip, sep = self._find_start_params(file_path, rf_keywords)
        return pd.read_csv(file_path, sep=sep, skiprows=skip)