"""Test script for CARA Pc calculation integration.

This script demonstrates how to:
1. Create a CDM with complete state vectors and covariances
2. Calculate Pc using CARA MATLAB tools via the API
3. Validate the results

Run this after starting the Django development server:
    python manage.py runserver

Then run this test script:
    python test_pc_calculation.py
"""

import requests
import json
from datetime import datetime, timezone

# API base URL
BASE_URL = "http://localhost:8000/api"

def create_sample_cdm():
    """Create a sample CDM with realistic conjunction data.
    
    This uses sample data from a typical LEO conjunction scenario.
    Position in meters, velocity in m/s, covariance in m^2 and m^2/s.
    """
    
    # Sample conjunction data (converted from km to meters)
    cdm_data = {
        "tca": "2024-12-25T14:30:00Z",
        
        # Object 1 (Primary satellite)
        "obj1_data": {
            "object_designator": "12345",
            "object_name": "TEST-SAT-1",
            "object_type": "PAYLOAD",
            "operator_organization": "TEST-ORG",
            "maneuverable": True
        },
        
        # Object 1 State Vector (ECI frame, meters and m/s)
        "obj1_position_x": 6678000.0,  # ~300 km altitude
        "obj1_position_y": 0.0,
        "obj1_position_z": 0.0,
        "obj1_velocity_x": 0.0,
        "obj1_velocity_y": 7500.0,  # ~7.5 km/s orbital velocity
        "obj1_velocity_z": 0.0,
        
        # Object 1 Covariance Matrix (6x6, ECI frame, m^2 and m^2/s)
        # Simplified diagonal covariance for testing
        "obj1_covariance_matrix": [
            [100.0, 0.0, 0.0, 0.0, 0.0, 0.0],      # Position X variance
            [0.0, 100.0, 0.0, 0.0, 0.0, 0.0],      # Position Y variance
            [0.0, 0.0, 100.0, 0.0, 0.0, 0.0],      # Position Z variance
            [0.0, 0.0, 0.0, 0.01, 0.0, 0.0],       # Velocity X variance
            [0.0, 0.0, 0.0, 0.0, 0.01, 0.0],       # Velocity Y variance
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.01]        # Velocity Z variance
        ],
        
        # Object 2 (Debris)
        "obj2_data": {
            "object_designator": "67890",
            "object_name": "DEBRIS-FRAGMENT",
            "object_type": "DEBRIS",
            "operator_organization": "UNKNOWN",
            "maneuverable": False
        },
        
        # Object 2 State Vector (slightly offset for close approach)
        "obj2_position_x": 6678050.0,  # 50m offset
        "obj2_position_y": 0.0,
        "obj2_position_z": 30.0,       # 30m offset
        "obj2_velocity_x": 0.0,
        "obj2_velocity_y": 7500.5,     # Slightly different velocity
        "obj2_velocity_z": 0.1,
        
        # Object 2 Covariance Matrix
        "obj2_covariance_matrix": [
            [200.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 200.0, 0.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 200.0, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.02, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.02, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, 0.02]
        ],
        
        # Hard body radius (combined sphere, meters)
        "hard_body_radius": 10.0,  # 10m radius
        
        # Miss distance (for reference)
        "miss_distance_m": 58.31,  # ~58m miss distance
    }
    
    return cdm_data


