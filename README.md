# 📡 RadioRCA
**Telecom Root Cause Analysis Framework**

A specialized Python framework for Telecom Root Cause Analysis (RCA). This tool automates the ingestion of Performance Management (PM), Configuration (CM), and Site Design data into a structured archive for analysis.

RadioRCA is designed to bridge the gap between messy network exports and actionable insights. It handles multi-vendor CSV inconsistencies, standardizes decimals/separators, and maintains a dual-archive system to ensure data integrity.

---

## 🛠 Features & Realization (Current Status)

### 1. Automated Data Pipeline
- **Smart Ingestion**: Detects headers and delimiters (`;` vs `,`) automatically.
- **Dual-Archive Logic**: 
    - **Raw Archive**: Preserves the original file exactly as exported for auditing.
    - **Clean Archive**: Generates a standardized version with consistent date formats and numeric decimals.
- **Multi-Source Support**: Modules ready for **PM**, **CM**, **Site Database**, and **RF** (Drive Test) data.

### 2. Command Line Interface (CLI)
The tool currently supports the following operational commands:

| Command | Purpose |
| :--- | :--- |
| `list` | Displays all archived files across categories with a numerical index. |
| `show <type> <index>` | Prints a snapshot of a specific file or aggregates all files in a category. |
| `kpi` | **Audit Matrix**: Generates a cross-file map of Cell IDs and Performance Counters to verify data consistency before correlation. |

---

## 📁 Directory Structure
- `data/input/`: Drop raw exports here (categorized by type).
- `src/infrastructure/`: Core readers and cleaning logic.
- `src/cli.py`: User interface for data navigation.
- `src/main.py`: Main execution script for batch processing.

---

## 💻 Quick Start
1. **Process new data**:
   ```bash
   python3 src/main.py