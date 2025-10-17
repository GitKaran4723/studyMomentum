"""
Stage 1 Backfill: Set safe defaults for prediction fields
- Equal subject weights per goal (summing to 1.0)
- Equal concept weights per subject (from subject_weight)
- Virtual tasks for subjects with no tasks
"""
import sqlite3
from datetime import datetime
import os

def get_db_path():
    """Get the database path"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'instance', 'goal_tracker.db')


def backfill_subject_weights():
    """
    For each goal, if all subjects have NULL weight,
    assign equal weights summing to 1.0
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📊 Backfilling Subject Weights...")
    
    try:
        # Get all goals with their subjects
        cursor.execute("""
            SELECT g.goal_id, COUNT(s.subject_id) as subject_count
            FROM goals g
            LEFT JOIN subjects s ON s.goal_id = g.goal_id
            GROUP BY g.goal_id
            HAVING subject_count > 0
        """)
        
        goals = cursor.fetchall()
        
        for goal_id, subject_count in goals:
            # Check if all subjects for this goal have NULL weight
            cursor.execute("""
                SELECT COUNT(*) FROM subjects 
                WHERE goal_id = ? AND subject_weight IS NOT NULL
            """, (goal_id,))
            
            non_null_count = cursor.fetchone()[0]
            
            if non_null_count == 0:
                # All NULL - assign equal weights
                equal_weight = 1.0 / subject_count
                
                cursor.execute("""
                    UPDATE subjects 
                    SET subject_weight = ?
                    WHERE goal_id = ?
                """, (equal_weight, goal_id))
                
                print(f"  ✅ Goal {goal_id}: Set {subject_count} subjects to {equal_weight:.4f} each")
            else:
                print(f"  ⏭️  Goal {goal_id}: Already has weighted subjects")
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Error: {e}")
        return False
        
    finally:
        conn.close()


