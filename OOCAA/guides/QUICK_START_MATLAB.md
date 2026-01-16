# Quick Reference: Calling MATLAB and Returning Pc

## 🎯 **The Answer: It's Already Working!**

Your application is ready to calculate Pc. Here's the complete flow:

## 📊 **Flow Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User Makes API Request                                   │
│    POST /api/cdms/1/calculate-pc/                          │
│    { "method": "multistep", "update_cdm": true }           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Django API View (core/api/views.py)                     │
│    Receives request and calls service                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. pc_calculation_service.py                               │
│    • get_matlab_engine() → Calls setup_matlab.py          │
│    • Loads .env → Gets CARA_MATLAB_PATH                    │
│    • Adds all paths with genpath()                         │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. MATLAB Engine Initialized                               │
│    • Local paths: core/matlab/, Pc3D_Hall_Utils/          │
│    • CARA paths: All DistributedMatlab subdirectories      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Convert CDM Data to MATLAB Format                       │
│    • Position vectors → matlab.double([[x, y, z]])         │
│    • Velocity vectors → matlab.double([[vx, vy, vz]])      │
│    • Covariances → matlab.double(6x6_matrix)               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Call MATLAB CARA Function                               │
│    Pc, out = eng.PcMultiStep(r1, v1, cov1,                │
│                               r2, v2, cov2,                │
│                               HBR, params)                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Return Result                                            │
│    {                                                        │
│      "success": true,                                       │
│      "Pc": 1.234567e-05,                                   │
│      "method": "PcMultiStep",                              │
│      "cdm_id": 1                                           │
│    }                                                        │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 **Quick Start (3 Commands)**

```bash
# 1. Make sure .env is configured
echo "CARA_MATLAB_PATH=C:\Users\peiya\OneDrive\Desktop\Capstone\CARA_Analysis_Tools\DistributedMatlab" > .env

# 2. Test MATLAB connection
python setup_matlab.py

# 3. Test full API
python manage.py runserver
# In another terminal:
python test_pc_calculation.py
```

## 💻 **Code Example: API Call**

```python
import requests

# Calculate Pc for CDM ID 1
response = requests.post(
    "http://localhost:8000/api/cdms/1/calculate-pc/",
    json={"method": "multistep", "update_cdm": True}
)

result = response.json()
pc = result['Pc']  # e.g., 1.23e-05
print(f"Collision Probability: {pc:.2e}")
```

## 📝 **Code Example: Direct Python**

```python
from core.services.pc_calculation_service import calculate_pc_multistep
from core.models import CDM

cdm = CDM.objects.get(id=1)
result = calculate_pc_multistep(cdm)

print(f"Pc: {result['Pc']:.6e}")
```

## 🔧 **What Changed**

**Before:** Hardcoded MATLAB paths in `pc_calculation_service.py`
```python
eng = matlab.engine.start_matlab()
eng.addpath('C:\\Hard\\Coded\\Path')  # ❌ Team can't use this
```

**After:** Environment-based configuration
```python
from setup_matlab import get_matlab_engine
eng = get_matlab_engine()  # ✅ Loads from .env automatically
```

## 🎓 **Key Files**

| File | Purpose |
|------|---------|
| `.env` | Your local MATLAB paths (not committed) |
| `setup_matlab.py` | Loads .env and initializes MATLAB |
| `pc_calculation_service.py` | Calls MATLAB functions, returns Pc |
| `test_pc_calculation.py` | End-to-end test of the whole flow |

## ✅ **You're Done!**

The integration is complete. Your app now:
- ✅ Reads MATLAB paths from `.env`
- ✅ Initializes MATLAB Engine with CARA tools
- ✅ Calculates Pc using NASA algorithms
- ✅ Returns results via API
- ✅ Works for your whole team (everyone uses their own `.env`)

See [HOW_TO_USE_MATLAB_PC.md](HOW_TO_USE_MATLAB_PC.md) for detailed examples and troubleshooting.
