#!/usr/bin/env python3
"""
Comprehensive Backend API Testing for Tourism App with Gamification Features
Tests all endpoints including new user destinations, points system, and rewards
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
        self.test_destination_id = None
        self.test_reward_id = None

    def log_test(self, test_name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name} - PASSED {details}")
        else:
            print(f"❌ {test_name} - FAILED {details}")
        return success

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

    def test_destinations_statistics(self):
        """Test GET /api/destinations/statistics endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/destinations/statistics", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_keys = ["total_destinations", "by_department", "by_category", "accommodation_stats"]
                success = all(key in data for key in required_keys)
                
                # Check if we have data for Boyacá and Cundinamarca
                if success and data.get("by_department"):
                    has_boyaca = "Boyacá" in data["by_department"]
                    has_cundinamarca = "Cundinamarca" in data["by_department"]
                    success = has_boyaca or has_cundinamarca
                
            self.log_test("Destinations Statistics", success, 
                        f"Status: {response.status_code}, Total: {data.get('total_destinations', 0) if success else 0}")
            return success
        except Exception as e:
            self.log_test("Destinations Statistics", False, f"Exception: {str(e)}")
            return False

    def test_destinations_search(self):
        """Test GET /api/destinations/search endpoint with filters"""
        try:
            # Test search with query
            response = requests.get(f"{self.base_url}/api/destinations/search?query=hotel&limit=5", timeout=15)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                
            self.log_test("Destinations Search (query)", success, 
                        f"Status: {response.status_code}, Count: {len(data) if success else 0}")
            
            # Test search with department filter
            response2 = requests.get(f"{self.base_url}/api/destinations/search?department=Boyacá&limit=5", timeout=15)
            success2 = response2.status_code == 200
            
            if success2:
                data2 = response2.json()
                success2 = isinstance(data2, list)
                
            self.log_test("Destinations Search (department filter)", success2, 
                        f"Status: {response2.status_code}, Count: {len(data2) if success2 else 0}")
            
            # Test search with category filter
            response3 = requests.get(f"{self.base_url}/api/destinations/search?category=ALOJAMIENTO HOTELERO&limit=5", timeout=15)
            success3 = response3.status_code == 200
            
            if success3:
                data3 = response3.json()
                success3 = isinstance(data3, list)
                
            self.log_test("Destinations Search (category filter)", success3, 
                        f"Status: {response3.status_code}, Count: {len(data3) if success3 else 0}")
            
            return success and success2 and success3
        except Exception as e:
            self.log_test("Destinations Search", False, f"Exception: {str(e)}")
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
                
            return self.log_test("Travel Trends Analytics", success, 
                        f"Status: {response.status_code}, Users: {data.get('total_users', 0) if success else 0}")
        except Exception as e:
            return self.log_test("Travel Trends Analytics", False, f"Exception: {str(e)}")

    # NEW GAMIFICATION FEATURES TESTS

    def test_initialize_rewards(self):
        """Test POST /api/admin/init-rewards endpoint"""
        try:
            response = requests.post(f"{self.base_url}/api/admin/init-rewards", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = "rewards" in data.get('message', '').lower()
                
            return self.log_test("Initialize Sample Rewards", success, 
                        f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Initialize Sample Rewards", False, f"Exception: {str(e)}")

    def test_get_rewards(self):
        """Test GET /api/rewards endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/rewards", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list) and len(data) > 0
                if success and data:
                    self.test_reward_id = data[0].get('id')  # Store first reward ID
                    
            return self.log_test("Get Rewards Catalog", success, 
                        f"Status: {response.status_code}, Count: {len(data) if success else 0}")
        except Exception as e:
            return self.log_test("Get Rewards Catalog", False, f"Exception: {str(e)}")

    def test_create_user_destination(self):
        """Test POST /api/user-destinations endpoint"""
        if not self.user_id:
            return self.log_test("Create User Destination", False, "No user_id available")
            
        try:
            destination_data = {
                "user_id": self.user_id,
                "name": "Ecolodge Los Pinos Test",
                "description": "Hermoso ecolodge en las montañas de Boyacá con vista panorámica",
                "category": "ALOJAMIENTO RURAL",
                "subcategory": "Ecoturismo",
                "department": "Boyacá",
                "municipality": "Villa de Leyva",
                "address": "Vereda Los Pinos, Km 5 vía Villa de Leyva",
                "phone": "(57) 310-555-0123",
                "email": "info@ecolodgelospinos.com",
                "website": "https://www.ecolodgelospinos.com"
            }
            
            response = requests.post(
                f"{self.base_url}/api/user-destinations",
                json=destination_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "destination_id" in data
                if success:
                    self.test_destination_id = data["destination_id"]
                    
            return self.log_test("Create User Destination", success, 
                        f"Status: {response.status_code}, ID: {self.test_destination_id}")
        except Exception as e:
            return self.log_test("Create User Destination", False, f"Exception: {str(e)}")

    def test_get_user_destinations(self):
        """Test GET /api/user-destinations/{user_id} endpoint"""
        if not self.user_id:
            return self.log_test("Get User Destinations", False, "No user_id available")
            
        try:
            response = requests.get(f"{self.base_url}/api/user-destinations/{self.user_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                
            return self.log_test("Get User Destinations", success, 
                        f"Status: {response.status_code}, Count: {len(data) if success else 0}")
        except Exception as e:
            return self.log_test("Get User Destinations", False, f"Exception: {str(e)}")

    def test_get_approved_destinations(self):
        """Test GET /api/user-destinations/all/approved endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/user-destinations/all/approved", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                success = isinstance(data, list)
                
            return self.log_test("Get Approved Destinations", success, 
                        f"Status: {response.status_code}, Count: {len(data) if success else 0}")
        except Exception as e:
            return self.log_test("Get Approved Destinations", False, f"Exception: {str(e)}")

    def test_get_user_points(self):
        """Test GET /api/points/{user_id} endpoint"""
        if not self.user_id:
            return self.log_test("Get User Points", False, "No user_id available")
            
        try:
            response = requests.get(f"{self.base_url}/api/points/{self.user_id}", timeout=10)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_keys = ["total_points", "level", "transactions"]
                success = all(key in data for key in required_keys)
                points = data.get('total_points', 0)
                level = data.get('level', {}).get('current_level', 'N/A')
                
            return self.log_test("Get User Points", success, 
                        f"Status: {response.status_code}, Points: {points if success else 0}, Level: {level if success else 'N/A'}")
        except Exception as e:
            return self.log_test("Get User Points", False, f"Exception: {str(e)}")

    def test_track_interaction_like(self):
        """Test tracking like interaction for points"""
        if not self.user_id or not self.test_destinations:
            return self.log_test("Track Like Interaction", False, "No user_id or destinations available")
            
        try:
            interaction_data = {
                "user_id": self.user_id,
                "destination_rnt": self.test_destinations[0]["rnt"],
                "action": "like"
            }
            
            response = requests.post(
                f"{self.base_url}/api/users/interactions",
                json=interaction_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            success = response.status_code == 200
            points_earned = 0
            if success:
                data = response.json()
                points_earned = data.get('points_earned', 0)
                success = points_earned == 3  # Like should give 3 points
                
            return self.log_test("Track Like Interaction", success, 
                        f"Status: {response.status_code}, Points earned: {points_earned} (expected 3)")
        except Exception as e:
            return self.log_test("Track Like Interaction", False, f"Exception: {str(e)}")

    def test_track_interaction_view(self):
        """Test tracking view interaction for points"""
        if not self.user_id or not self.test_destinations:
            return self.log_test("Track View Interaction", False, "No user_id or destinations available")
            
        try:
            interaction_data = {
                "user_id": self.user_id,
                "destination_rnt": self.test_destinations[1]["rnt"] if len(self.test_destinations) > 1 else "TEST_RNT",
                "action": "view"
            }
            
            response = requests.post(
                f"{self.base_url}/api/users/interactions",
                json=interaction_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            success = response.status_code == 200
            points_earned = 0
            if success:
                data = response.json()
                points_earned = data.get('points_earned', 0)
                success = points_earned == 1  # View should give 1 point
                
            return self.log_test("Track View Interaction", success, 
                        f"Status: {response.status_code}, Points earned: {points_earned} (expected 1)")
        except Exception as e:
            return self.log_test("Track View Interaction", False, f"Exception: {str(e)}")

    def test_approve_destination(self):
        """Test POST /api/user-destinations/{destination_id}/approve endpoint"""
        if not self.test_destination_id:
            return self.log_test("Approve Destination", False, "No destination_id available")
            
        try:
            # The endpoint expects approved_by parameter
            response = requests.post(
                f"{self.base_url}/api/user-destinations/{self.test_destination_id}/approve?approved_by=admin_test",
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                success = "approved" in data.get('message', '').lower()
                
            return self.log_test("Approve Destination", success, 
                        f"Status: {response.status_code}")
        except Exception as e:
            return self.log_test("Approve Destination", False, f"Exception: {str(e)}")

    def test_redeem_reward(self):
        """Test POST /api/rewards/redeem endpoint"""
        if not self.user_id or not self.test_reward_id:
            return self.log_test("Redeem Reward", False, "No user_id or reward_id available")
            
        try:
            # First check user points
            points_response = requests.get(f"{self.base_url}/api/points/{self.user_id}", timeout=10)
            if points_response.status_code != 200:
                return self.log_test("Redeem Reward", False, "Could not get user points")
            
            user_points = points_response.json().get('total_points', 0)
            
            # Get reward details
            rewards_response = requests.get(f"{self.base_url}/api/rewards", timeout=10)
            if rewards_response.status_code != 200:
                return self.log_test("Redeem Reward", False, "Could not get rewards")
            
            rewards = rewards_response.json()
            target_reward = next((r for r in rewards if r['id'] == self.test_reward_id), None)
            if not target_reward:
                return self.log_test("Redeem Reward", False, "Target reward not found")
            
            required_points = target_reward.get('points_required', 0)
            
            # Try to redeem
            redeem_data = {
                "user_id": self.user_id,
                "reward_id": self.test_reward_id
            }
            
            response = requests.post(
                f"{self.base_url}/api/rewards/redeem",
                json=redeem_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if user_points < required_points:
                # Should get 400 error for insufficient points
                success = response.status_code == 400
                return self.log_test("Redeem Reward", success, 
                            f"Insufficient points test - User: {user_points}, Required: {required_points}, Status: {response.status_code}")
            else:
                # Should succeed
                success = response.status_code == 200
                if success:
                    data = response.json()
                    success = "redeemed" in data.get('message', '').lower()
                return self.log_test("Redeem Reward", success, 
                            f"Status: {response.status_code}, Points spent: {required_points}")
                
        except Exception as e:
            return self.log_test("Redeem Reward", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting Comprehensive Tourism API Tests with Gamification")
        print(f"📍 Testing against: {self.base_url}")
        print("=" * 70)
        
        # Test sequence - order matters for dependent tests
        test_results = []
        
        # 1. Basic API tests (independent)
        print("📋 BASIC API TESTS")
        test_results.append(self.test_health_check())
        test_results.append(self.test_get_destinations())
        test_results.append(self.test_destinations_statistics())
        test_results.append(self.test_destinations_search())
        
        # 2. User setup (needed for gamification features)
        print("\n👤 USER SETUP TESTS")
        test_results.append(self.test_save_user_preferences())
        
        # 3. Gamification setup
        print("\n🎮 GAMIFICATION SETUP TESTS")
        test_results.append(self.test_initialize_rewards())
        test_results.append(self.test_get_rewards())
        
        # 4. User destinations tests
        print("\n📍 USER DESTINATIONS TESTS")
        test_results.append(self.test_create_user_destination())
        test_results.append(self.test_get_user_destinations())
        test_results.append(self.test_get_approved_destinations())
        
        # 5. Points system tests
        print("\n⭐ POINTS SYSTEM TESTS")
        test_results.append(self.test_get_user_points())
        test_results.append(self.test_track_interaction_like())
        test_results.append(self.test_track_interaction_view())
        
        # 6. Admin functions
        print("\n🔧 ADMIN FUNCTIONS TESTS")
        test_results.append(self.test_approve_destination())
        
        # 7. Final points check after all interactions
        print("\n📊 FINAL POINTS CHECK")
        test_results.append(self.test_get_user_points())
        
        # 8. Rewards redemption
        print("\n🎁 REWARDS REDEMPTION TESTS")
        test_results.append(self.test_redeem_reward())
        
        # 9. Recommendations and analytics (depends on user_id)
        print("\n📈 RECOMMENDATIONS & ANALYTICS TESTS")
        test_results.append(self.test_get_recommendations())
        test_results.append(self.test_travel_trends())
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 COMPREHENSIVE TEST SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.user_id:
            print(f"\n🔑 Test User ID: {self.user_id}")
        if self.test_destination_id:
            print(f"📍 Test Destination ID: {self.test_destination_id}")
        if self.test_reward_id:
            print(f"🎁 Test Reward ID: {self.test_reward_id}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 ALL TESTS PASSED! Backend API is fully functional.")
            return True
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} TESTS FAILED - Check details above")
            return False

def main():
    """Main test execution"""
    tester = TourismAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())