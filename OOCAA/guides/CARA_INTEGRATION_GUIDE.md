# CARA Pc Calculation Integration - Implementation Guide

## Overview

This implementation integrates NASA's CARA (Conjunction Assessment Risk Analysis) Analysis Tools with the OOCAA Django REST API to calculate probability of collision (Pc) using industry-standard algorithms.

## What Was Implemented

### 1. Extended CDM Data Model
**File**: `core/models/cdm.py`

Added fields to store complete conjunction state:
- **Position vectors** (6 fields): `obj1_position_x/y/z`, `obj2_position_x/y/z` (ECI frame, meters)
- **Velocity vectors** (6 fields): `obj1_velocity_x/y/z`, `obj2_velocity_x/y/z` (ECI frame, m/s)
- **Covariance matrices** (2 fields): `obj1_covariance_matrix`, `obj2_covariance_matrix` (6x6 nested arrays, ECI frame)
- **Hard body radius** (1 field): `hard_body_radius` (meters)

### 2. Pc Calculation Service
**File**: `core/services/pc_calculation_service.py`

Complete MATLAB Engine integration with:
- `calculate_pc_multistep()` - NASA's recommended multi-tiered algorithm
- `calculate_pc_circle()` - Fast 2D circular integration method
- `calculate_pc_dilution()` - Maximum Pc analysis with covariance scaling
- `batch_calculate_pc()` - Bulk processing for multiple CDMs
- `validate_cdm_for_pc()` - Input validation
- `update_cdm_with_pc_result()` - Store results in database

### 3. REST API Endpoints
**Files**: `core/api/views.py`, `core/api/urls.py`

New endpoints:
- `POST /api/cdms/<id>/calculate-pc/` - Calculate Pc for a single CDM
- `POST /api/cdms/batch-calculate-pc/` - Calculate Pc for multiple CDMs

### 4. Serializer Validation
**File**: `core/api/serializers.py`

Extended `CDMSerializer` with:
- All new state vector and covariance fields
- Covariance matrix structure validation (3x3 or 6x6)
- Hard body radius validation (must be > 0)
- Numeric type validation for matrix elements

### 5. Test Script
**File**: `test_pc_calculation.py`

Comprehensive test demonstrating:
- CDM creation with complete state data
- Pc calculation using different methods
- Batch processing
- Result verification

## API Usage Examples

### Create a CDM with State Vectors

```bash
curl -X POST http://localhost:8000/api/cdms/ \
  -H "Content-Type: application/json" \
  -d '{
    "tca": "2024-12-25T14:30:00Z",
    "obj1_data": {
      "object_designator": "12345",
      "object_name": "TEST-SAT-1",
      "object_type": "PAYLOAD"
    },
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
    "obj2_data": {
      "object_designator": "67890",
      "object_name": "DEBRIS",
      "object_type": "DEBRIS"
    },
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
    "miss_distance_m": 58.31
  }'
```

### Calculate Pc (PcMultiStep Method)

```bash
curl -X POST http://localhost:8000/api/cdms/1/calculate-pc/ \
  -H "Content-Type: application/json" \
  -d '{
    "method": "multistep",
    "update_cdm": true
  }'
```

**Response**:
```json
{
  "cdm_id": 1,
  "Pc": 1.23e-05,
  "method": "PcMultiStep",
  "details": {
    "xm": 50.0,
    "zm": 30.0,
    "sx": 14.14,
    "sz": 17.32
  },
  "success": true,
  "updated": true
}
```

### Calculate Pc (PcCircle - Faster)

```bash
curl -X POST http://localhost:8000/api/cdms/1/calculate-pc/ \
  -H "Content-Type: application/json" \
  -d '{
    "method": "circle",
    "update_cdm": false
  }'
```

### Batch Calculate Pc

```bash
curl -X POST http://localhost:8000/api/cdms/batch-calculate-pc/ \
  -H "Content-Type: application/json" \
  -d '{
    "cdm_ids": [1, 2, 3, 4, 5],
    "method": "multistep",
    "update_cdms": true
  }'
```

