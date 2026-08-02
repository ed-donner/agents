from fastmcp import FastMCP
import os
import aiosqlite
import sqlite3
import hashlib
import json
from datetime import datetime
from functools import wraps

BASE_DIR =  os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "healthcare.db")

mcp = FastMCP("HealthcareMCP")

# Role Permissions
ROLE_PERMISSIONS = {
    "admin": ["register_patient", "get_patient", "update_patient", "delete_patient",
              "list_patients", "search_patient", "add_staff", "get_staff",
              "list_staff"],

    "doctor": ["register_patient", "get_patient", "update_patient",
                         "list_patients", "search_patient", "get_staff"],

    "nurse": ["get_patient", "list_patients", "search_patient"],
}

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_permission(role: str, action: str) -> bool:
    return action in ROLE_PERMISSIONS.get(role, [])

# DB Init
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS staff (
                    id  INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'doctor', 'nurse')),
                    email_address TEXT NOT NULL UNIQUE,
                     password_hash  TEXT NOT NULL,
                     created_at  TEXT NOT NULL DEFAULT (datetime('now'))
                     )
                     """)
        
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS patients (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     first_name TEXT NOT NULL,
                     last_name TEXT NOT NULL,
                     dob  TEXT NOT NULL,
                     gender  TEXT NOT NULL,
                     phone   TEXT DEFAULT  '',
                     email_address  TEXT DEFAULT  '',
                     address  TEXT DEFAULT  '',
                     medical_history  TEXT DEFAULT '',
                     allergies  TEXT DEFAULT  '',
                     current_diagnosis  TEXT DEFAULT '',
                     assigned_doctor  TEXT DEFAULT  '',
                     created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                     updated_at  TEXT NOT NULL DEFAULT (datetime('now'))

                     )
                     """)
        
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS audit_log (
                     id INTEGER PRIMARY KEY AUTOINCREMENT,
                     staff_id INTEGER,
                     action TEXT NOT NULL,
                     details  TEXT DEFAULT '',
                     timestamp  TEXT NOT NULL DEFAULT (datetime('now'))
                        )
                     """)
        
        # Create a default admin if none exists
        cursor = conn.execute("SELECT COUNT(*) FROM staff WHERE role='admin'")
        if cursor.fetchone()[0] == 0:
            conn.execute(
                "INSERT INTO staff (name, role, email_address, password_hash) VALUES (?,?,?,?)",
                ("System Admin", "admin", "admin@vendor.com", hash_password("admin1234"))
            )
            conn.commit()

init_db()


# Audit Helper
async def log_action(staff_id: int, action: str, details: str = ""):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO audit_log (staff_id, action, details) VALUES (?, ?, ?)",
            (staff_id, action, details)
        )
        await conn.commit()

# Auth Helper
async def authenticate(email_address: str, password: str):
    """Returns staff record dict or None."""
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROm staff WHERE email_address = ? AND password_hash = ?",
            (email_address, hash_password(password))
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

# STAFF MCP TOOLS
@mcp.tool()
async def add_staff(
    admin_email: str,
    admin_password: str,
    name: str,
    role: str,
    email: str,
    password: str
):
    """
    (Admin only) Regiser a new staff member.
    role must be one of: admin, doctor, nurse.
    """
    staff = await authenticate(admin_email, admin_password)
    if not staff:
        return {"status": "error", "message": "Invalid credentials"}
    if not check_permission(staff["role"], "add_staff"):
        return {"statue": "error", "message": f"Role '{staff['role']}' is not allowed to add staff"}
    if role not in ("admin", "doctor", "nurse"):
        return {"status": "error", "message": "Role not recognized"}
    
    async with aiosqlite.connect(DB_PATH) as conn:
        try:
            cursor = await conn.execute(
                "INSERT INTO staff (name, role, email_address, password_hash) VALUES (?, ?, ?, ?)",
                (name, role, email, hash_password(password))
            )
            await conn.commit()
            await log_action(staff["id"], "add_staff", f"Added staff {email} as {role}")
            return {"status": "ok", "id": cursor.lastrowid, "message": f"Staff '{name}' added as {role}"}
        except Exception as e:
            return {"status": "error", "message": f"Staff already exists: {str(e)}"}
        
    
@mcp.tool()
async def get_staff(requester_email: str, requester_password: str, staff_id: int):
    """ Retrieve a staff member's info by ID"""
    requester = await authenticate(requester_email, requester_password)
    if not requester:
        return {"status": "error", "message": "Permission denied"}
    
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT id, name, role, email_address, created_at FROM staff WHERE id = ?", (staff_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return {"status": "error", "message": f"Staff {staff_id} not found"}
        return {"status": "ok", "staff": dict(row)}
    
