# MATLAB Setup Guide

This project uses MATLAB Engine for collision probability calculations with the CARA Analysis Tools.

## Quick Setup for Team Members

### 1. Configure Your Local MATLAB Paths

Copy the environment template and add your paths:

```bash
cd OOCAA
copy .env.example .env  # Windows
# or
cp .env.example .env    # Mac/Linux
```

Edit `.env` and set your local paths:

```env
CARA_MATLAB_PATH=C:\Users\YourName\Path\To\CARA_Analysis_Tools\DistributedMatlab
MATLAB_ROOT=C:\Program Files\MATLAB\R2025b
```

> **Note**: The `.env` file is gitignored, so your local paths won't be committed.

### 2. Install MATLAB Engine for Python

From your MATLAB installation directory:

**Windows:**
```bash
cd "C:\Program Files\MATLAB\R2025b\extern\engines\python"
python setup.py install
```

**Mac:**
```bash
cd "/Applications/MATLAB_R2025b.app/extern/engines/python"
python setup.py install
```

### 3. Test Your Setup

```bash
python setup_matlab.py
```

This will verify:
- ✅ MATLAB Engine installation
- ✅ Local MATLAB function paths
- ✅ CARA Analysis Tools path
- ✅ Basic function availability

### 4. Use in Your Code

```python
from setup_matlab import get_matlab_engine

# Initialize MATLAB with all configured paths
eng = get_matlab_engine()

# Use MATLAB functions
result = eng.PcCircle(...)

# Clean up when done
eng.quit()
```

## For Existing Code

If you need to update existing MATLAB code to use the new setup, replace:

```python
# Old way
eng = matlab.engine.start_matlab()
eng.addpath(genpath('C:\\Hard\\Coded\\Path'))
```

With:

```python
# New way
from setup_matlab import get_matlab_engine
eng = get_matlab_engine()  # Automatically loads paths from .env
```

## Troubleshooting

### "CARA_MATLAB_PATH not set"
- Make sure you copied `.env.example` to `.env`
- Verify your `.env` file has the correct path set

### "MATLAB Engine not installed"
- Install from your MATLAB installation's `extern/engines/python` directory
- Make sure you're using the correct Python environment

### "Path does not exist"
- Check the path in your `.env` file
- Use absolute paths
- On Windows, use backslashes or forward slashes: `C:\Path\To\Dir` or `C:/Path/To/Dir`

## Team Workflow

1. **Never commit `.env`** - It contains local paths specific to your machine
2. **Do commit `.env.example`** - Updated template for new team members
3. **Share your MATLAB root path pattern** - Help teammates find their installation
4. **Use `setup_matlab.py`** - Consistent MATLAB initialization across the project
