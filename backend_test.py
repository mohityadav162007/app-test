import requests
import sys
import json
from datetime import datetime

class TMSAPITester:
    def __init__(self, base_url="https://cargosync-13.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.created_trip_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    headers.pop('Content-Type', None)
                    response = requests.post(url, files=files, headers=headers)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.content else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                self.failed_tests.append({
                    "test": name,
                    "expected": expected_status,
                    "actual": response.status_code,
                    "response": response.text
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failed_tests.append({
                "test": name,
                "error": str(e)
            })
            return False, {}

    def test_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "shrisanwariyaroadlines@gmail.com", "password": "Sanwariya_1228"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            print(f"✅ Login successful, user role: {response.get('user', {}).get('role')}")
            return True
        return False

    def test_get_me(self):
        """Test get current user"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_create_trip(self):
        """Test trip creation with auto-generated Trip ID"""
        trip_data = {
            "loading_date": "2026-01-15",
            "unloading_date": "2026-01-16",
            "vehicle_number": "GJ01AB1234",
            "driver_mobile": "9876543210",
            "is_own_vehicle": False,
            "motor_owner_name": "Test Motor Owner",
            "motor_owner_mobile": "9876543211",
            "gadi_bhada": 50000,
            "gadi_advance": 20000,
            "party_name": "Test Party",
            "party_mobile": "9876543212",
            "party_freight": 75000,
            "party_advance": 25000,
            "tds": 2000,
            "from_location": "Mumbai",
            "to_location": "Delhi",
            "weight": "10 tons",
            "himmali": "Electronics",
            "remarks": "Test trip creation",
            "status": "Loaded"
        }
        
        success, response = self.run_test(
            "Create Trip",
            "POST",
            "trips",
            200,
            data=trip_data
        )
        
        if success and 'trip_id' in response:
            self.created_trip_id = response['trip_id']
            print(f"✅ Trip created with ID: {self.created_trip_id}")
            
            # Verify Trip ID format (YEAR_INCREMENT)
            current_year = datetime.now().year
            if self.created_trip_id.startswith(f"{current_year}_"):
                print(f"✅ Trip ID format correct: {self.created_trip_id}")
            else:
                print(f"❌ Trip ID format incorrect: {self.created_trip_id}")
                
            # Verify balance calculations
            expected_gadi_balance = 50000 - 20000  # 30000
            expected_party_balance = 75000 - 25000  # 50000
            
            if response.get('gadi_balance') == expected_gadi_balance:
                print(f"✅ Gadi balance calculated correctly: {response.get('gadi_balance')}")
            else:
                print(f"❌ Gadi balance incorrect. Expected: {expected_gadi_balance}, Got: {response.get('gadi_balance')}")
                
            if response.get('party_balance') == expected_party_balance:
                print(f"✅ Party balance calculated correctly: {response.get('party_balance')}")
            else:
                print(f"❌ Party balance incorrect. Expected: {expected_party_balance}, Got: {response.get('party_balance')}")
        
        return success

    def test_get_trips(self):
        """Test get all trips"""
        success, response = self.run_test(
            "Get All Trips",
            "GET",
            "trips",
            200
        )
        if success:
            print(f"✅ Retrieved {len(response)} trips")
        return success

    def test_get_trip_details(self):
        """Test get specific trip details"""
        if not self.created_trip_id:
            print("❌ No trip ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get Trip Details",
            "GET",
            f"trips/{self.created_trip_id}",
            200
        )
        return success

    def test_update_trip(self):
        """Test trip update"""
        if not self.created_trip_id:
            print("❌ No trip ID available for testing")
            return False
            
        update_data = {
            "status": "In-Transit",
            "remarks": "Updated via API test"
        }
        
        success, response = self.run_test(
            "Update Trip",
            "PUT",
            f"trips/{self.created_trip_id}",
            200,
            data=update_data
        )
        return success

    def test_party_analytics(self):
        """Test party analytics (admin only)"""
        success, response = self.run_test(
            "Party Analytics",
            "GET",
            "analytics/parties",
            200
        )
        if success:
            print(f"✅ Retrieved analytics for {len(response)} parties")
        return success

    def test_motor_owner_analytics(self):
        """Test motor owner analytics (admin only)"""
        success, response = self.run_test(
            "Motor Owner Analytics",
            "GET",
            "analytics/motor-owners",
            200
        )
        if success:
            print(f"✅ Retrieved analytics for {len(response)} motor owners")
        return success

    def test_export_trips(self):
        """Test Excel export functionality"""
        success, response = self.run_test(
            "Export Trips",
            "GET",
            "export/trips",
            200
        )
        return success

    def test_pod_upload(self):
        """Test POD upload functionality"""
        if not self.created_trip_id:
            print("❌ No trip ID available for testing")
            return False
            
        # Create a dummy file for testing
        test_file_content = b"Test POD file content"
        files = {'file': ('test_pod.txt', test_file_content, 'text/plain')}
        
        success, response = self.run_test(
            "POD Upload",
            "POST",
            f"trips/{self.created_trip_id}/pod",
            200,
            files=files
        )
        return success

    def test_pod_download(self):
        """Test POD download functionality"""
        if not self.created_trip_id:
            print("❌ No trip ID available for testing")
            return False
            
        success, response = self.run_test(
            "POD Download",
            "GET",
            f"trips/{self.created_trip_id}/pod",
            200
        )
        return success

    def test_own_vehicle_trip(self):
        """Test creating trip with own vehicle (no motor owner fields)"""
        trip_data = {
            "loading_date": "2026-01-17",
            "vehicle_number": "GJ01CD5678",
            "driver_mobile": "9876543213",
            "is_own_vehicle": True,
            "party_name": "Test Party 2",
            "party_mobile": "9876543214",
            "party_freight": 60000,
            "party_advance": 15000,
            "from_location": "Pune",
            "to_location": "Bangalore",
            "status": "Loaded"
        }
        
        success, response = self.run_test(
            "Create Own Vehicle Trip",
            "POST",
            "trips",
            200,
            data=trip_data
        )
        
        if success:
            # Verify no gadi_balance for own vehicle
            if response.get('gadi_balance') is None:
                print("✅ Own vehicle trip has no gadi_balance (correct)")
            else:
                print(f"❌ Own vehicle trip should not have gadi_balance, got: {response.get('gadi_balance')}")
        
        return success

def main():
    print("🚀 Starting TMS API Testing...")
    print("=" * 50)
    
    tester = TMSAPITester()
    
    # Authentication Tests
    if not tester.test_login():
        print("❌ Login failed, stopping tests")
        return 1
    
    tester.test_get_me()
    
    # Trip Management Tests
    tester.test_create_trip()
    tester.test_get_trips()
    tester.test_get_trip_details()
    tester.test_update_trip()
    tester.test_own_vehicle_trip()
    
    # POD Tests
    tester.test_pod_upload()
    tester.test_pod_download()
    
    # Analytics Tests (Admin only)
    tester.test_party_analytics()
    tester.test_motor_owner_analytics()
    
    # Export Tests
    tester.test_export_trips()
    
    # Print Results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.failed_tests:
        print("\n❌ Failed Tests:")
        for test in tester.failed_tests:
            print(f"  - {test}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())