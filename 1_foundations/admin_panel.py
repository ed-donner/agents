# admin_panel.py
import sqlite3
import pandas as pd

conn = sqlite3.connect("career_bot.db")

print("=== Contacts ===")
print(pd.read_sql("SELECT * FROM contacts", conn))

print("\n=== Unknown Questions ===")
print(pd.read_sql("SELECT * FROM unknown_questions WHERE resolved = FALSE", conn))

print("\n=== Stats ===")
print(pd.read_sql("SELECT COUNT(*) as total_conversations FROM conversations", conn))

conn.close()
