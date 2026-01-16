# How to Use MATLAB Functions and Return Pc

This guide explains how to call MATLAB CARA functions and return collision probability (Pc) through your application.

## Architecture Overview

```
User Request (API/Frontend)
    ↓
Django API View (core/api/views.py)
    ↓
Pc Calculation Service (core/services/pc_calculation_service.py)
    ↓
Setup MATLAB (setup_matlab.py) → Loads .env config
    ↓
MATLAB Engine + CARA Functions
    ↓
Return Pc Result
```

## Quick Start

### 1. **Configure Your Environment** (One-time setup)

Make sure your `.env` file is configured:
```bash
cd OOCAA
# If .env doesn't exist, copy from template
copy .env.example .env
```

Edit `.env`:
```env
CARA_MATLAB_PATH=C:\Users\peiya\OneDrive\Desktop\Capstone\CARA_Analysis_Tools\DistributedMatlab
```

### 2. **Test MATLAB Connection**

```bash
python setup_matlab.py
```

This verifies:
- ✅ MATLAB Engine is installed
- ✅ Local MATLAB paths are accessible
- ✅ CARA Analysis Tools path is loaded
- ✅ Functions are available

### 3. **Start Your Django Server**

```bash
python manage.py runserver
```

### 4. **Use the API to Calculate Pc**

The service is already integrated! Here's how it works:

## API Usage Examples

### Example 1: Calculate Pc for a Single CDM

**Python (using requests):**
```python
import requests

# 1. Create a CDM with conjunction data
cdm_data = {
    "tca": "2024-12-25T14:30:00Z",
    "obj1_position_x": 6678000.0,
    "obj1_position_y": 0.0,
    "obj1_position_z": 0.0,
    "obj1_velocity_x": 0.0,
    "obj1_velocity_y": 7500.0,
    "obj1_velocity_z": 0.0,
    "obj1_covariance_matrix": [
        [100.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 100.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 100.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.01, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.01, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.01]
    ],
    "obj2_position_x": 6678050.0,
    "obj2_position_y": 0.0,
    "obj2_position_z": 30.0,
    "obj2_velocity_x": 0.0,
    "obj2_velocity_y": 7500.5,
    "obj2_velocity_z": 0.1,
    "obj2_covariance_matrix": [
        [200.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 200.0, 0.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 200.0, 0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.02, 0.0, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.02, 0.0],
        [0.0, 0.0, 0.0, 0.0, 0.0, 0.02]
    ],
    "hard_body_radius": 10.0,
    "obj1_data": {...},
    "obj2_data": {...}
}

response = requests.post("http://localhost:8000/api/cdms/", json=cdm_data)
cdm = response.json()
cdm_id = cdm['id']

# 2. Calculate Pc using CARA MATLAB tools
calc_request = {
    "method": "multistep",  # or "circle", "dilution"
    "update_cdm": True       # Save Pc to database
}

response = requests.post(
    f"http://localhost:8000/api/cdms/{cdm_id}/calculate-pc/",
    json=calc_request,
    timeout=60
)

result = response.json()
print(f"Pc: {result['Pc']}")  # e.g., 1.23e-05
```

**cURL:**
```bash
# Calculate Pc for CDM ID 1
curl -X POST http://localhost:8000/api/cdms/1/calculate-pc/ \
  -H "Content-Type: application/json" \
  -d '{"method": "multistep", "update_cdm": true}'
```

**Response:**
```json
{
  "success": true,
  "Pc": 1.234567e-05,
  "method": "PcMultiStep",
  "cdm_id": 1,
  "updated": true,
  "details": {
    "miss_distance": 58.31,
    "calculation_time_ms": 245
  }
}
```

### Example 2: Batch Calculate Pc for Multiple CDMs

```python
batch_request = {
    "cdm_ids": [1, 2, 3, 4, 5],
    "method": "multistep",
    "update_cdms": True
}

response = requests.post(
    "http://localhost:8000/api/cdms/batch-calculate-pc/",
    json=batch_request
)

result = response.json()
# {
#   "total": 5,
#   "successful": 5,
#   "failed": 0,
#   "results": [
#     {"cdm_id": 1, "Pc": 1.23e-05, "success": true},
#     {"cdm_id": 2, "Pc": 4.56e-06, "success": true},
#     ...
#   ]
# }
```

## Direct Python Usage (Without API)

You can also use the service directly in your Python code:

