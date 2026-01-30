#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OOCAA.settings')
django.setup()

from core.models import CDM

# Get latest CDM
cdms = CDM.objects.all().order_by('-id')
if cdms.exists():
    cdm = cdms.first()
    print(f'✓ CDM Found (ID: {cdm.id})')
    print(f'  CDM ID: {cdm.cdm_id}')
    print(f'  Message ID: {cdm.message_id}')
    print(f'  Creation Date: {cdm.creation_date}')
    print(f'  TCA: {cdm.tca}')
    print(f'  Miss Distance: {cdm.miss_distance_m} m')
    print(f'  Collision Probability: {cdm.collision_probability}')
    print(f'  Obj1 ID: {cdm.obj1_id}')
    print(f'  Obj2 ID: {cdm.obj2_id}')
    
    # Check objects
    if cdm.obj1:
        print(f'  Object 1: {cdm.obj1.object_designator}')
    if cdm.obj2:
        print(f'  Object 2: {cdm.obj2.object_designator}')
else:
    print('✗ No CDM found')
