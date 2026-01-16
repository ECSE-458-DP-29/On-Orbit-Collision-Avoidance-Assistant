"""MATLAB Setup Script for CARA Analysis Tools

This script initializes the MATLAB Engine and configures paths for the CARA
Analysis Tools. It reads configuration from environment variables to support
different team members' local setups.

Usage:
    python setup_matlab.py              # Just test the setup
    python -c "from setup_matlab import get_matlab_engine; eng = get_matlab_engine()"  # Use in code
"""

import os
import sys
from pathlib import Path


def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent / '.env'
    
    if not env_file.exists():
        print("⚠️  Warning: .env file not found!")
        print(f"   Expected location: {env_file}")
        print("   Copy .env.example to .env and configure your paths.")
        return False
    
    # Simple .env parser (for more complex needs, use python-dotenv package)
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                if value:  # Only set if value is not empty
                    os.environ[key] = value
    
    return True


def get_matlab_engine(add_cara_path=True):
    """Initialize and configure MATLAB Engine with CARA paths.
    
    Args:
        add_cara_path: If True, adds the CARA_MATLAB_PATH to MATLAB's search path
        
    Returns:
        matlab.engine: Configured MATLAB Engine instance
        
    Raises:
        ImportError: If MATLAB Engine is not installed
        RuntimeError: If MATLAB Engine fails to start or paths are misconfigured
    """
    # Load environment variables
    if not load_env_file():
        print("\n   Continuing anyway, but CARA paths may not be configured...")
    
    # Import MATLAB Engine
    try:
        import matlab.engine
    except ImportError as e:
        raise ImportError(
            "MATLAB Engine for Python is not installed.\n"
            "Install it from your MATLAB installation:\n"
            '  cd "C:\\Program Files\\MATLAB\\R2025b\\extern\\engines\\python"\n'
            "  python setup.py install"
        ) from e
    
    # Start MATLAB Engine
    print("Starting MATLAB Engine (this may take 5-10 seconds)...")
    try:
        eng = matlab.engine.start_matlab()
        print("MATLAB Engine started successfully")
    except Exception as e:
        raise RuntimeError(f"Failed to start MATLAB Engine: {e}") from e
    
    # Add local MATLAB function paths (always needed)
    current_dir = Path(__file__).parent
    matlab_dir = current_dir / 'core' / 'matlab'
    pc3d_utils_dir = matlab_dir / 'Pc3D_Hall_Utils'
    
    local_paths = [matlab_dir, pc3d_utils_dir]
    
    print("\nAdding local MATLAB paths...")
    for path in local_paths:
        if path.exists():
            eng.addpath(str(path), nargout=0)
            print(f"   Added: {path}")
        else:
            print(f"   Path not found: {path}")
    
    # Add CARA Analysis Tools path if requested
    if add_cara_path:
        cara_path = os.environ.get('CARA_MATLAB_PATH')
        
        if not cara_path:
            print("\nWarning: CARA_MATLAB_PATH not set in environment")
            print("   CARA Analysis Tools will not be available")
            print("   Set this in your .env file")
        else:
            cara_path = Path(cara_path)
            if not cara_path.exists():
                print(f"\nWarning: CARA_MATLAB_PATH does not exist: {cara_path}")
                print("   Check your .env file configuration")
            else:
                print(f"\nAdding CARA Analysis Tools path...")
                # Use genpath to add all subdirectories recursively
                eng.addpath(eng.genpath(str(cara_path)), nargout=0)
                print(f"   Added (with subdirectories): {cara_path}")
    
    return eng


def test_matlab_setup():
    """Test the MATLAB setup with a simple calculation."""
    print("=" * 80)
    print("MATLAB Setup Test")
    print("=" * 80)
    print()
    
    try:
        # Get configured MATLAB engine
        eng = get_matlab_engine(add_cara_path=True)
        
        # Test basic MATLAB operation
        print("\nTesting basic MATLAB calculation...")
        result = eng.sqrt(16.0)
        print(f"   MATLAB sqrt(16) = {result}")
        
        # Test local CARA function availability
        print("\nTesting local CARA functions...")
        try:
            exists = eng.eval("exist('PcCircle', 'file')", nargout=1)
            if exists > 0:
                print("   PcCircle function found")
            else:
                print("   PcCircle function not found")
        except Exception as e:
            print(f"   Could not verify PcCircle: {e}")
        
        # Display MATLAB path for debugging
        print("\nCurrent MATLAB path (first 5 entries):")
        try:
            path_str = eng.eval("path", nargout=1)
            paths = path_str.split(';')[:5]
            for p in paths:
                if p.strip():
                    print(f"   - {p}")
            if len(paths) >= 5:
                print(f"   ... and {len(path_str.split(';')) - 5} more")
        except:
            pass
        
        # Shutdown
        print("\nShutting down MATLAB Engine...")
        eng.quit()
        print("MATLAB Engine shutdown successfully")
        
        print()
        print("=" * 80)
        print("Setup test completed successfully!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\nSetup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = test_matlab_setup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
