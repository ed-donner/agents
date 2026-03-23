import sqlite3
import datetime
import logging
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class InventoryManager:
    def __init__(self, db_path: str = "farm_inventory.db"):
        self.db_path = db_path
        self._initialize_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crops (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    planting_date TEXT,
                    harvest_date TEXT,
                    field_assignment TEXT,
                    growth_stage TEXT,
                    health_status TEXT,
                    expected_yield REAL,
                    actual_yield REAL,
                    notes TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS livestock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    species TEXT,
                    breed TEXT,
                    birth_date TEXT,
                    weight REAL,
                    health_status TEXT,
                    vaccination_records TEXT,
                    field_assignment TEXT
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT,
                    unit TEXT,
                    unit_cost REAL,
                    supplier TEXT,
                    quantity REAL,
                    reorder_threshold REAL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    item_id INTEGER,
                    transaction_type TEXT,
                    quantity_delta REAL,
                    unit_cost REAL,
                    linked_entity TEXT,
                    FOREIGN KEY(item_id) REFERENCES inventory(id)
                )
            ''')

            cursor.execute("SELECT COUNT(*) FROM inventory")
            if cursor.fetchone()[0] == 0:
                self._seed_data(cursor)
                
            conn.commit()

    def _seed_data(self, cursor):
        cursor.executemany('''
            INSERT INTO crops (planting_date, harvest_date, field_assignment, growth_stage, health_status, expected_yield, actual_yield, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            ('2023-05-01', None, 'Field A', 'Vegetative', 'healthy', 5000.0, None, 'Maize, growing well.'),
            ('2023-04-15', '2023-08-10', 'Field B', 'Harvested', 'healthy', 3000.0, 3100.0, 'Cassava, good yield.'),
            ('2023-06-20', None, 'Field C', 'Seedling', 'at-risk', 2000.0, None, 'Tomatoes, showing signs of blight.')
        ])

        cursor.executemany('''
            INSERT INTO livestock (species, breed, birth_date, weight, health_status, vaccination_records, field_assignment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [
            ('Cattle', 'White Fulani', '2020-03-15', 450.5, 'healthy', 'FMD: 2023-01-10', 'Pasture 1'),
            ('Goat', 'Sokoto Red', '2022-06-10', 35.2, 'healthy', 'PPR: 2022-09-01', 'Pasture 2'),
            ('Poultry', 'Broiler', '2023-08-01', 1.5, 'diseased', 'Newcastle: 2023-08-15', 'Coop A')
        ])

        cursor.executemany('''
            INSERT INTO inventory (item_name, unit, unit_cost, supplier, quantity, reorder_threshold)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [
            ('Maize Seeds', 'kg', 1500.00, 'AgriSeed Co.', 50.0, 20.0),
            ('NPK Fertilizer', 'bags', 15000.00, 'Fertilizer Inc.', 10.0, 15.0),
            ('Cattle Feed', 'bags', 8000.00, 'FeedMasters', 100.0, 30.0)
        ])

        timestamp = datetime.datetime.now().isoformat()
        cursor.executemany('''
            INSERT INTO transactions (timestamp, item_id, transaction_type, quantity_delta, unit_cost, linked_entity)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', [
            (timestamp, 1, 'purchase', 50.0, 1500.00, 'Initial Stock'),
            (timestamp, 2, 'purchase', 10.0, 15000.00, 'Initial Stock'),
            (timestamp, 3, 'purchase', 100.0, 8000.00, 'Initial Stock')
        ])

    def add_crop(self, planting_date: str, field_assignment: str, expected_yield: float, notes: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO crops (planting_date, harvest_date, field_assignment, growth_stage, health_status, expected_yield, actual_yield, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (planting_date, None, field_assignment, 'Seedling', 'healthy', expected_yield, None, notes))
            conn.commit()

    def update_crop(self, crop_id: int, harvest_date: Optional[str] = None, growth_stage: Optional[str] = None, health_status: Optional[str] = None, actual_yield: Optional[float] = None, notes: Optional[str] = None) -> None:
        updates = []
        params = []
        if harvest_date is not None:
            updates.append("harvest_date = ?")
            params.append(harvest_date)
        if growth_stage is not None:
            updates.append("growth_stage = ?")
            params.append(growth_stage)
        if health_status is not None:
            updates.append("health_status = ?")
            params.append(health_status)
        if actual_yield is not None:
            updates.append("actual_yield = ?")
            params.append(actual_yield)
        if notes is not None:
            updates.append("notes = ?")
            params.append(notes)
            
        if not updates:
            return

        params.append(crop_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE crops SET {", ".join(updates)} WHERE id = ?
            ''', params)
            conn.commit()

    def get_crops(self) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM crops")
            return [dict(row) for row in cursor.fetchall()]

    def register_livestock(self, species: str, breed: str, birth_date: str, weight: float, field_assignment: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO livestock (species, breed, birth_date, weight, health_status, vaccination_records, field_assignment)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (species, breed, birth_date, weight, 'healthy', '', field_assignment))
            conn.commit()

    def update_livestock(self, animal_id: int, weight: Optional[float] = None, health_status: Optional[str] = None, vaccination_records: Optional[str] = None) -> None:
        updates = []
        params = []
        if weight is not None:
            updates.append("weight = ?")
            params.append(weight)
        if health_status is not None:
            updates.append("health_status = ?")
            params.append(health_status)
        if vaccination_records is not None:
            updates.append("vaccination_records = ?")
            params.append(vaccination_records)
            
        if not updates:
            return

        params.append(animal_id)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE livestock SET {", ".join(updates)} WHERE id = ?
            ''', params)
            conn.commit()

    def get_livestock(self) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM livestock")
            return [dict(row) for row in cursor.fetchall()]

    def add_inventory_item(self, item_name: str, unit: str, unit_cost: float, supplier: str, quantity: float, reorder_threshold: float) -> None:
        unit_cost = round(unit_cost, 2)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO inventory (item_name, unit, unit_cost, supplier, quantity, reorder_threshold)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (item_name, unit, unit_cost, supplier, quantity, reorder_threshold))
            conn.commit()

    def update_inventory_item(self, item_id: int, quantity_delta: float, transaction_type: str) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT quantity, reorder_threshold, unit_cost FROM inventory WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Inventory item with id {item_id} not found.")
                
            current_qty, threshold, unit_cost = row
            new_qty = current_qty + quantity_delta
            
            cursor.execute("UPDATE inventory SET quantity = ? WHERE id = ?", (new_qty, item_id))
            conn.commit()
            
            if new_qty < threshold:
                logger.warning(f"Inventory for item ID {item_id} dropped below reorder threshold ({new_qty} < {threshold}).")

            self.log_transaction(item_id, quantity_delta, unit_cost, transaction_type)

    def get_inventory_items(self) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventory")
            items = [dict(row) for row in cursor.fetchall()]
            for item in items:
                item['reorder_alert'] = item['quantity'] < item['reorder_threshold']
                item['unit_cost'] = round(item['unit_cost'], 2)
            return items

    def log_transaction(self, item_id: int, quantity_delta: float, unit_cost: float, linked_entity: Optional[str]) -> None:
        unit_cost = round(unit_cost, 2)
        transaction_type = "purchase" if quantity_delta > 0 else "use/disposal"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            timestamp = datetime.datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO transactions (timestamp, item_id, transaction_type, quantity_delta, unit_cost, linked_entity)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, item_id, transaction_type, quantity_delta, unit_cost, linked_entity))
            conn.commit()

    def get_transactions(self) -> List[Dict]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions ORDER BY timestamp DESC")
            transactions = [dict(row) for row in cursor.fetchall()]
            for tx in transactions:
                tx['unit_cost'] = round(tx['unit_cost'], 2)
            return transactions

    def generate_report(self, start_date: str, end_date: str, report_type: str) -> Dict:
        report = {
            "start_date": start_date,
            "end_date": end_date,
            "report_type": report_type,
            "data": []
        }
        
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if report_type == "crop performance":
                cursor.execute('''
                    SELECT * FROM crops 
                    WHERE planting_date >= ? AND planting_date <= ?
                    OR (harvest_date IS NOT NULL AND harvest_date >= ? AND harvest_date <= ?)
                ''', (start_date, end_date, start_date, end_date))
                report["data"] = [dict(row) for row in cursor.fetchall()]
                
            elif report_type == "livestock health":
                cursor.execute("SELECT * FROM livestock")
                report["data"] = [dict(row) for row in cursor.fetchall()]
                
            elif report_type == "inventory status":
                cursor.execute("SELECT * FROM inventory")
                report["data"] = [dict(row) for row in cursor.fetchall()]
                
            elif report_type == "transactions":
                cursor.execute('''
                    SELECT * FROM transactions 
                    WHERE timestamp >= ? AND timestamp <= ?
                ''', (start_date, end_date + "T23:59:59"))
                report["data"] = [dict(row) for row in cursor.fetchall()]
                
        return report