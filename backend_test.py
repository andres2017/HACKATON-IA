#!/usr/bin/env python3
"""
Backend API Testing for Tourism Application
Tests all endpoints using the public URL from frontend/.env
"""

import requests
import json
import sys
from datetime import datetime
import uuid

class TourismAPITester:
    def __init__(self, base_url="https://48e7611f-d1de-4fe5-8fee-46c75b1124f5.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.test_destinations = []

    def log_test(self, test_name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name} - PASSED")
        else:
            print(f"❌ {test_name} - FAILED")
        
        if details:
            print(f"   Details: {details}")
        print()

    def test_health_check(self):
        """Test GET /api/health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            success = response.status_code == 200 and response.json().get("status") == "healthy"
            self.log_test("Health Check", success, f"Status: {response.status_code}, Response: {response.json()}")
            return success
        except Exception as e:
            self.log_test("Health Check", False, f"Exception: {str(e)}")
            return False

    def test_get_destinations(self):
        """Test GET /api/destinations endpoint"""
        try:
            # Test basic destinations fetch
            response = requests.get(f"{self.base_url}/api/destinations?limit=5", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list) and len(data) > 0
                if success:
                    self.test_destinations = data[:3]  # Store some destinations for later tests
                    # Check if destinations have required fields
                    first_dest = data[0]
                    required_fields = ['rnt', 'categoria', 'nomdep', 'nombre_muni', 'razon_social']
                    has_required_fields = all(field in first_dest for field in required_fields)
                    success = success and has_required_fields
                    
                self.log_test("Get Destinations", success, 
                            f"Status: {response.status_code}, Count: {len(data) if success else 0}, "
                            f"Sample: {data[0].get('razon_social', 'N/A') if data else 'None'}")
            else:
                self.log_test("Get Destinations", False, f"Status: {response.status_code}")
            
            return success
        except Exception as e:
            self.log_test("Get Destinations", False, f"Exception: {str(e)}")
            return False

    def test_save_user_preferences(self):
        """Test POST /api/users/preferences endpoint"""
        try:
            test_preferences = {
                "name": "Juan Test",
                "email": "test@example.com",
                "preferred_categories": ["ALOJAMIENTO HOTELERO"],
                "preferred_departments": ["BOYACÁ"],
                "age_range": "26-35",
                "travel_style": "aventura"
            }
            
            response = requests.post(
                f"{self.base_url}/api/users/preferences",
                json=test_preferences,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "user_id" in data and "message" in data
                if success:
                    self.user_id = data["user_id"]
                    
            self.log_test("Save User Preferences", success, 
                        f"Status: {response.status_code}, User ID: {self.user_id}")
            return success
        except Exception as e:
            self.log_test("Save User Preferences", False, f"Exception: {str(e)}")
            return False

    def test_track_user_interaction(self):
        """Test POST /api/users/interactions endpoint"""
        if not self.user_id or not self.test_destinations:
            self.log_test("Track User Interaction", False, "No user_id or destinations available")
            return False
            
        try:
            test_interaction = {
                "user_id": self.user_id,
                "destination_rnt": self.test_destinations[0]["rnt"],
                "action": "like"
            }
            
            response = requests.post(
                f"{self.base_url}/api/users/interactions",
                json=test_interaction,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "message" in data
                
            self.log_test("Track User Interaction", success, 
                        f"Status: {response.status_code}, Action: like")
            return success
        except Exception as e:
            self.log_test("Track User Interaction", False, f"Exception: {str(e)}")
            return False

    def test_get_recommendations(self):
        """Test GET /api/recommendations/{user_id} endpoint"""
        if not self.user_id:
            self.log_test("Get Recommendations", False, "No user_id available")
            return False
            
        try:
            response = requests.get(f"{self.base_url}/api/recommendations/{self.user_id}?limit=5", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                
            self.log_test("Get Recommendations", success, 
                        f"Status: {response.status_code}, Count: {len(data) if success else 0}")
            return success
        except Exception as e:
            self.log_test("Get Recommendations", False, f"Exception: {str(e)}")
            return False

    def test_popular_destinations(self):
        """Test GET /api/analytics/popular-destinations endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/analytics/popular-destinations?limit=5", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                
            self.log_test("Popular Destinations Analytics", success, 
                        f"Status: {response.status_code}, Count: {len(data) if success else 0}")
            return success
        except Exception as e:
            self.log_test("Popular Destinations Analytics", False, f"Exception: {str(e)}")
            return False

    def test_travel_trends(self):
        """Test GET /api/analytics/trends endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/analytics/trends", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_keys = ["department_trends", "category_trends", "travel_style_trends", 
                               "total_users", "total_interactions"]
                success = all(key in data for key in required_keys)
                
            self.log_test("Travel Trends Analytics", success, 
                        f"Status: {response.status_code}, Users: {data.get('total_users', 0) if success else 0}")
            return success
        except Exception as e:
            self.log_test("Travel Trends Analytics", False, f"Exception: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting Tourism API Tests")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test sequence - order matters for dependent tests
        test_results = []
        
        # 1. Health check (independent)
        test_results.append(self.test_health_check())
        
        # 2. Get destinations (independent, needed for interactions)
        test_results.append(self.test_get_destinations())
        
        # 3. Save user preferences (needed for recommendations and interactions)
        test_results.append(self.test_save_user_preferences())
        
        # 4. Track user interaction (depends on user_id and destinations)
        test_results.append(self.test_track_user_interaction())
        
        # 5. Get recommendations (depends on user_id)
        test_results.append(self.test_get_recommendations())
        
        # 6. Analytics endpoints (independent)
        test_results.append(self.test_popular_destinations())
        test_results.append(self.test_travel_trends())
        
        # Print summary
        print("=" * 60)
        print(f"📊 TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL TESTS PASSED!")
            return True
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} TESTS FAILED")
            return False

def main():
    """Main test execution"""
    tester = TourismAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())