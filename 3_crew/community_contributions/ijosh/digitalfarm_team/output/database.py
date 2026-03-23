from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Sequence, Tuple, Union

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
DB_PATH = OUTPUT_DIR / "database.sqlite"


def _ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _connect() -> sqlite3.Connection:
    _ensure_output_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn


def _now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat(sep=" ")


def _date_iso(value: Union[str, date, datetime]) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _dt_iso(value: Union[str, datetime]) -> str:
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat(sep=" ")
    return str(value)


def _money(value: Union[str, float, int, Decimal]) -> float:
    d = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(d)


def _json_text(value: Any) -> str:
    import json
    return json.dumps(value, ensure_ascii=False)


def _json_load(value: Optional[str], default: Any = None) -> Any:
    import json
    if value is None or value == "":
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


class DatabaseManager:
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        _ensure_output_dir()

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = _connect() if Path(self.db_path) == DB_PATH else sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA foreign_keys = ON;")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, query: str, params: Sequence[Any] = ()) -> sqlite3.Cursor:
        with self.connection() as conn:
            cur = conn.execute(query, params)
            return cur

    def fetchall(self, query: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        with self.connection() as conn:
            cur = conn.execute(query, params)
            return [dict(row) for row in cur.fetchall()]

    def fetchone(self, query: str, params: Sequence[Any] = ()) -> Optional[Dict[str, Any]]:
        with self.connection() as conn:
            cur = conn.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None

    def create_crop(
        self,
        crop_name: str,
        planting_date: Union[str, date],
        field_id: int,
        growth_stage: str = "planted",
        health_status: str = "healthy",
        expected_yield: float = 0.0,
        actual_yield: Optional[float] = None,
        harvest_date: Optional[Union[str, date]] = None,
        notes: str = "",
    ) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO crops
                (crop_name, planting_date, harvest_date, field_id, growth_stage, health_status, expected_yield, actual_yield, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    crop_name,
                    _date_iso(planting_date),
                    _date_iso(harvest_date) if harvest_date else None,
                    field_id,
                    growth_stage,
                    health_status,
                    float(expected_yield),
                    float(actual_yield) if actual_yield is not None else None,
                    notes,
                ),
            )
            return cur.lastrowid

    def get_crops(self) -> List[Dict[str, Any]]:
        return self.fetchall(
            """
            SELECT c.*, f.name AS field_name
            FROM crops c
            LEFT JOIN fields f ON c.field_id = f.id
            ORDER BY c.id DESC
            """
        )

    def get_crop(self, crop_id: int) -> Optional[Dict[str, Any]]:
        return self.fetchone(
            """
            SELECT c.*, f.name AS field_name
            FROM crops c
            LEFT JOIN fields f ON c.field_id = f.id
            WHERE c.id = ?
            """,
            (crop_id,),
        )

    def update_crop(self, crop_id: int, **fields: Any) -> None:
        allowed = {
            "crop_name",
            "planting_date",
            "harvest_date",
            "field_id",
            "growth_stage",
            "health_status",
            "expected_yield",
            "actual_yield",
            "notes",
        }
        pairs = []
        params = []
        for k, v in fields.items():
            if k in allowed and v is not None:
                pairs.append(f"{k} = ?")
                if k in {"planting_date", "harvest_date"}:
                    params.append(_date_iso(v))
                else:
                    params.append(v)
        if not pairs:
            return
        params.append(crop_id)
        self.execute(f"UPDATE crops SET {', '.join(pairs)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", params)

    def delete_crop(self, crop_id: int) -> None:
        self.execute("DELETE FROM crops WHERE id = ?", (crop_id,))

    def create_field(
        self,
        name: str,
        location: str,
        area_hectares: float,
        soil_type: str = "",
        status: str = "available",
        notes: str = "",
    ) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO fields (name, location, area_hectares, soil_type, status, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, location, float(area_hectares), soil_type, status, notes),
            )
            return cur.lastrowid

    def get_fields(self) -> List[Dict[str, Any]]:
        return self.fetchall("SELECT * FROM fields ORDER BY id DESC")

    def get_field(self, field_id: int) -> Optional[Dict[str, Any]]:
        return self.fetchone("SELECT * FROM fields WHERE id = ?", (field_id,))

    def update_field(self, field_id: int, **fields: Any) -> None:
        allowed = {"name", "location", "area_hectares", "soil_type", "status", "notes"}
        pairs = []
        params = []
        for k, v in fields.items():
            if k in allowed and v is not None:
                pairs.append(f"{k} = ?")
                params.append(v)
        if not pairs:
            return
        params.append(field_id)
        self.execute(f"UPDATE fields SET {', '.join(pairs)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", params)

    def delete_field(self, field_id: int) -> None:
        self.execute("DELETE FROM fields WHERE id = ?", (field_id,))

    def create_livestock(
        self,
        tag: str,
        species: str,
        breed: str,
        date_of_birth: Union[str, date],
        weight_kg: float,
        field_id: Optional[int] = None,
        health_status: str = "healthy",
        vaccination_records: str = "",
        notes: str = "",
    ) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO livestock
                (tag, species, breed, date_of_birth, weight_kg, field_id, health_status, vaccination_records, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tag,
                    species,
                    breed,
                    _date_iso(date_of_birth),
                    float(weight_kg),
                    field_id,
                    health_status,
                    vaccination_records,
                    notes,
                ),
            )
            return cur.lastrowid

    def get_livestock(self) -> List[Dict[str, Any]]:
        return self.fetchall(
            """
            SELECT l.*, f.name AS field_name
            FROM livestock l
            LEFT JOIN fields f ON l.field_id = f.id
            ORDER BY l.id DESC
            """
        )

    def get_livestock_item(self, animal_id: int) -> Optional[Dict[str, Any]]:
        return self.fetchone(
            """
            SELECT l.*, f.name AS field_name
            FROM livestock l
            LEFT JOIN fields f ON l.field_id = f.id
            WHERE l.id = ?
            """,
            (animal_id,),
        )

    def update_livestock(self, animal_id: int, **fields: Any) -> None:
        allowed = {
            "tag",
            "species",
            "breed",
            "date_of_birth",
            "weight_kg",
            "field_id",
            "health_status",
            "vaccination_records",
            "notes",
        }
        pairs = []
        params = []
        for k, v in fields.items():
            if k in allowed and v is not None:
                pairs.append(f"{k} = ?")
                params.append(_date_iso(v) if k == "date_of_birth" else v)
        if not pairs:
            return
        params.append(animal_id)
        self.execute(f"UPDATE livestock SET {', '.join(pairs)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", params)

    def delete_livestock(self, animal_id: int) -> None:
        self.execute("DELETE FROM livestock WHERE id = ?", (animal_id,))

    def create_inventory_item(
        self,
        item_name: str,
        category: str,
        quantity_on_hand: float,
        unit_of_measure: str,
        reorder_threshold: float,
        supplier: str,
        unit_cost: float,
        notes: str = "",
    ) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO inventory_items
                (item_name, category, quantity_on_hand, unit_of_measure, reorder_threshold, supplier, unit_cost, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_name,
                    category,
                    float(quantity_on_hand),
                    unit_of_measure,
                    float(reorder_threshold),
                    supplier,
                    _money(unit_cost),
                    notes,
                ),
            )
            return cur.lastrowid

    def get_inventory_items(self) -> List[Dict[str, Any]]:
        items = self.fetchall("SELECT * FROM inventory_items ORDER BY id DESC")
        for item in items:
            item["low_stock_warning"] = item["quantity_on_hand"] <= item["reorder_threshold"]
        return items

    def get_inventory_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        item = self.fetchone("SELECT * FROM inventory_items WHERE id = ?", (item_id,))
        if item:
            item["low_stock_warning"] = item["quantity_on_hand"] <= item["reorder_threshold"]
        return item

    def update_inventory_item(self, item_id: int, **fields: Any) -> None:
        allowed = {
            "item_name",
            "category",
            "quantity_on_hand",
            "unit_of_measure",
            "reorder_threshold",
            "supplier",
            "unit_cost",
            "notes",
        }
        pairs = []
        params = []
        for k, v in fields.items():
            if k in allowed and v is not None:
                pairs.append(f"{k} = ?")
                params.append(_money(v) if k == "unit_cost" else v)
        if not pairs:
            return
        params.append(item_id)
        self.execute(f"UPDATE inventory_items SET {', '.join(pairs)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", params)

    def delete_inventory_item(self, item_id: int) -> None:
        self.execute("DELETE FROM inventory_items WHERE id = ?", (item_id,))

    def log_transaction(
        self,
        item_id: int,
        quantity_delta: float,
        unit_cost: float,
        transaction_type: str,
        linked_entity_type: Optional[str] = None,
        linked_entity_id: Optional[int] = None,
        notes: str = "",
        transaction_time: Optional[Union[str, datetime]] = None,
    ) -> int:
        with self.connection() as conn:
            item = conn.execute(
                "SELECT quantity_on_hand, reorder_threshold FROM inventory_items WHERE id = ?",
                (item_id,),
            ).fetchone()
            if not item:
                raise ValueError("Inventory item not found")

            new_qty = float(item["quantity_on_hand"]) + float(quantity_delta)
            cur = conn.execute(
                """
                INSERT INTO transactions
                (item_id, transaction_type, quantity_delta, unit_cost, linked_entity_type, linked_entity_id, notes, transaction_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    transaction_type,
                    float(quantity_delta),
                    _money(unit_cost),
                    linked_entity_type,
                    linked_entity_id,
                    notes,
                    _dt_iso(transaction_time) if transaction_time else _now_iso(),
                ),
            )
            conn.execute(
                "UPDATE inventory_items SET quantity_on_hand = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (new_qty, item_id),
            )
            return cur.lastrowid

    def get_transactions(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT t.*, i.item_name
            FROM transactions t
            LEFT JOIN inventory_items i ON t.item_id = i.id
        """
        params: List[Any] = []
        clauses = []
        if start_date:
            clauses.append("date(t.transaction_time) >= date(?)")
            params.append(start_date)
        if end_date:
            clauses.append("date(t.transaction_time) <= date(?)")
            params.append(end_date)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY t.id DESC"
        return self.fetchall(query, params)

    def get_transaction(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        return self.fetchone("SELECT * FROM transactions WHERE id = ?", (transaction_id,))

    def delete_transaction(self, transaction_id: int) -> None:
        self.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))

    def create_sensor(
        self,
        sensor_name: str,
        sensor_type: str,
        field_id: Optional[int],
        status: str = "active",
        last_reading: Optional[float] = None,
        last_reading_at: Optional[Union[str, datetime]] = None,
        notes: str = "",
    ) -> int:
        with self.connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO sensors
                (sensor_name, sensor_type, field_id, status, last_reading, last_reading_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sensor_name,
                    sensor_type,
                    field_id,
                    status,
                    last_reading,
                    _dt_iso(last_reading_at) if last_reading_at else None,
                    notes,
                ),
            )
            return cur.lastrowid

    def get_sensors(self) -> List[Dict[str, Any]]:
        return self.fetchall(
            """
            SELECT s.*, f.name AS field_name
            FROM sensors s
            LEFT JOIN fields f ON s.field_id = f.id
            ORDER BY s.id DESC
            """
        )

    def get_sensor(self, sensor_id: int) -> Optional[Dict[str, Any]]:
        return self.fetchone("SELECT * FROM sensors WHERE id = ?", (sensor_id,))

    def update_sensor(self, sensor_id: int, **fields: Any) -> None:
        allowed = {"sensor_name", "sensor_type", "field_id", "status", "last_reading", "last_reading_at", "notes"}
        pairs = []
        params = []
        for k, v in fields.items():
            if k in allowed and v is not None:
                pairs.append(f"{k} = ?")
                params.append(_dt_iso(v) if k == "last_reading_at" else v)
        if not pairs:
            return
        params.append(sensor_id)
        self.execute(f"UPDATE sensors SET {', '.join(pairs)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", params)

    def delete_sensor(self, sensor_id: int) -> None:
        self.execute("DELETE FROM sensors WHERE id = ?", (sensor_id,))

    def generate_report(self, start_date: str, end_date: str, report_type: str) -> Dict[str, Any]:
        report_type = report_type.lower().strip()
        result: Dict[str, Any] = {"report_type": report_type, "start_date": start_date, "end_date": end_date}

        if report_type in {"crop", "crop performance", "crops"}:
            crops = self.fetchall(
                """
                SELECT * FROM crops
                WHERE date(planting_date) BETWEEN date(?) AND date(?)
                   OR date(harvest_date) BETWEEN date(?) AND date(?)
                """,
                (start_date, end_date, start_date, end_date),
            )
            result["total_crops"] = len(crops)
            result["harvested"] = sum(1 for c in crops if c.get("harvest_date"))
            result["avg_expected_yield"] = round(
                sum(float(c["expected_yield"] or 0) for c in crops) / len(crops), 2
            ) if crops else 0.0
            result["avg_actual_yield"] = round(
                sum(float(c["actual_yield"] or 0) for c in crops) / max(1, sum(1 for c in crops if c.get("actual_yield") is not None)),
                2,
            ) if any(c.get("actual_yield") is not None for c in crops) else 0.0
            result["records"] = crops

        elif report_type in {"livestock", "livestock health"}:
            animals = self.get_livestock()
            result["total_animals"] = len(animals)
            result["healthy"] = sum(1 for a in animals if a["health_status"] == "healthy")
            result["at_risk"] = sum(1 for a in animals if a["health_status"] == "at-risk")
            result["diseased"] = sum(1 for a in animals if a["health_status"] == "diseased")
            result["records"] = animals

        elif report_type in {"inventory", "inventory status"}:
            items = self.get_inventory_items()
            result["total_items"] = len(items)
            result["low_stock_items"] = [i for i in items if i["low_stock_warning"]]
            result["records"] = items

        elif report_type in {"sensor", "sensor anomalies"}:
            sensors = self.fetchall(
                """
                SELECT s.*, f.name AS field_name
                FROM sensors s
                LEFT JOIN fields f ON s.field_id = f.id
                WHERE (s.status != 'active')
                   OR s.last_reading IS NULL
                ORDER BY s.id DESC
                """
            )
            result["anomalies"] = sensors
            result["count"] = len(sensors)

        else:
            result["error"] = "Unsupported report type"

        return result