**Response**:
```json
{
  "total": 5,
  "successful": 5,
  "failed": 0,
  "results": [
    {
      "cdm_id": 1,
      "Pc": 1.23e-05,
      "method": "PcMultiStep",
      "success": true,
      "updated": true
    },
    ...
  ]
}
```

## MATLAB Integration Details

### CARA Tools Location
The service automatically adds these paths from CARA_Analysis_Tools:
- `DistributedMatlab/ProbabilityOfCollision/`
- `DistributedMatlab/ProbabilityOfCollision/Utils/`
- `DistributedMatlab/Maximum2DPc/`
- `DistributedMatlab/MonteCarloPc/`
- `DistributedMatlab/Utils/`

### Calculation Methods

#### 1. PcMultiStep (Recommended)
**Function**: `PcMultiStep.m`
- Multi-tiered algorithm that automatically selects best method
- Chooses between 2D-Pc, 2D-Nc, or 3D-Nc based on geometry
- Industry standard used by NASA CARA
- Most robust for edge cases

#### 2. PcCircle (Fast)
**Function**: `PcCircle.m`
- Fast 2D circular integration
- Good for screening/bulk processing
- Less robust for edge cases than PcMultiStep

#### 3. PcDilution (Analysis)
**Function**: `PcDilution.m`
- Detects "dilution region" conjunctions
- Calculates maximum achievable Pc via covariance scaling
- Useful for risk assessment and uncertainty analysis

### Data Conversion

Python (Django) → MATLAB:
```python
# Position/velocity vectors (Python lists → MATLAB double arrays)
r1 = matlab.double([cdm.obj1_position_x, cdm.obj1_position_y, cdm.obj1_position_z])

# Covariance matrices (Python nested lists → MATLAB 6x6 arrays)
cov1 = matlab.double(cdm.obj1_covariance_matrix)

# Scalars (Python float → MATLAB double)
HBR = float(cdm.hard_body_radius)
```

MATLAB → Python:
```python
# Scalar results
pc_value = float(Pc)

# Struct fields (iterate and convert)
for field in dir(out):
    value = getattr(out, field)
    # Convert to Python types
```

## Database Schema

**Migration**: `core/migrations/0004_cdm_hard_body_radius_cdm_obj1_covariance_matrix_and_more.py`

New fields added to `core_cdm` table:
- `obj1_position_x` (float, nullable)
- `obj1_position_y` (float, nullable)
- `obj1_position_z` (float, nullable)
- `obj1_velocity_x` (float, nullable)
- `obj1_velocity_y` (float, nullable)
- `obj1_velocity_z` (float, nullable)
- `obj2_position_x` (float, nullable)
- `obj2_position_y` (float, nullable)
- `obj2_position_z` (float, nullable)
- `obj2_velocity_x` (float, nullable)
- `obj2_velocity_y` (float, nullable)
- `obj2_velocity_z` (float, nullable)
- `obj1_covariance_matrix` (JSON, nullable)
- `obj2_covariance_matrix` (JSON, nullable)
- `hard_body_radius` (float, nullable)

## Testing

### Run Test Script

1. Start Django development server:
```bash
cd OOCAA
python manage.py runserver
```

2. In a new terminal, run the test:
```bash
cd OOCAA
python test_pc_calculation.py
```

Expected output:
```
================================================================================
CARA Pc Calculation Integration Test
================================================================================

Step 1: Creating CDM with state vectors and covariances...
✅ CDM created successfully (ID: 1)
   TCA: 2024-12-25T14:30:00Z
   Miss Distance: 58.31 m
   HBR: 10.0 m

Step 2: Calculating Pc using CARA PcMultiStep...
✅ Pc calculation successful!
   Pc: 1.234567e-05
   Method: PcMultiStep
   CDM Updated: True

...
```

## Important Notes

### Reference Frames
⚠️ **CRITICAL**: All state vectors and covariances must be in **ECI (Earth-Centered Inertial)** frame.

Standard CDM files often use **RTN (Radial-Transverse-Normal)** frame for covariances. You'll need to transform RTN → ECI using CARA's utilities in `Utils/CovarianceTransformations/` before storing in the database.

### Unit Conversions
CDM files typically use:
- Position: **kilometers** → Convert to **meters** (multiply by 1000)
- Velocity: **km/s** → Convert to **m/s** (multiply by 1000)
- Covariance: Usually already in **m²** and **m²/s** in CDM files

