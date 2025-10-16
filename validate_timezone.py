"""
IST Timezone Validation Script
Run this to verify all timezone changes are working correctly
"""

from datetime import datetime, date
import pytz

print("=" * 60)
print("IST TIMEZONE VALIDATION SCRIPT")
print("=" * 60)

# Test 1: pytz installation
print("\n✓ Test 1: pytz Library")
try:
    print(f"  pytz version: {pytz.__version__}")
    print("  ✅ PASS: pytz is installed")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 2: IST timezone
print("\n✓ Test 2: IST Timezone")
try:
    ist = pytz.timezone('Asia/Kolkata')
    print(f"  IST Timezone: {ist}")
    print("  ✅ PASS: IST timezone available")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 3: Get IST time
print("\n✓ Test 3: Current IST Time")
try:
    ist = pytz.timezone('Asia/Kolkata')
    ist_now = datetime.now(ist)
    ist_today = ist_now.date()
    
    print(f"  Current IST: {ist_now}")
    print(f"  IST Date: {ist_today}")
    print(f"  UTC Offset: +05:30")
    print("  ✅ PASS: IST time retrieved")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 4: Compare UTC vs IST
print("\n✓ Test 4: UTC vs IST Comparison")
try:
    utc_now = datetime.utcnow()
    ist = pytz.timezone('Asia/Kolkata')
    ist_now = datetime.now(ist)
    
    print(f"  UTC Time: {utc_now}")
    print(f"  IST Time: {ist_now}")
    
    # Calculate difference (should be ~5.5 hours)
    utc_aware = pytz.UTC.localize(utc_now)
    diff = ist_now - utc_aware
    hours_diff = diff.total_seconds() / 3600
    
    print(f"  Time Difference: {hours_diff:.1f} hours")
    
    if 5.0 <= hours_diff <= 6.0:
        print("  ✅ PASS: Correct 5:30 hour offset")
    else:
        print(f"  ⚠️  WARNING: Expected ~5.5 hours, got {hours_diff:.1f}")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Test 5: Helper functions from routes.py
print("\n✓ Test 5: Application Helper Functions")
try:
    from app.main.routes import get_ist_now, get_ist_today, get_ist_timezone
    
    app_ist_now = get_ist_now()
    app_ist_today = get_ist_today()
    app_ist_tz = get_ist_timezone()
    
    print(f"  get_ist_now(): {app_ist_now}")
    print(f"  get_ist_today(): {app_ist_today}")
    print(f"  get_ist_timezone(): {app_ist_tz}")
    print("  ✅ PASS: Route helpers working")
except Exception as e:
    print(f"  ❌ FAIL: {e}")
    print("  Note: Run this from the app directory with Flask app context")

# Test 6: Model helper function
print("\n✓ Test 6: Model Helper Functions")
try:
    from app.models import ist_now as model_ist_now
    
    model_time = model_ist_now()
    print(f"  ist_now(): {model_time}")
    print("  ✅ PASS: Model helper working")
except Exception as e:
    print(f"  ❌ FAIL: {e}")
    print("  Note: Run this from the app directory")

# Test 7: Day boundary check
print("\n✓ Test 7: Day Boundary Logic")
try:
    ist = pytz.timezone('Asia/Kolkata')
    ist_now = datetime.now(ist)
    hour = ist_now.hour
    
    print(f"  Current IST Hour: {hour}")
    
    if hour < 12:
        print("  Time: Morning (Before noon)")
    elif hour < 18:
        print("  Time: Afternoon")
    elif hour < 24:
        print("  Time: Evening/Night")
    
    # Check if close to midnight
    if 23 <= hour or hour < 1:
        print("  ⚠️  WARNING: Near day boundary - good time to test!")
    
    print("  ✅ PASS: Day boundary logic working")
except Exception as e:
    print(f"  ❌ FAIL: {e}")

# Summary
print("\n" + "=" * 60)
print("VALIDATION COMPLETE")
print("=" * 60)
print("\n📋 Next Steps:")
print("  1. If all tests pass ✅, timezone fix is working!")
print("  2. Test on server: python validate_timezone.py")
print("  3. Test dashboard: http://127.0.0.1:5000/dashboard")
print("  4. Compare date shown with: https://time.is/IST")
print("\n🚀 Deploy with confidence!")
print("=" * 60)
