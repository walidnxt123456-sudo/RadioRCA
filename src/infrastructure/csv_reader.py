from pathlib import Path
import csv


class CsvReader:
    def read(self, file_path: Path) -> list[dict]:
        with file_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)