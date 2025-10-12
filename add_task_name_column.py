"""
Add task_name column to tasks table
"""
import sqlite3
from pathlib import Path

def add_task_name_column():
    db_path = Path('instance/goal_tracker.db')
    
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'task_name' in columns:
            print("✅ task_name column already exists")
            return
        
        # Add the column
        print("Adding task_name column to tasks table...")
        cursor.execute("ALTER TABLE tasks ADD COLUMN task_name VARCHAR(200)")
        conn.commit()
        print("✅ Successfully added task_name column")
        
        # Verify
        cursor.execute("PRAGMA table_info(tasks)")
        columns = cursor.fetchall()
        print("\n📋 Updated tasks table structure:")
        for col in columns:
            print(f"  {col[1]}: {col[2]}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    add_task_name_column()
