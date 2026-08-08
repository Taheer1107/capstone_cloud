import requests
import json

# API endpoint
BASE_URL = "http://127.0.0.1:8002"

print("="*70)
print("TESTING HEALTHCARE COST PREDICTION API")
print("="*70)

# Test 1: Health check
print("\n1. Testing health endpoint...")
try:
    response = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Prediction with all parameters
print("\n2. Testing prediction endpoint...")
params = {
    "procedure": "Appendectomy",
    "specialty": "General Surgery",
    "hospital_type": "Private",
    "city_tier": "Tier-1",
    "age": 45,
    "pmjay_flag": 0,
    "ward_type": "private"
}

print(f"   Request parameters:")
for key, value in params.items():
    print(f"     {key}: {value}")

try:
    response = requests.get(f"{BASE_URL}/predict", params=params)
    print(f"\n   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ SUCCESS!")
        print(f"\n   Response:")
        print(json.dumps(result, indent=2))
        
        if "prediction" in result:
            pred = result["prediction"]
            print(f"\n   {'='*60}")
            print(f"   PREDICTED COST: ₹{pred['final_cost_inr']:,.2f}")
            print(f"   Base Cost: ₹{pred['base_cost_inr']:,.2f}")
            print(f"   Ward Multiplier: {pred['ward_multiplier']}x")
            print(f"   {'='*60}")
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   {json.dumps(response.json(), indent=2)}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: With PMJAY discount
print("\n3. Testing with PMJAY discount...")
params_pmjay = {
    "procedure": "Knee Replacement",
    "specialty": "Orthopedics",
    "hospital_type": "Private",
    "city_tier": "Tier-2",
    "age": 65,
    "pmjay_flag": 1,
    "ward_type": "general"
}

try:
    response = requests.get(f"{BASE_URL}/predict", params=params_pmjay)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✓ SUCCESS!")
        
        if "prediction" in result:
            pred = result["prediction"]
            print(f"\n   {'='*60}")
            print(f"   PREDICTED COST: ₹{pred['final_cost_inr']:,.2f}")
            print(f"   Base Cost: ₹{pred['base_cost_inr']:,.2f}")
            print(f"   PMJAY Applied: {result['inputs']['pmjay_applied']}")
            print(f"   {'='*60}")
    else:
        print(f"   ❌ Error: {response.status_code}")
        print(f"   {json.dumps(response.json(), indent=2)}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Missing required field (should fail gracefully)
print("\n4. Testing validation (missing specialty)...")
params_invalid = {
    "procedure": "Appendectomy",
    # "specialty": "General Surgery",  # MISSING!
    "hospital_type": "Private",
    "city_tier": "Tier-1",
    "age": 45,
    "pmjay_flag": 0,
    "ward_type": "private"
}

try:
    response = requests.get(f"{BASE_URL}/predict", params=params_invalid)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 422:
        print(f"   ✓ Validation working correctly!")
    
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "="*70)
print("TESTING COMPLETE")
print("="*70)