def backfill_concept_weights():
    """
    For each subject with tasks, if concept_weight is NULL,
    distribute subject_weight equally over existing tasks
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n📝 Backfilling Task Concept Weights...")
    
    try:
        # Get subjects with their tasks
        cursor.execute("""
            SELECT s.subject_id, s.subject_weight, COUNT(t.task_id) as task_count
            FROM subjects s
            LEFT JOIN topics top ON top.subject_id = s.subject_id
            LEFT JOIN tasks t ON t.topic_id = top.topic_id
            WHERE s.subject_weight IS NOT NULL
            GROUP BY s.subject_id, s.subject_weight
            HAVING task_count > 0
        """)
        
        subjects = cursor.fetchall()
        
        for subject_id, subject_weight, task_count in subjects:
            if subject_weight is None:
                continue
                
            # Check if tasks have NULL concept_weight
            cursor.execute("""
                SELECT COUNT(*) FROM tasks t
                JOIN topics top ON top.topic_id = t.topic_id
                WHERE top.subject_id = ? AND t.concept_weight IS NOT NULL
            """, (subject_id,))
            
            non_null_count = cursor.fetchone()[0]
            
            if non_null_count == 0:
                # All NULL - assign equal weights
                equal_weight = subject_weight / task_count
                
                cursor.execute("""
                    UPDATE tasks
                    SET concept_weight = ?
                    WHERE topic_id IN (
                        SELECT topic_id FROM topics WHERE subject_id = ?
                    )
                """, (equal_weight, subject_id))
                
                print(f"  ✅ Subject {subject_id}: Set {task_count} tasks to {equal_weight:.6f} each")
            else:
                print(f"  ⏭️  Subject {subject_id}: Already has weighted tasks")
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Error: {e}")
        return False
        
    finally:
        conn.close()


def create_virtual_tasks():
    """
    For subjects with no tasks, create one virtual task:
    - task_name: "Subject Core Pack"
    - task_type: 'learn'
    - concept_weight: subject_weight
    - t_est_hours: 10
    - mastery: 0.2 (baseline)
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🎯 Creating Virtual Tasks for Empty Subjects...")
    
    try:
        # Find subjects with no tasks
        cursor.execute("""
            SELECT s.subject_id, s.name, s.subject_weight, s.goal_id
            FROM subjects s
            WHERE s.subject_weight IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM topics top
                JOIN tasks t ON t.topic_id = top.topic_id
                WHERE top.subject_id = s.subject_id
            )
        """)
        
        empty_subjects = cursor.fetchall()
        
        virtual_count = 0
        
        for subject_id, subject_name, subject_weight, goal_id in empty_subjects:
            # Create a virtual topic for this subject
            cursor.execute("""
                INSERT INTO topics (subject_id, topic_name, created_at)
                VALUES (?, ?, ?)
            """, (subject_id, f"{subject_name} - Core", datetime.now()))
            
            topic_id = cursor.lastrowid
            
            # Create the virtual task
            cursor.execute("""
                INSERT INTO tasks (
                    topic_id, task_name, task_type, 
                    concept_weight, t_est_hours, mastery,
                    lambda_forgetting, eta_learn, rho_revise,
                    spaced_stage, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                topic_id,
                "Subject Core Pack (Virtual)",
                'learn',
                subject_weight,  # Full subject weight
                10.0,            # Default 10 hours
                0.2,             # Baseline mastery
                0.04,            # Default forgetting rate
                0.8,             # Default learning efficiency
                0.35,            # Default revision efficiency
                0,               # Not in spaced repetition yet
                datetime.now()
            ))
            
            print(f"  ✅ Created virtual task for '{subject_name}' (weight: {subject_weight:.4f})")
            virtual_count += 1
        
        if virtual_count == 0:
            print("  ℹ️  No subjects need virtual tasks")
        else:
            print(f"\n  📦 Created {virtual_count} virtual task(s)")
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"  ❌ Error: {e}")
        return False
        
    finally:
        conn.close()


def verify_backfill():
    """Verify backfill completed successfully"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 Verifying Backfill...")
    
    try:
        # Check subject weights
        cursor.execute("""
            SELECT 
                g.goal_id,
                g.goal_name,
                COUNT(s.subject_id) as subject_count,
                SUM(s.subject_weight) as total_weight
            FROM goals g
            LEFT JOIN subjects s ON s.goal_id = g.goal_id
            WHERE s.subject_weight IS NOT NULL
            GROUP BY g.goal_id, g.goal_name
        """)
        
        print("\n  📊 Subject Weight Distribution:")
        for goal_id, goal_name, subject_count, total_weight in cursor.fetchall():
            status = "✅" if abs(total_weight - 1.0) < 0.01 else "⚠️"
            print(f"  {status} Goal '{goal_name}': {subject_count} subjects, total weight = {total_weight:.4f}")
        
        # Check tasks per subject
        cursor.execute("""
            SELECT 
                s.name,
                COUNT(t.task_id) as task_count,
                SUM(t.concept_weight) as total_concept_weight
            FROM subjects s
            LEFT JOIN topics top ON top.subject_id = s.subject_id
            LEFT JOIN tasks t ON t.topic_id = top.topic_id
            WHERE s.subject_weight IS NOT NULL
            GROUP BY s.subject_id, s.name
        """)
        
        print("\n  📝 Task Concept Weight Distribution:")
        for subject_name, task_count, total_concept_weight in cursor.fetchall():
            if task_count > 0 and total_concept_weight:
                print(f"  ✅ Subject '{subject_name}': {task_count} task(s), total = {total_concept_weight:.6f}")
            else:
                print(f"  ⚠️  Subject '{subject_name}': No tasks")
        
        # Check virtual tasks
        cursor.execute("""
            SELECT COUNT(*) FROM tasks 
            WHERE task_name LIKE '%Virtual%'
        """)
        virtual_count = cursor.fetchone()[0]
        print(f"\n  🎯 Virtual Tasks: {virtual_count}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Verification error: {e}")
        return False
        
    finally:
        conn.close()


def main():
    """Run all backfill operations"""
    print("=" * 60)
    print("🚀 Stage 1 Backfill: Setting Safe Defaults")
    print("=" * 60)
    
    success = True
    
    # Step 1: Subject weights
    if not backfill_subject_weights():
        success = False
    
    # Step 2: Concept weights
    if not backfill_concept_weights():
        success = False
    
    # Step 3: Virtual tasks
    if not create_virtual_tasks():
        success = False
    
    # Step 4: Verify
    if not verify_backfill():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Backfill completed successfully!")
        print("=" * 60)
        print("\n💡 Next Steps:")
        print("   1. Check .env file for PREDICTION_ENABLED=false")
        print("   2. Restart the app and verify existing flows work")
        print("   3. Ready for Stage 2 (prediction service layer)")
    else:
        print("❌ Backfill completed with errors")
        print("=" * 60)
    
    return success


if __name__ == '__main__':
    main()
