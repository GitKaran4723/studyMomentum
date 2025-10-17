import sqlite3

conn = sqlite3.connect('instance/goal_tracker.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")
    
    # Show columns for each table
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f"    Columns: {len(columns)}")
    for col in columns[:5]:  # Show first 5 columns
        print(f"      • {col[1]} ({col[2]})")
    if len(columns) > 5:
        print(f"      ... and {len(columns) - 5} more")

conn.close()
