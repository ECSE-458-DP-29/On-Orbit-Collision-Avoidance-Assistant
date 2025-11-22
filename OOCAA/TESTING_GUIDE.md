# Testing the CARA Integration

## Before Running Tests

### 1. Verify MATLAB Engine Installation

Run this quick test first:

```bash
python test_matlab_engine.py
```

This will:
- ✅ Check if MATLAB Engine is installed
- ✅ Verify MATLAB can start
- ✅ Add CARA paths
- ✅ Test basic MATLAB operations

**Expected output:**
```
================================================================================
MATLAB Engine Installation Test
================================================================================

Step 1: Checking MATLAB Engine installation...
✅ MATLAB Engine module found

Step 2: Starting MATLAB Engine (this may take 5-10 seconds)...
✅ MATLAB Engine started successfully

Step 3: Adding CARA Analysis Tools paths...
   ✅ Added: c:\...\ProbabilityOfCollision
   ...

✅ All tests passed! MATLAB Engine is ready.
```

---

## Running the Full API Test

### Step 1: Start Django Server

In **Terminal 1**:
```bash
cd OOCAA
python manage.py runserver
```

Keep this running. You should see:
```
Starting development server at http://127.0.0.1:8000/
```

### Step 2: Run Test Script

In **Terminal 2** (new terminal):
```bash
cd OOCAA
python test_pc_calculation.py
```

**⏱️ IMPORTANT**: The first Pc calculation will take **5-10 seconds** while MATLAB Engine initializes. This is normal!

**Expected output:**
```
================================================================================
CARA Pc Calculation Integration Test
================================================================================

Step 1: Creating CDM with state vectors and covariances...
✅ CDM created successfully (ID: 1)

Step 2: Calculating Pc using CARA PcMultiStep...
   (First calculation may take 5-10 seconds to initialize MATLAB...)
✅ Pc calculation successful!
   Pc: 1.234567e-05
   Method: PcMultiStep
   CDM Updated: True

...
```

---

## Manual Testing with curl

### Test 1: Create a CDM

```bash
curl -X POST http://localhost:8000/api/cdms/ \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "tca": "2024-12-25T14:30:00Z",
  "obj1_data": {
    "object_designator": "12345",
    "object_name": "TEST-SAT",
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
}
EOF
```

### Test 2: Calculate Pc

Replace `<CDM_ID>` with the ID from the response above:

```bash
curl -X POST http://localhost:8000/api/cdms/<CDM_ID>/calculate-pc/ \
  -H "Content-Type: application/json" \
  -d '{
    "method": "multistep",
    "update_cdm": true
  }'
```

**⏱️ Note**: First request will be slow (5-10s) due to MATLAB startup.

---

## Troubleshooting

### Issue: "Connection refused" or timeout

**Problem**: Django server is not running

**Solution**: 
```bash
# In Terminal 1
cd OOCAA
python manage.py runserver
```

### Issue: Test hangs at "Step 2: Calculating Pc"

**Problem**: MATLAB Engine is initializing (normal for first calculation)

**Solution**: Wait 10-15 seconds. If still hanging:
1. Check Django server logs for errors
2. Try running `test_matlab_engine.py` first
3. Verify MATLAB is installed and accessible

### Issue: "MATLAB Engine not installed"

**Problem**: MATLAB Engine for Python not installed

**Solution**:
```bash
cd "C:\Program Files\MATLAB\R2025b\extern\engines\python"
python setup.py install
```

### Issue: Django server errors mentioning "matlab"

**Problem**: MATLAB Engine paths may be incorrect

**Solution**: Update paths in `core/services/pc_calculation_service.py`:
```python
cara_base = r'c:\Users\Neeshal\OneDrive\Desktop\School Work\Capstone\CARA_Analysis_Tools\DistributedMatlab'
```

### Issue: "No module named 'requests'"

**Solution**:
```bash
pip install requests
```

---

## Performance Notes

| Action | First Time | Subsequent |
|--------|-----------|------------|
| MATLAB Engine startup | 5-10 seconds | N/A (singleton) |
| PcMultiStep calculation | 100-200ms | 100-200ms |
| PcCircle calculation | 50-100ms | 50-100ms |
| Batch (10 CDMs) | ~1-2 seconds | ~1-2 seconds |

---

## Next Steps After Testing

1. ✅ Verify MATLAB Engine works: `python test_matlab_engine.py`
2. ✅ Start Django server: `python manage.py runserver`
3. ✅ Run full test: `python test_pc_calculation.py`
4. 📚 Read full documentation: `CARA_INTEGRATION_GUIDE.md`
5. 🚀 Start building your application!

---

## Quick Reference

**Check if server is running:**
```bash
curl http://localhost:8000/api/
```

**List all CDMs:**
```bash
curl http://localhost:8000/api/cdms/
```

**Get specific CDM:**
```bash
curl http://localhost:8000/api/cdms/1/
```

**Calculate Pc (fast method):**
```bash
curl -X POST http://localhost:8000/api/cdms/1/calculate-pc/ \
  -H "Content-Type: application/json" \
  -d '{"method": "circle", "update_cdm": true}'
```
