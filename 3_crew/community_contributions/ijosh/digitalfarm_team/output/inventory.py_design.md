```markdown
# Design Specification for `inventory.py` Module

## Overview
The `inventory.py` module serves as the backbone for the Digital Integrated Farm Inventory System. It encapsulates all core functionalities needed to manage crops, livestock, and supply inventory while tracking transactions and facilitating report generation. The module uses an SQLite database for data persistence and will seed the database with demo data upon initial use.

## Core Classes and Method Signatures

### Class: `InventoryManager`

Main class responsible for managing the farm inventory system. Contains methods related to crops, livestock, supplies, transactions, and report generation.

#### Methods

##### Initialization
- **`__init__(self)`**
  - Initializes the InventoryManager class, sets up the SQLite database connection, and seeds initial demo data.

##### Crop Management
- **`add_crop(self, planting_date: str, field_assignment: str, expected_yield: float, notes: str) -> None`**
  - Adds a new crop entry with an initial healthy status and growth stage.

- **`update_crop(self, crop_id: int, harvest_date: Optional[str], growth_stage: Optional[str], health_status: Optional[str], actual_yield: Optional[float], notes: Optional[str]) -> None`**
  - Updates an existing crop’s details like harvest date, growth stage, and yield.

- **`get_crops(self) -> List[Dict]`**
  - Retrieves all crop records, including their current health status and expected vs. actual yield.

##### Livestock Management
- **`register_livestock(self, species: str, breed: str, birth_date: str, weight: float, field_assignment: str) -> None`**
  - Registers a new animal in the system with initial health status as ‘healthy’.

- **`update_livestock(self, animal_id: int, weight: Optional[float], health_status: Optional[str], vaccination_records: Optional[str]) -> None`**
  - Updates existing livestock information like weight and health status.

- **`get_livestock(self) -> List[Dict]`**
  - Retrieves all livestock records with their current health status and vaccination history.

##### Inventory/Supplies Management
- **`add_inventory_item(self, item_name: str, unit: str, unit_cost: float, supplier: str, quantity: float, reorder_threshold: float) -> None`**
  - Registers a new inventory item and initializes the stock level.

- **`update_inventory_item(self, item_id: int, quantity_delta: float, transaction_type: str) -> None`**
  - Updates an inventory item based on purchase, use, or disposal, adjusting the stock levels accordingly.

- **`get_inventory_items(self) -> List[Dict]`**
  - Returns the list of inventory items showing current stock levels and reorder alerts.

##### Transactions
- **`log_transaction(self, item_id: int, quantity_delta: float, unit_cost: float, linked_entity: Optional[str]) -> None`**
  - Logs every inventory movement with details about the transaction, timestamped and linked to a crop or livestock.

- **`get_transactions(self) -> List[Dict]`**
  - Retrieves a historical log of all transactions made for inventory items.

##### Reports
- **`generate_report(self, start_date: str, end_date: str, report_type: str) -> Dict`**
  - Generates summary reports for a specified date range and report type (e.g., crop performance, livestock health).

## Business Rules
- Implement alert functionality within inventory transactions to warn if quantities fall below the reorder threshold, but allow transactions to proceed.
- Ensure monetary values for all transactions are consistently stored in NGN, formatted to two decimal places.

## Persistence
- Integrate SQLite for persistent data storage.
- On initial run, seed the database with realistic data for simulation purposes, ensuring that the system has baseline data to operate with.

## User Interface
- Although not defined within this module, this backend design supports a rich Gradio 6 dashboard for a user-friendly interface. The UI is expected to be theme-consistent, card-based, and implements user-friendly elements like searchable and sortable tables with at least one Plotly-powered chart and comprehensive CRUD operations directly accessible.

This detailed design serves as the core module blueprint for building components of the Digital Integrated Farm Inventory System, ensuring extensible, maintainable, and efficient farm operations management.
```