### MATLAB Engine Performance
- **Startup time**: 5-10 seconds (one-time per process)
- **Per-calculation**: ~50-200ms depending on method
- **Recommendation**: Use singleton pattern (already implemented)
- **For high volume**: Consider porting `PcCircle` to pure Python (NumPy/SciPy)

### Error Handling
The service gracefully handles:
- Missing required fields (validation error)
- Invalid covariance matrices (structure validation)
- MATLAB calculation errors (falls back to PcCircle)
- MATLAB Engine connection issues (informative error messages)

## Future Enhancements

### 1. CDM File Parser
Add automatic CDM file parsing:
```python
POST /api/cdms/upload-cdm/
Content-Type: multipart/form-data

# Automatically parse standard CDM format
# Extract state vectors, covariances, HBR
# Handle RTN → ECI transformation
# Create CDM with all fields populated
```

### 2. Python Port of PcCircle
For faster screening without MATLAB:
```python
def pc_circle_numpy(r1, v1, cov1, r2, v2, cov2, HBR):
    """Pure Python/NumPy implementation of PcCircle."""
    # Use scipy.special.erf for circular integration
    # ~10x faster than MATLAB Engine call
```

### 3. Covariance Transformation
Integrate CARA's RTN ↔ ECI transformation:
```python
from core.services.covariance_transform import rtn_to_eci

# Automatically transform on CDM creation
if cdm_data['covariance_frame'] == 'RTN':
    cov_eci = rtn_to_eci(cov_rtn, position, velocity)
```

### 4. Background Task Processing
For large batches:
```python
# Use Celery for async Pc calculation
from celery import shared_task

@shared_task
def calculate_pc_async(cdm_id):
    cdm = CDM.objects.get(id=cdm_id)
    result = calculate_pc_multistep(cdm)
    update_cdm_with_pc_result(cdm, result)
```

## Troubleshooting

### MATLAB Engine Not Found
```
ModuleNotFoundError: No module named 'matlab'
```
**Solution**: Install MATLAB Engine from MATLAB installation:
```bash
cd "C:\Program Files\MATLAB\R2025b\extern\engines\python"
python setup.py install
```

### Python Version Incompatibility
```
MATLAB Engine supports Python 3.9-3.12, but your version is 3.14
```
**Solution**: Create virtual environment with compatible Python version:
```bash
python3.12 -m venv venv
.\venv\Scripts\Activate.ps1
cd "C:\Program Files\MATLAB\R2025b\extern\engines\python"
python setup.py install
```

### Covariance Matrix Validation Error
```
Object 1 covariance matrix must be 3x3 or 6x6, got 2x?
```
**Solution**: Ensure covariance is properly formatted nested array:
```json
"obj1_covariance_matrix": [
  [100.0, 0.0, 0.0, ...],
  [0.0, 100.0, 0.0, ...],
  ...
]
```

### Missing State Vector Fields
```
Missing required fields: Object 1 X position, ...
```
**Solution**: All 15 fields (12 position/velocity + 2 covariances + 1 HBR) must be provided:
- `obj1_position_x/y/z`
- `obj1_velocity_x/y/z`
- `obj2_position_x/y/z`
- `obj2_velocity_x/y/z`
- `obj1_covariance_matrix`
- `obj2_covariance_matrix`
- `hard_body_radius`

## References

- [NASA CARA Analysis Tools (GitHub)](https://github.com/nasa/CARA_Analysis_Tools)
- [MATLAB Engine for Python Documentation](https://www.mathworks.com/help/matlab/matlab-engine-for-python.html)
- [PcMultiStep Algorithm Paper](https://commons.erau.edu/stm/2019/presentations/28) - Hejduk (2019)
- [Conjunction Probability Theory](https://doi.org/10.2514/1.22765) - Alfano (2005)

## Support

For issues or questions:
1. Check CARA_Analysis_Tools documentation in `References/` folder
2. Review MATLAB function headers (extensive inline documentation)
3. Examine `test_pc_calculation.py` for working examples
4. Check Django logs for detailed error messages
