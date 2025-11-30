#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('contracts.db')
cursor = conn.cursor()

# Get schema
print("=== Table Schema ===")
cursor.execute("PRAGMA table_info(contracts)")
for row in cursor.fetchall():
    print(f"{row[0]}: {row[1]} ({row[2]})")

print("\n=== Sample Data ===")
cursor.execute("SELECT * FROM contracts LIMIT 1")
columns = [description[0] for description in cursor.description]
row = cursor.fetchone()

for col, val in zip(columns, row):
    if col != 'raw_payload':
        print(f"{col}: {val}")

conn.close()