def test_create_cdm_and_calculate_pc():
    """Test creating a CDM and calculating Pc."""
    
    print("=" * 80)
    print("CARA Pc Calculation Integration Test")
    print("=" * 80)
    print()
    
    # Step 1: Create a CDM
    print("Step 1: Creating CDM with state vectors and covariances...")
    cdm_data = create_sample_cdm()
    
    response = requests.post(f"{BASE_URL}/cdms/", json=cdm_data)
    
    if response.status_code != 201:
        print(f"❌ Failed to create CDM: {response.status_code}")
        print(response.json())
        return False
    
    cdm = response.json()
    cdm_id = cdm['id']
    print(f"✅ CDM created successfully (ID: {cdm_id})")
    print(f"   TCA: {cdm['tca']}")
    print(f"   Miss Distance: {cdm['miss_distance_m']:.2f} m")
    print(f"   HBR: {cdm['hard_body_radius']} m")
    print()
    
    # Step 2: Calculate Pc using PcMultiStep (default method)
    print("Step 2: Calculating Pc using CARA PcMultiStep...")
    print("   (First calculation may take 5-10 seconds to initialize MATLAB...)")
    
    calc_request = {
        "method": "multistep",
        "update_cdm": True
    }
    
    response = requests.post(
        f"{BASE_URL}/cdms/{cdm_id}/calculate-pc/",
        json=calc_request,
        timeout=60  # Allow 60 seconds for MATLAB startup
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to calculate Pc: {response.status_code}")
        print(response.json())
        return False
    
    result = response.json()
    
    if not result.get('success'):
        print(f"❌ Pc calculation failed")
        print(json.dumps(result, indent=2))
        return False
    
    print(f"✅ Pc calculation successful!")
    print(f"   Pc: {result['Pc']:.6e}")
    print(f"   Method: {result['method']}")
    print(f"   CDM Updated: {result['updated']}")
    print()
    
    # Step 3: Verify CDM was updated
    print("Step 3: Verifying CDM was updated with Pc...")
    
    response = requests.get(f"{BASE_URL}/cdms/{cdm_id}/")
    
    if response.status_code != 200:
        print(f"❌ Failed to retrieve CDM: {response.status_code}")
        return False
    
    updated_cdm = response.json()
    
    if updated_cdm['collision_probability'] is not None:
        print(f"✅ CDM updated successfully")
        print(f"   Stored Pc: {updated_cdm['collision_probability']}")
        print(f"   Method: {updated_cdm['collision_probability_method']}")
    else:
        print(f"⚠️  CDM not updated with Pc")
    
    print()
    
    # Step 4: Test PcCircle method
    print("Step 4: Testing alternative method (PcCircle)...")
    
    calc_request = {
        "method": "circle",
        "update_cdm": False  # Don't overwrite the stored value
    }
    
    response = requests.post(
        f"{BASE_URL}/cdms/{cdm_id}/calculate-pc/",
        json=calc_request
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"✅ PcCircle calculation successful")
            print(f"   Pc: {result['Pc']:.6e}")
        else:
            print(f"⚠️  PcCircle calculation failed: {result.get('detail', 'Unknown error')}")
    else:
        print(f"⚠️  PcCircle request failed: {response.status_code}")
    
    print()
    
    # Step 5: Test batch calculation
    print("Step 5: Testing batch Pc calculation...")
    
    # Create a second CDM
    cdm_data_2 = create_sample_cdm()
    cdm_data_2['obj1_data']['object_designator'] = "11111"
    cdm_data_2['obj2_data']['object_designator'] = "22222"
    cdm_data_2['miss_distance_m'] = 100.0
    
    response = requests.post(f"{BASE_URL}/cdms/", json=cdm_data_2)
    if response.status_code == 201:
        cdm_2 = response.json()
        cdm_2_id = cdm_2['id']
        
        # Batch calculate for both CDMs
        batch_request = {
            "cdm_ids": [cdm_id, cdm_2_id],
            "method": "multistep",
            "update_cdms": False
        }
        
        response = requests.post(
            f"{BASE_URL}/cdms/batch-calculate-pc/",
            json=batch_request
        )
        
        if response.status_code == 200:
            batch_result = response.json()
            print(f"✅ Batch calculation completed")
            print(f"   Total: {batch_result['total']}")
            print(f"   Successful: {batch_result['successful']}")
            print(f"   Failed: {batch_result['failed']}")
            
            for r in batch_result['results']:
                if r.get('success'):
                    print(f"   CDM {r['cdm_id']}: Pc = {r['Pc']:.6e}")
        else:
            print(f"⚠️  Batch calculation failed: {response.status_code}")
    
    print()
    print("=" * 80)
    print("Test completed successfully! ✅")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    try:
        success = test_create_cdm_and_calculate_pc()
        if not success:
            print("\n⚠️  Some tests failed. Check the output above for details.")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server.")
        print("   Make sure the Django server is running:")
        print("   python manage.py runserver")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