def init_db() -> None:
    _ensure_output_dir()
    first_run = not DB_PATH.exists()

    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                location TEXT NOT NULL,
                area_hectares REAL NOT NULL DEFAULT 0,
                soil_type TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'available',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS crops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                crop_name TEXT NOT NULL,
                planting_date TEXT NOT NULL,
                harvest_date TEXT,
                field_id INTEGER,
                growth_stage TEXT NOT NULL DEFAULT 'planted',
                health_status TEXT NOT NULL DEFAULT 'healthy',
                expected_yield REAL NOT NULL DEFAULT 0,
                actual_yield REAL,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(field_id) REFERENCES fields(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS livestock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag TEXT NOT NULL UNIQUE,
                species TEXT NOT NULL,
                breed TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                weight_kg REAL NOT NULL DEFAULT 0,
                field_id INTEGER,
                health_status TEXT NOT NULL DEFAULT 'healthy',
                vaccination_records TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(field_id) REFERENCES fields(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS inventory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT NOT NULL,
                category TEXT NOT NULL,
                quantity_on_hand REAL NOT NULL DEFAULT 0,
                unit_of_measure TEXT NOT NULL,
                reorder_threshold REAL NOT NULL DEFAULT 0,
                supplier TEXT DEFAULT '',
                unit_cost REAL NOT NULL DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                quantity_delta REAL NOT NULL,
                unit_cost REAL NOT NULL DEFAULT 0,
                linked_entity_type TEXT,
                linked_entity_id INTEGER,
                notes TEXT DEFAULT '',
                transaction_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(item_id) REFERENCES inventory_items(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sensors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_name TEXT NOT NULL,
                sensor_type TEXT NOT NULL,
                field_id INTEGER,
                status TEXT NOT NULL DEFAULT 'active',
                last_reading REAL,
                last_reading_at TEXT,
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(field_id) REFERENCES fields(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_crops_field_id ON crops(field_id);
            CREATE INDEX IF NOT EXISTS idx_livestock_field_id ON livestock(field_id);
            CREATE INDEX IF NOT EXISTS idx_transactions_item_id ON transactions(item_id);
            CREATE INDEX IF NOT EXISTS idx_transactions_time ON transactions(transaction_time);
            CREATE INDEX IF NOT EXISTS idx_sensors_field_id ON sensors(field_id);
            """
        )

        if first_run:
            fields = [
                ("North Field", "Abeokuta", 12.5, "Loamy", "active", "Primary maize and cassava block"),
                ("South Field", "Ibadan", 8.2, "Sandy loam", "active", "Vegetable and legume rotation"),
                ("River Plot", "Abeokuta", 5.0, "Clay loam", "active", "Irrigated plot near water source"),
            ]
            conn.executemany(
                "INSERT INTO fields (name, location, area_hectares, soil_type, status, notes) VALUES (?, ?, ?, ?, ?, ?)",
                fields,
            )

            field_ids = [row["id"] for row in conn.execute("SELECT id FROM fields ORDER BY id").fetchall()]

            crops = [
                ("Maize", "2026-01-10", None, field_ids[0], "vegetative", "healthy", 4.5, None, "Early growth, good stand count"),
                ("Cassava", "2025-11-22", None, field_ids[0], "established", "at-risk", 8.0, None, "Requires weed control"),
                ("Tomato", "2025-12-05", "2026-03-01", field_ids[1], "harvested", "healthy", 2.2, 2.0, "Batch 1 completed"),
                ("Soybean", "2025-12-20", None, field_ids[1], "flowering", "healthy", 1.8, None, "Flowering observed"),
                ("Pepper", "2026-01-02", None, field_ids[2], "fruiting", "diseased", 1.1, None, "Fungal spotting detected"),
            ]
            conn.executemany(
                """
                INSERT INTO crops
                (crop_name, planting_date, harvest_date, field_id, growth_stage, health_status, expected_yield, actual_yield, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                crops,
            )

            livestock = [
                ("COW-001", "Cattle", "White Fulani", "2023-05-14", 320.5, field_ids[0], "healthy", "2025-10-10: FMD; 2025-11-12: dewormed", "Breeding cow"),
                ("GOAT-001", "Goat", "West African Dwarf", "2024-01-09", 38.2, field_ids[1], "at-risk", "2025-12-01: PPR", "Slight weight loss monitored"),
                ("SHEEP-001", "Sheep", "Yankasa", "2024-03-21", 44.0, field_ids[2], "healthy", "2025-12-15: clostridial vaccine", "Growing well"),
            ]
            conn.executemany(
                """
                INSERT INTO livestock
                (tag, species, breed, date_of_birth, weight_kg, field_id, health_status, vaccination_records, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                livestock,
            )

            inventory = [
                ("Maize Seeds", "seeds", 120.0, "kg", 40.0, "GreenHarvest Ltd", 2500.00, "Hybrid seed stock"),
                ("NPK Fertiliser", "fertiliser", 50.0, "bags", 15.0, "AgroPlus", 18500.00, "20kg bags"),
                ("Urea Fertiliser", "fertiliser", 35.0, "bags", 10.0, "AgroPlus", 17200.00, "Nitrogen booster"),
                ("Glyphosate", "pesticide", 18.0, "litres", 6.0, "FarmChem", 9800.00, "Weed control"),
                ("Knapsack Sprayer", "equipment", 6.0, "units", 2.0, "AgroTools", 45000.00, "Manual sprayer"),
                ("Layer Feed", "feed", 200.0, "kg", 70.0, "FeedMaster", 4200.00, "Poultry feed"),
                ("Broiler Feed", "feed", 160.0, "kg", 60.0, "FeedMaster", 4100.00, "Poultry feed"),
                ("Vet Syringes", "equipment", 100.0, "pcs", 25.0, "MediFarm", 220.00, "Disposable"),
                ("Limestone", "fertiliser", 80.0, "kg", 20.0, "SoilCare", 1200.00, "Soil amendment"),
                ("Irrigation Hose", "equipment", 15.0, "rolls", 5.0, "AgroTools", 15500.00, "PVC hose"),
            ]
            conn.executemany(
                """
                INSERT INTO inventory_items
                (item_name, category, quantity_on_hand, unit_of_measure, reorder_threshold, supplier, unit_cost, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                inventory,
            )

            sensors = [
                ("Soil Moisture A", "soil_moisture", field_ids[0], "active", 41.2, "2026-03-20 07:20:00", "North block sensor"),
                ("Temperature A", "temperature", field_ids[0], "active", 31.6, "2026-03-20 07:20:00", "Ambient temp"),
                ("Soil Moisture B", "soil_moisture", field_ids[1], "active", 52.8, "2026-03-20 07:21:00", "South block sensor"),
                ("Humidity B", "humidity", field_ids[1], "maintenance", 78.4, "2026-03-18 09:15:00", "Calibration due"),
                ("Water Level C", "water_level", field_ids[2], "active", 63.0, "2026-03-20 07:23:00", "Irrigation tank"),
            ]
            conn.executemany(
                """
                INSERT INTO sensors
                (sensor_name, sensor_type, field_id, status, last_reading, last_reading_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                sensors,
            )

            inv_ids = [row["id"] for row in conn.execute("SELECT id FROM inventory_items ORDER BY id").fetchall()]
            transactions = [
                (inv_ids[0], "purchase", 80.0, 2500.00, "crop", 1, "Initial maize seed procurement", "2026-01-05 08:00:00"),
                (inv_ids[1], "purchase", 20.0, 18500.00, "field", 1, "Bulk fertiliser restock", "2026-01-06 09:00:00"),
                (inv_ids[3], "use", -2.0, 9800.00, "crop", 2, "Applied herbicide on cassava plot", "2026-01-20 10:30:00"),
                (inv_ids[5], "use", -25.0, 4200.00, "livestock", 1, "Feed issued to poultry house", "2026-02-02 12:15:00"),
                (inv_ids[4], "disposal", -1.0, 45000.00, "field", 2, "Damaged sprayer disposed", "2026-02-10 15:40:00"),
            ]
            conn.executemany(
                """
                INSERT INTO transactions
                (item_id, transaction_type, quantity_delta, unit_cost, linked_entity_type, linked_entity_id, notes, transaction_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                transactions,
            )

            for item_id, delta, _, _, _, _, _, _ in transactions:
                conn.execute(
                    "UPDATE inventory_items SET quantity_on_hand = quantity_on_hand + ? WHERE id = ?",
                    (delta, item_id),
                )


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


init_db()