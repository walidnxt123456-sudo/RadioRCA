from pathlib import Path
from infrastructure.csv_reader import CsvReader


def main():
    csv_path = Path("data/input/hello.csv")

    reader = CsvReader()
    rows = reader.read(csv_path)

    print("Hello World – CSV content:")
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
