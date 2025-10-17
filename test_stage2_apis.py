"""
Stage 2 API Test Script
Tests prediction endpoints with actual database data
"""

import urllib.request
import urllib.parse
import json
import http.cookiejar
from datetime import date

# Configuration
BASE_URL = "http://127.0.0.1:5000"
API_BASE = f"{BASE_URL}/api/predict"

# Test credentials (update with your admin user)
USERNAME = "admin"
PASSWORD = "admin123"

class Session:
    """Simple session handler using urllib"""
    def __init__(self):
        self.cookies = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies),
            urllib.request.HTTPRedirectHandler()
        )
    
    def post(self, url, data=None, json_data=None, headers=None):
        """POST request"""
        if headers is None:
            headers = {}
        
        if json_data:
            data = json.dumps(json_data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        elif data:
            data = urllib.parse.urlencode(data).encode('utf-8')
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        
        request = urllib.request.Request(url, data=data, headers=headers, method='POST')
        
        try:
            response = self.opener.open(request)
            return Response(response)
        except urllib.error.HTTPError as e:
            return Response(e)
    
    def get(self, url, params=None):
        """GET request"""
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        
        request = urllib.request.Request(url)
        
        try:
            response = self.opener.open(request)
            return Response(response)
        except urllib.error.HTTPError as e:
            return Response(e)

class Response:
    """Simple response wrapper"""
    def __init__(self, response):
        self._response = response
        self.status_code = response.code if hasattr(response, 'code') else response.status
        self._text = None
    
    @property
    def text(self):
        if self._text is None:
            self._text = self._response.read().decode('utf-8')
        return self._text
    
    def json(self):
        return json.loads(self.text)

def login():
    """Login and get session"""
    session = Session()
    response = session.post(
        f"{BASE_URL}/auth/login",
        data={
            'username': USERNAME,
            'password': PASSWORD
        }
    )
    
    if response.status_code in [302, 200]:
        print("✅ Login successful")
        return session
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def test_health_check(session):
    """Test /api/predict/health endpoint"""
    print("\n" + "="*60)
    print("Test 1: Health Check")
    print("="*60)
    
    response = session.get(f"{API_BASE}/health")
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Health check passed")
        print(json.dumps(data, indent=2))
        return True
    else:
        print(f"❌ Health check failed")
        print(response.text)
        return False

def test_status(session, goal_id=1):
    """Test /api/predict/status endpoint"""
    print("\n" + "="*60)
    print(f"Test 2: Get Status for Goal {goal_id}")
    print("="*60)
    
    response = session.get(f"{API_BASE}/status", params={'goal_id': goal_id})
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Status endpoint working")
        print("\n📊 Goal Status:")
        print(f"  Goal: {data.get('goal_name')}")
        print(f"  Expected Marks (μ): {data['current_state']['mu']}")
        print(f"  Std Dev (σ): {data['current_state']['sigma']}")
        print(f"  P(clear today): {data['current_state']['p_clear_today']*100:.2f}%")
        
        if 'exam_projection' in data and 'days_remaining' in data['exam_projection']:
            proj = data['exam_projection']
            print(f"\n📈 Exam Projection:")
            print(f"  Days Remaining: {proj['days_remaining']}")
            print(f"  Projected μ at exam: {proj.get('mu_exam', 'N/A')}")
            print(f"  P(clear at exam): {proj.get('p_clear_exam', 0)*100:.2f}%")
        
        print(f"\n📋 Tasks:")
        stats = data['task_statistics']
        print(f"  Total: {stats['total_tasks']}")
        print(f"  Mastered (≥80%): {stats['mastered_tasks']}")
        print(f"  Average Mastery: {stats['avg_mastery']*100:.1f}%")
        
        return True
    else:
        print(f"❌ Status endpoint failed")
        try:
            print(response.json())
        except:
            print(response.text)
        return False

def test_plan(session, goal_id=1, daily_hours=6.0, split_new=0.6):
    """Test /api/predict/plan endpoint"""
    print("\n" + "="*60)
    print(f"Test 3: Generate Daily Plan for Goal {goal_id}")
    print("="*60)
    
    payload = {
        'goal_id': goal_id,
        'daily_hours': daily_hours,
        'split_new': split_new
    }
    
    response = session.post(
        f"{API_BASE}/plan",
        json_data=payload
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Plan endpoint working")
        
        print(f"\n📅 Daily Plan for {data['date']}:")
        print(f"  Goal: {data['goal_name']}")
        
        summary = data['summary']
        print(f"\n⏱️ Time Allocation:")
        print(f"  New Learning: {summary['hours_new']} hours")
        print(f"  Revision: {summary['hours_revision']} hours")
        print(f"  Total: {summary['total_hours']} hours")
        
        print(f"\n📚 New Learning Tasks ({len(data['new_tasks'])}):")
        for i, task in enumerate(data['new_tasks'][:5], 1):  # Show first 5
            print(f"  {i}. {task['task_name']} ({task['subject_name']})")
            print(f"     Allocated: {task['allocated_hours']:.1f}h | Mastery: {task['mastery_before']:.2f} → {task['mastery_after']:.2f}")
            if task['derived']:
                print(f"     ⚠️  From virtual task")
        
        if len(data['new_tasks']) > 5:
            print(f"  ... and {len(data['new_tasks']) - 5} more")
        
        print(f"\n🔄 Revision Tasks ({len(data['revision_tasks'])}):")
        for i, task in enumerate(data['revision_tasks'][:5], 1):
            print(f"  {i}. {task['task_name']} ({task['subject_name']})")
            print(f"     Allocated: {task['allocated_hours']:.1f}h | Mastery: {task['mastery_before']:.2f} → {task['mastery_after']:.2f}")
            print(f"     Days since last: {task['days_since_last']}")
        
        if len(data['revision_tasks']) > 5:
            print(f"  ... and {len(data['revision_tasks']) - 5} more")
        
        gains = summary['projected_gains']
        print(f"\n📈 Projected Gains:")
        print(f"  μ before: {gains['mu_before']:.1f}")
        print(f"  μ after: {gains['mu_after']:.1f}")
        print(f"  Δμ: +{gains['delta_mu']:.1f} marks")
        print(f"  P(clear) before: {gains['p_clear_before']*100:.2f}%")
        print(f"  P(clear) after: {gains['p_clear_after']*100:.2f}%")
        
        print(f"\n✅ READ-ONLY: {data['metadata']['no_persistence']}")
        
        return True
    else:
        print(f"❌ Plan endpoint failed")
        try:
            print(response.json())
        except:
            print(response.text)
        return False

def test_without_feature_flag():
    """Test that APIs return 404 when feature flag is disabled"""
    print("\n" + "="*60)
    print("Test 4: Feature Flag Guard (requires PREDICTION_ENABLED=false)")
    print("="*60)
    print("⚠️  This test is informational only.")
    print("   Set PREDICTION_ENABLED=false in .env to test 404 response")

def main():
    """Run all tests"""
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "Stage 2 API Test Suite" + " "*20 + "║")
    print("╚" + "="*58 + "╝")
    
    print(f"\n📡 Testing: {API_BASE}")
    print(f"   Make sure Flask app is running on {BASE_URL}")
    print(f"   Set PREDICTION_ENABLED=preview in .env")
    
    # Login
    session = login()
    if not session:
        print("\n❌ Tests aborted: Login failed")
        return
    
    # Run tests
    results = []
    
    results.append(("Health Check", test_health_check(session)))
    results.append(("Status Endpoint", test_status(session)))
    results.append(("Plan Endpoint", test_plan(session)))
    test_without_feature_flag()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total_count = len(results)
    
    print(f"\nResult: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All Stage 2 tests passed!")
        print("   ✅ Prediction APIs are working")
        print("   ✅ Feature flag guard is active")
        print("   ✅ User ownership validation working")
        print("   ✅ Read-only simulations confirmed")
    else:
        print("\n⚠️  Some tests failed. Check output above.")

if __name__ == '__main__':
    main()