```python
from core.services.pc_calculation_service import calculate_pc_multistep
from core.models import CDM

# Get a CDM from database
cdm = CDM.objects.get(id=1)

# Calculate Pc
result = calculate_pc_multistep(cdm)

print(f"Pc: {result['Pc']:.6e}")
print(f"Method: {result['method']}")
print(f"Success: {result['success']}")
```

## Available MATLAB Functions

The service provides three main calculation methods:

### 1. **PcMultiStep** (Recommended)
```python
result = calculate_pc_multistep(cdm)
```
- Automatically selects best algorithm (2D-Pc, 2D-Nc, or 3D-Nc)
- Most robust for all conjunction geometries
- Returns detailed calculation metadata

### 2. **PcCircle** (Fast screening)
```python
result = calculate_pc_circle(cdm)
```
- Fast 2D circular integration
- Good for bulk processing/screening
- Less robust for edge cases

### 3. **PcDilution** (Analysis)
```python
result = calculate_pc_dilution(cdm)
```
- Analyzes covariance dilution effects
- Returns `PcMax`, `PcOne`, dilution flag
- Useful for conjunction analysis

## How It Works Internally

### Step 1: Service initializes MATLAB
```python
# In pc_calculation_service.py
from setup_matlab import get_matlab_engine as get_configured_matlab_engine

def get_matlab_engine():
    global _matlab_engine
    if _matlab_engine is None:
        # This automatically:
        # - Loads .env file
        # - Adds local MATLAB paths
        # - Adds CARA_MATLAB_PATH with genpath
        _matlab_engine = get_configured_matlab_engine(add_cara_path=True)
    return _matlab_engine
```

### Step 2: Service converts CDM data to MATLAB format
```python
def cdm_to_matlab_params(cdm):
    import matlab
    
    # Convert to MATLAB arrays
    r1 = matlab.double([[cdm.obj1_position_x, cdm.obj1_position_y, cdm.obj1_position_z]])
    v1 = matlab.double([[cdm.obj1_velocity_x, cdm.obj1_velocity_y, cdm.obj1_velocity_z]])
    cov1 = matlab.double(cdm.obj1_covariance_matrix)
    # ... same for obj2 ...
    
    return {'r1': r1, 'v1': v1, 'cov1': cov1, ...}
```

### Step 3: Service calls MATLAB function
```python
eng = get_matlab_engine()

# Call CARA function
Pc, out = eng.PcMultiStep(
    matlab_params['r1'],
    matlab_params['v1'],
    matlab_params['cov1'],
    matlab_params['r2'],
    matlab_params['v2'],
    matlab_params['cov2'],
    matlab_params['HBR'],
    params_struct,
    nargout=2
)
```

### Step 4: Return result
```python
return {
    'Pc': float(Pc),
    'method': 'PcMultiStep',
    'details': {...},
    'success': True
}
```

## Running the Full Test

Test the complete integration:

```bash
# Terminal 1: Start Django server
python manage.py runserver

# Terminal 2: Run test script
python test_pc_calculation.py
```

This will:
1. ✅ Create sample CDMs with realistic conjunction data
2. ✅ Calculate Pc using CARA MATLAB functions
3. ✅ Verify results are stored in database
4. ✅ Test multiple calculation methods
5. ✅ Test batch processing

## Troubleshooting

### "CARA_MATLAB_PATH not set"
- Check your `.env` file exists in the `OOCAA/` directory
- Verify the path is correct and points to `DistributedMatlab`

### "MATLAB function not found"
- Run `python setup_matlab.py` to verify paths
- Check that CARA_MATLAB_PATH contains the CARA functions

### First calculation is slow (5-10 seconds)
- This is normal! MATLAB Engine initialization takes time
- Subsequent calculations will be much faster (~100-500ms)
- The engine stays loaded for the lifetime of the Django process

### "MATLAB Engine not installed"
- Install from your MATLAB installation:
  ```bash
  cd "C:\Program Files\MATLAB\R2025b\extern\engines\python"
  python setup.py install
  ```

## Performance Tips

1. **Keep Django server running** - MATLAB Engine persists across requests
2. **Use batch processing** - Process multiple CDMs in one request
3. **Cache results** - Pc is stored in CDM, no need to recalculate
4. **Use PcCircle for screening** - Faster for initial triage

## Next Steps

- ✅ Configure `.env` with your CARA path
- ✅ Run `python setup_matlab.py` to test
- ✅ Start Django server
- ✅ Run `python test_pc_calculation.py`
- ✅ Integrate into your frontend/workflow

Your application is now ready to calculate collision probabilities using NASA's CARA tools! 🚀
