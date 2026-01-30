#!/usr/bin/env python
import os
import json
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OOCAA.settings')
django.setup()

from core.models import CDM, SpaceObject
from core.services.cdm_service import parse_cdm_json
from core.services.pc_calculation_service import calculate_pc_multistep, update_cdm_with_pc_result
from django.db import transaction

# Load the CDM file
with open('CDM_CASSIOPE_event4_2.json', 'r') as f:
    data = json.load(f)

print("=" * 60)
print("TESTING CDM UPLOAD AND PC CALCULATION")
print("=" * 60)

# Clear database
print("\n1. Clearing database...")
CDM.objects.all().delete()
SpaceObject.objects.all().delete()
print("   ✓ Database cleared")

# Test parse_cdm_json
print("\n2. Parsing CDM JSON...")
try:
    with transaction.atomic():
        cdm, obj1, obj2 = parse_cdm_json(data[0])
        print(f"   ✓ CDM parsed successfully")
        print(f"     - CDM ID: {cdm.cdm_id}")
        print(f"     - CDM DB ID: {cdm.id}")
        print(f"     - Object 1: {obj1.object_designator}")
        print(f"     - Object 2: {obj2.object_designator}")
        print(f"     - TCA: {cdm.tca}")
        print(f"     - Miss Distance: {cdm.miss_distance_m} m")
        print(f"     - Collision Probability: {cdm.collision_probability}")
except Exception as e:
    print(f"   ✗ Error parsing CDM: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Check database
print("\n3. Checking database...")
db_cdm = CDM.objects.first()
if db_cdm:
    print(f"   ✓ CDM found in database")
    print(f"     - DB ID: {db_cdm.id}")
    print(f"     - CDM ID: {db_cdm.cdm_id}")
    print(f"     - Current Pc: {db_cdm.collision_probability}")
else:
    print(f"   ✗ CDM NOT found in database!")
    exit(1)

# Test PC calculation
print("\n4. Calculating Pc...")
try:
    result = calculate_pc_multistep(cdm, None)
    print(f"   ✓ Pc calculation completed")
    print(f"     - Success: {result.get('success')}")
    print(f"     - Pc: {result.get('pc')}")
    print(f"     - Method: {result.get('method')}")
    
    if result.get('success'):
        print("\n5. Updating CDM with Pc result...")
        update_cdm_with_pc_result(cdm, result, save=True)
        
        # Refresh from database
        cdm.refresh_from_db()
        print(f"   ✓ CDM updated")
        print(f"     - New Pc: {cdm.collision_probability}")
    else:
        print(f"   ⚠ Pc calculation unsuccessful: {result.get('error')}")
        
except Exception as e:
    print(f"   ✗ Error calculating Pc: {e}")
    import traceback
    traceback.print_exc()

# Final check
print("\n6. Final database check...")
final_cdm = CDM.objects.first()
if final_cdm:
    print(f"   ✓ CDM persisted in database")
    print(f"     - CDM ID: {final_cdm.cdm_id}")
    print(f"     - DB ID: {final_cdm.id}")
    print(f"     - Pc: {final_cdm.collision_probability}")
    print(f"     - Total CDMs in DB: {CDM.objects.count()}")
else:
    print(f"   ✗ CDM NOT in database!")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