@mcp.tool()
async def list_staff(admin_email: str, admin_password: str):
    """(Admin only) List all staff members."""
    staf = await authenticate(admin_email, admin_password)
    if not staf:
        return {"status": "error", "message": "Invalid credentials"}
    if not check_permission(staf["role"], "list_staff"):
        return {"status": "error", "message": f"Role '{staf['role']}' is not allowed to list staff"}

    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT id, name, role, email_address, created_at FROM staff ORDER By id ASC"
        )
        rows = await cursor.fetchall()
        return {"status": "ok", "staff": [dict(row) for row in rows]}


# PATIENT MCP TOOLS

@mcp.tool()
async def register_patient(
    staff_email: str,
    staff_password: str,
    first_name: str,
    last_name: str,
    dob: str,
    gender: str,
    phone: str = "",
    email_address: str = "",
    address: str = "",
    medical_history: str = "",
    allergies: str = "",
    current_diagnosis: str = "",
    assigned_doctor: str = ""
):
    """
     Register a new patient.
     Accessible by: admin, doctor,
     dob format: YYYY-MM-DD
     gender: Male | Female | other
    """
    staff = await authenticate(staff_email, staff_password)
    if not staff:
        return {"status": "error", "message": "Invalid credentials"}
    if not check_permission(staff["role"], "register_patient"):
        return {"status": "error", "message": "Permission denied"}
    
    async with aiosqlite.connect(DB_PATH) as conn:
        try:
            cursor = await conn.execute(
                """
                INSERT INTO patients (first_name, last_name, dob, gender, phone, email_address, address, medical_history, allergies, current_diagnosis, assigned_doctor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) """,
                (first_name, last_name, dob, gender, phone, email_address, address, medical_history, allergies, current_diagnosis, assigned_doctor)

            )
            await conn.commit()
            patient_id = cursor.lastrowid

            await log_action(staff["id"], "register_patient", f"Registered patient {first_name} {last_name} {patient_id}")
            return {"status": "ok", "id": patient_id, "message": f"Patient '{first_name} {last_name}' registered successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to register patient: {str(e)}"}
        
@mcp.tool()
async def get_patient(staff_email: str, staff_password: str, patient_id: int):
    """ Retrieve a patient's info by ID. Accessible by: admin, doctor, nurse."""
    staff = await authenticate(staff_email, staff_password)
    if not staff:
        return {"status": "error", "message": "Invalid credentials"}
    if not check_permission(staff["role"], "get_patient"):
        return {"status": "error", "message": "Permission denied"}
    
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM patients WHERE id = ?", (patient_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return {"status": "error", "message": f"Patient {patient_id} not found"}
        await log_action(staff["id"], "get_patient", f"Accessed patient ID {patient_id}")
        return {"status": "ok", "patient": dict(row)}


