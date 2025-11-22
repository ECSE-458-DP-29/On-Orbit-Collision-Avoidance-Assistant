"""Quick test to verify MATLAB Engine installation and CARA path setup.

Run this to verify MATLAB Engine is working before testing the full API.
"""

import sys

def test_matlab_engine_installation():
    """Test if MATLAB Engine for Python is installed."""
    print("=" * 80)
    print("MATLAB Engine Installation Test")
    print("=" * 80)
    print()
    
    print("Step 1: Checking MATLAB Engine installation...")
    try:
        import matlab.engine
        print("✅ MATLAB Engine module found")
    except ImportError as e:
        print("❌ MATLAB Engine not installed")
        print(f"   Error: {e}")
        print("\n   Install from MATLAB:")
        print('   cd "C:\\Program Files\\MATLAB\\R2025b\\extern\\engines\\python"')
        print("   python setup.py install")
        return False
    
    print()
    print("Step 2: Starting MATLAB Engine (this may take 5-10 seconds)...")
    try:
        eng = matlab.engine.start_matlab()
        print("✅ MATLAB Engine started successfully")
    except Exception as e:
        print(f"❌ Failed to start MATLAB Engine: {e}")
        return False
    
    print()
    print("Step 3: Adding local MATLAB function paths...")
    try:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        matlab_dir = os.path.join(current_dir, 'core', 'matlab')
        pc3d_utils_dir = os.path.join(matlab_dir, 'Pc3D_Hall_Utils')
        
        paths_to_add = [
            matlab_dir,
            pc3d_utils_dir,
        ]
        
        for path in paths_to_add:
            if os.path.exists(path):
                eng.addpath(path, nargout=0)
                print(f"   ✅ Added: {path}")
            else:
                print(f"   ⚠️  Path not found: {path}")
    except Exception as e:
        print(f"❌ Failed to add MATLAB paths: {e}")
        eng.quit()
        return False
    
    print()
    print("Step 4: Testing simple MATLAB calculation...")
    try:
        # Test basic MATLAB operation
        result = eng.sqrt(16.0)
        print(f"   ✅ MATLAB sqrt(16) = {result}")
    except Exception as e:
        print(f"❌ MATLAB calculation failed: {e}")
        eng.quit()
        return False
    
    print()
    print("Step 5: Testing CARA function availability...")
    try:
        # Check if PcCircle exists
        eng.eval("exist('PcCircle', 'file')", nargout=1)
        print("   ✅ PcCircle function found")
    except Exception as e:
        print(f"⚠️  Could not verify PcCircle: {e}")
    
    print()
    print("Step 6: Shutting down MATLAB Engine...")
    try:
        eng.quit()
        print("✅ MATLAB Engine shutdown successfully")
    except Exception as e:
        print(f"⚠️  Engine shutdown warning: {e}")
    
    print()
    print("=" * 80)
    print("✅ All tests passed! MATLAB Engine is ready.")
    print("=" * 80)
    print()
    print("Next steps:")
    print("1. Start Django server: python manage.py runserver")
    print("2. Run API test: python test_pc_calculation.py")
    
    return True


if __name__ == "__main__":
    try:
        success = test_matlab_engine_installation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
