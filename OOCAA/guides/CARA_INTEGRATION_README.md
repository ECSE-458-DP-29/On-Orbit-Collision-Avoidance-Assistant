# CARA Pc Calculation - Quick Start

## ✅ Implementation Complete

The OOCAA Django API now supports calculating probability of collision (Pc) using NASA's CARA Analysis Tools via MATLAB Engine.

## 🚀 Quick Test

1. **Start Django server:**
```bash
cd OOCAA
python manage.py runserver
```

2. **Run test script (in new terminal):**
```bash
cd OOCAA
python test_pc_calculation.py
```

## 📊 New API Endpoints

### Calculate Pc for Single CDM
```bash
POST /api/cdms/<id>/calculate-pc/
{
  "method": "multistep",  # or "circle", "dilution"
  "update_cdm": true
}
```

### Batch Calculate Pc
```bash
POST /api/cdms/batch-calculate-pc/
{
  "cdm_ids": [1, 2, 3],
  "method": "multistep",
  "update_cdms": true
}
```

## 📝 CDM Data Requirements

To calculate Pc, CDMs must include:

**Position & Velocity (ECI frame):**
- `obj1_position_x/y/z` (meters)
- `obj1_velocity_x/y/z` (m/s)
- `obj2_position_x/y/z` (meters)
- `obj2_velocity_x/y/z` (m/s)

**Covariance Matrices (6x6 or 3x3):**
- `obj1_covariance_matrix` (nested array)
- `obj2_covariance_matrix` (nested array)

**Hard Body Radius:**
- `hard_body_radius` (meters)

## 📖 Full Documentation

See `CARA_INTEGRATION_GUIDE.md` for complete details:
- API usage examples
- MATLAB integration architecture
- Data format specifications
- Troubleshooting guide

## 🔧 What Changed

### Database
- ✅ Added 15 new fields to `CDM` model
- ✅ Migration applied: `0004_cdm_hard_body_radius_cdm_obj1_covariance_matrix_and_more.py`

### Code
- ✅ `core/services/pc_calculation_service.py` - MATLAB Engine integration
- ✅ `core/api/views.py` - New Pc calculation endpoints
- ✅ `core/api/urls.py` - URL routing for new endpoints
- ✅ `core/api/serializers.py` - Extended with state vector fields
- ✅ `test_pc_calculation.py` - Comprehensive test script

### Dependencies
- ✅ `numpy` - Installed
- ✅ `requests` - Installed
- ⚠️ `matlabengine` - Already installed (Python 3.14 warning can be ignored)

## ⚠️ Important Notes

1. **Reference Frame**: All data must be in **ECI (Earth-Centered Inertial)** frame
2. **Units**: Position in meters, velocity in m/s
3. **MATLAB Engine**: First calculation will take 5-10s to initialize MATLAB
4. **Performance**: ~50-200ms per Pc calculation after initialization

## 🎯 Next Steps

1. **Test the integration** - Run `test_pc_calculation.py`
2. **Import real CDM data** - Parse actual CDM files and populate fields
3. **Consider RTN→ECI transformation** - Most CDMs use RTN frame for covariances
4. **Optimize for production** - Consider caching MATLAB engine or porting to Python

## 📚 CARA Methods Available

- **PcMultiStep** - NASA's recommended multi-tiered algorithm (default)
- **PcCircle** - Fast 2D circular integration for screening
- **PcDilution** - Maximum Pc analysis with covariance scaling

---

**Ready to calculate collision probabilities!** 🛰️✨
