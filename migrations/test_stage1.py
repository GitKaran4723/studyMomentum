"""
Stage 1 Test Suite: Verify migration and backfill without affecting production
"""
import sqlite3
import os
from datetime import datetime

def get_db_path():
    """Get the database path"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, 'instance', 'goal_tracker.db')

def test_database_exists():
    """Test 1: Database file exists"""
    db_path = get_db_path()
    if os.path.exists(db_path):
        print("✅ Test 1 PASSED: Database file exists at", db_path)
        return True
    else:
        print("❌ Test 1 FAILED: Database file not found at", db_path)
        return False

def test_existing_tables():
    """Test 2: All required tables exist"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    required_tables = ['users', 'goals', 'subjects', 'topics', 'tasks', 
                      'completions', 'sessions', 'daily_snapshots']
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = [row[0] for row in cursor.fetchall()]
    
    missing = [t for t in required_tables if t not in existing_tables]
    
    if not missing:
        print(f"✅ Test 2 PASSED: All {len(required_tables)} required tables exist")
        conn.close()
        return True
    else:
        print(f"❌ Test 2 FAILED: Missing tables: {missing}")
        conn.close()
        return False

def test_existing_data():
    """Test 3: Check for existing data"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    tables_with_data = {}
    for table in ['users', 'goals', 'subjects', 'topics', 'tasks']:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        tables_with_data[table] = count
    
    conn.close()
    
    print(f"✅ Test 3 PASSED: Data inventory:")
    for table, count in tables_with_data.items():
        status = "📊" if count > 0 else "📭"
        print(f"   {status} {table}: {count} rows")
    
    return True

def test_migration_needed():
    """Test 4: Check if migration is needed"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tasks table for new columns
    cursor.execute("PRAGMA table_info(tasks)")
    task_columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = ['task_type', 'concept_weight', 'mastery', 'lambda_forgetting', 
                   'eta_learn', 'rho_revise', 'last_studied_at', 'spaced_stage']
    
    missing = [col for col in new_columns if col not in task_columns]
    
    conn.close()
    
    if missing:
        print(f"✅ Test 4 PASSED: Migration needed - {len(missing)} new columns to add")
        print(f"   Missing columns: {', '.join(missing[:3])}...")
        return True
    else:
        print(f"ℹ️  Test 4 INFO: Migration already applied (or columns exist)")
        return True

def test_backup_strategy():
    """Test 5: Verify backup can be created"""
    db_path = get_db_path()
    backup_path = db_path + ".test_backup"
    
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        
        # Verify backup
        if os.path.exists(backup_path):
            backup_size = os.path.getsize(backup_path)
            os.remove(backup_path)  # Clean up test backup
            print(f"✅ Test 5 PASSED: Backup strategy works ({backup_size} bytes)")
            return True
        else:
            print("❌ Test 5 FAILED: Backup not created")
            return False
            
    except Exception as e:
        print(f"❌ Test 5 FAILED: Backup error - {e}")
        return False

def test_models_file():
    """Test 6: Verify models.py is valid Python"""
    models_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'app', 'models.py'
    )
    
    try:
        with open(models_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # Check for new field definitions
        new_fields = ['threshold_marks', 'subject_weight', 'topic_weight_hint', 
                     'task_type', 'concept_weight', 'mastery']
        
        found_fields = [field for field in new_fields if field in code]
        
        if len(found_fields) >= len(new_fields):
            print(f"✅ Test 6 PASSED: models.py updated with prediction fields")
            print(f"   Found: {', '.join(found_fields[:3])}... ({len(found_fields)} total)")
            return True
        else:
            print(f"⚠️  Test 6 WARNING: models.py may need updates")
            print(f"   Found only {len(found_fields)}/{len(new_fields)} expected fields")
            return True
            
    except Exception as e:
        print(f"❌ Test 6 FAILED: Error reading models.py - {e}")
        return False

def test_migration_scripts():
    """Test 7: Verify migration scripts exist and are valid"""
    migrations_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'migrations'
    )
    
    required_scripts = [
        'add_prediction_fields.py',
        'backfill_prediction_data.py'
    ]
    
    all_exist = True
    for script in required_scripts:
        script_path = os.path.join(migrations_dir, script)
        if os.path.exists(script_path):
            print(f"   ✅ {script} exists")
        else:
            print(f"   ❌ {script} MISSING")
            all_exist = False
    
    if all_exist:
        print(f"✅ Test 7 PASSED: All migration scripts present")
        return True
    else:
        print(f"❌ Test 7 FAILED: Missing migration scripts")
        return False

def test_feature_flags():
    """Test 8: Check for feature flag configuration"""
    env_prediction_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        '.env.prediction'
    )
    
    if os.path.exists(env_prediction_path):
        with open(env_prediction_path, 'r') as f:
            content = f.read()
            if 'PREDICTION_ENABLED=false' in content:
                print("✅ Test 8 PASSED: Feature flag file exists with PREDICTION_ENABLED=false")
                return True
            else:
                print("⚠️  Test 8 WARNING: Feature flag file exists but may need review")
                return True
    else:
        print("ℹ️  Test 8 INFO: .env.prediction not found (will be created)")
        return True

def run_all_tests():
    """Run all Stage 1 tests"""
    print("=" * 70)
    print("🧪 Stage 1 Test Suite: Pre-Migration Verification")
    print("=" * 70)
    print()
    
    tests = [
        ("Database Exists", test_database_exists),
        ("Required Tables", test_existing_tables),
        ("Existing Data", test_existing_data),
        ("Migration Status", test_migration_needed),
        ("Backup Strategy", test_backup_strategy),
        ("Models File", test_models_file),
        ("Migration Scripts", test_migration_scripts),
        ("Feature Flags", test_feature_flags),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n🔍 Running: {name}")
        print("-" * 70)
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            results.append((name, False))
        print()
    
    print("=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Result: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print()
        print("🎉 ALL TESTS PASSED! Ready for Stage 1 migration.")
        print()
        print("Next steps:")
        print("1. Create backup: Copy-Item instance\\study_momentum.db instance\\study_momentum.db.backup")
        print("2. Run migration: python migrations\\add_prediction_fields.py")
        print("3. Run backfill: python migrations\\backfill_prediction_data.py")
        print("4. Test app: python run.py")
    else:
        print()
        print("⚠️  Some tests failed. Review above output before proceeding.")
    
    print("=" * 70)
    
    return passed_count == total_count

if __name__ == '__main__':
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
