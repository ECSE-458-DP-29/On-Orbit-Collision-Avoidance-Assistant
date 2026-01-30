#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'OOCAA.settings')
django.setup()

from core.models import CDM, SpaceObject

# Delete old CDMs to test fresh
CDM.objects.all().delete()
SpaceObject.objects.all().delete()
print("✓ Database cleared")
