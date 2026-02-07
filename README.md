# 📡 RadioRCA
**Telecom Root Cause Analysis Framework**

A specialized Python framework for Telecom Root Cause Analysis (RCA). This tool automates the ingestion of Performance Management (PM), Configuration (CM), and Site Design data into a structured archive for analysis.

RadioRCA is designed to bridge the gap between messy network exports and actionable insights. It handles multi-vendor CSV inconsistencies, standardizes decimals/separators, and maintains a dual-archive system to ensure data integrity.

---

## 🛠 Features & Realization (Current Status)

* **Hybrid Core**: Shared logic engine for terminal and web interfaces.
* **Interactive Web Portal**: Built with Streamlit for visual site diagnostics.
* **Two-Way Binding**: Sync coordinates by typing in the sidebar or clicking the interactive map.
* **Visual Insights**: Map-based antenna wedges and site-to-user path visualization.

## 💻 Quick Start
1. **Process new data**:
   ```bash

   python3 src/main.py
