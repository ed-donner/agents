"""
Checks that the Supabase database schema is applied correctly.
Run this once after setting up your Supabase project.

Usage:
    uv run python scripts/check_supabase.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL", "")
key = os.environ.get("SUPABASE_SERVICE_KEY", "")

if not url or not key:
    print("❌  SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    sys.exit(1)

from supabase import create_client
db = create_client(url, key)

TABLES = ["posts", "campaigns", "analytics"]
all_ok = True

print("🔍 Checking Supabase tables...\n")
for table in TABLES:
    try:
        result = db.table(table).select("*").limit(1).execute()
        print(f"  ✅ {table} — ok ({len(result.data)} rows sampled)")
    except Exception as e:
        print(f"  ❌ {table} — MISSING: {e}")
        all_ok = False

print()
if all_ok:
    print("✅ All tables present. Database is ready.")
else:
    print("❌ Some tables are missing.")
    print("\nFix: Open your Supabase project → SQL Editor → paste and run supabase_schema.sql")
    print("     https://supabase.com/dashboard → your project → SQL Editor → New query")
    sys.exit(1)
