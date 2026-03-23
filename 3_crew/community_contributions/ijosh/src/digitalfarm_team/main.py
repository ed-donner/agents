#!/usr/bin/env python
import re
import sys
import warnings
from datetime import datetime
from digitalfarm_team.crew import DigitalFarmTeam  
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


requirements = """
A Digital Integrated Farm Inventory System with the following capabilities:

CORE DOMAIN ENTITIES
- Crop management: track planting date, harvest date, field assignment, growth stage,
  health status (healthy / at-risk / diseased), expected yield, actual yield, notes.
- Livestock management: animal registry with species, breed, date of birth, weight,
  health status, vaccination records, field assignment.
- Inventory / supplies: items (seeds, fertilisers, pesticides, equipment, feed) with
  quantity on hand, unit of measure, reorder threshold, supplier, unit cost.
- Transactions: every inventory movement (purchase, use, disposal) is logged with
  timestamp, quantity delta, unit cost, and linked entity (crop/field/livestock).
- Reports: generate summary reports by date range covering crop performance,
  livestock health, inventory status, sensor anomalies.

BUSINESS RULES
- Warn (do not block) when inventory drops below reorder threshold.
- All monetary values stored in NGN with 2 decimal places.

PERSISTENCE
- SQLite database.
- Seed database with realistic demo data on first run.

UI REQUIREMENTS
- Rich and clean Gradio 6 dashboard  (see tasks.yaml).
- Light green and golden farm theme, card-based layout.
- Searchable, sortable data tables.
- At least one Plotly chart (e.g. inventory levels bar chart or crop timeline).
- All CRUD operations accessible from the UI without touching the CLI.
"""
module_name = "inventory.py"
class_name = "Inventorymanager"


def run():
    inputs = {
        "requirements": requirements,
        "module_name": module_name,
        "class_name": class_name,
    }

    try:
        result = DigitalFarmTeam().crew().kickoff(inputs=inputs)
        print(result)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")