@mcp.tool()
async def update_patient(
    staff_email: str,
    staff_password: str,
    patient_id: int,
    first_name: str = None,
    last_name: str = None,
    dob: str = None,
    gender: str = None,
    phone: str = None,
    email_address: str = None,
    address: str = None,
    medical_history: str = None,
    allergies: str = None,
    current_diagnosis: str = None,
    assigned_doctor: str = None
):
    """ Update patient info. Accessible by: admin, doctor."""
    staff = await authenticate(staff_email, staff_password)
    if not staff:
        return {"status": "error", "message": "Invalid credentials"}
    if not check_permission(staff["role"], "update_patient"):
        return {"status": "error", "message": "Permission denied"}
    
    async with aiosqlite.connect(DB_PATH) as conn:
        # Check if patient exists
        cursor = await conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        if not await cursor.fetchone():
            return {"status": "error", "message": f"Patient {patient_id} not found"}
        
        fields = {
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
            "gender": gender,
            "phone": phone,
            "email_address": email_address,
            "address": address,
            "medical_history": medical_history,
            "allergies": allergies,
            "current_diagnosis": current_diagnosis,
            "assigned_doctor": assigned_doctor
        }
        updates = [(k, v) for k, v in fields.items() if v is not None]
        if not updates:
            return {"status": "error", "message": "No fields provided to update"}
        
        set_clause = ", ".join(f"{k} = ?" for k, _ in updates)

        set_clause += ", updated_at = ?"
        params = [v for _, v in updates] + [datetime.now().isoformat(), patient_id]

        await conn.execute(f"UPDATE patients SET {set_clause} WHERE id = ?", params)
        await conn.commit()
        await log_action(staff["id"], "update_patient", f"Updated patient ID {patient_id}: {[k for k, _ in updates]}")
        return {"status": "ok", "message": f"Patient {patient_id} updated successfully", "updated_fields": len(updates)}
    

@mcp.tool()
async def delete_patient(staff_email: str, staff_password: str, patient_id: int):
    """Permanently delete a patient record. Accessible by: admin only."""
    staff = await authenticate(staff_email, staff_password)
    if not staff:
        return {"status": "error", "message": "Invalid credentials"}
    if not check_permission(staff["role"], "delete_patient"):
        return {"status": "error", "message": "Permission denied"}
    
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
        if not await cursor.fetchone():
            return {"status": "error", "message": f"Patient {patient_id} not found"}
        
        await conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
        await conn.commit()
        await log_action(staff["id"], "delete_patient", f"Deleted patient ID {patient_id}")
        return {"status": "ok", "message": f"Patient {patient_id} deleted successfully"}
    
@mcp.tool()
async def list_patients(
    staff_email: str,
    staff_password: str,
    assigned_doctor: str = None,
    gender: str = None,
    limit: int = 50,
    offset: int = 0
):
    """
    List patients with optional filters (assigned_doctor, gender).
    Accessible by: admin, doctor, nurse.
    """
    staff = await authenticate(staff_email, staff_password)
    if not staff:
        return {"status": "error", "message": "Invalid credentials"}
    if not check_permission(staff["role"], "list_patients"):
        return {"status": "error", "message": "Permission denied"}
    
    query = "SELECT * FROM patients WHERE 1=1"
    params = []

    if assigned_doctor:
        query += " AND assigned_doctor = ?"
        params.append(assigned_doctor)
    if gender:
        query += " AND gender = ?"
        params.append(gender)

    query += " ORDER BY id ASC LIMIT ? OFFSET ?"
    params += [limit, offset]

    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()
        return {"status": "ok", "count": len(rows), "patients": [dict(row) for row in rows]}   

@mcp.tool()
async def search_patient(staff_email: str, staff_password: str, query: str):
    """
    Search patients by first name, last name, phone or email.
    
    Accessible by: admin, doctor, nurse.
    """
    staff = await authenticate(staff_email, staff_password)
    if not staff:
        return {"status": "error", "message": "Invalid credentials"}
    if not check_permission(staff["role"], "search_patient"):
        return {"status": "error", "message": "Permission denied"}
    
    term = f"%{query}%"
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            """
            SELECT * FROM patients 
            WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ? OR email_address LIKE ?
            ORDER BY id ASC
            """,
            (term, term, term, term)
        )
        rows = await cursor.fetchall()
        return {"status": "ok", "count": len(rows), "patients": [dict(row) for row in rows]}
    

# AUDIT LOG TOOL
@mcp.tool()
async def get_audit_log(admin_email: str, admin_password: str, limit: int = 100):
    """(Admin only) View the last N audit log entries."""
    staff = await authenticate(admin_email, admin_password)
    if not staff:
        return {"status": "error", "message": "Invalid credentials"}
    if staff["role"] != "admin":
        return {"status": "error", "message": "Permission denied"}
    
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.execute(
            "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return {"status": "ok", "logs": [dict(row) for row in rows]}
    

if __name__ == "__main__":
    mcp.run()