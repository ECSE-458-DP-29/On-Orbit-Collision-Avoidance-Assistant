"""Service for calculating probability of collision using CARA MATLAB tools.

This service integrates NASA's CARA Analysis Tools via MATLAB Engine for Python
to calculate conjunction probability of collision (Pc) using industry-standard
algorithms like PcMultiStep, PcCircle, and PcDilution.
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
import numpy as np

logger = logging.getLogger(__name__)

# MATLAB Engine will be lazily initialized
_matlab_engine = None


class MatlabEngineError(Exception):
    """Exception raised when MATLAB Engine encounters an error."""
    pass


class PcCalculationError(Exception):
    """Exception raised when Pc calculation fails."""
    pass


def get_matlab_engine():
    """Get or initialize the MATLAB Engine singleton.
    
    Returns:
        matlab.engine instance
        
    Raises:
        MatlabEngineError: If MATLAB Engine cannot be initialized
    """
    global _matlab_engine
    
    if _matlab_engine is None:
        try:
            import matlab.engine
            import os
            logger.info("Starting MATLAB Engine...")
            _matlab_engine = matlab.engine.start_matlab()
            
            # Add local MATLAB function paths (copied from CARA_Analysis_Tools)
            # Get the absolute path to core/matlab directory
            core_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            matlab_dir = os.path.join(core_dir, 'matlab')
            pc3d_utils_dir = os.path.join(matlab_dir, 'Pc3D_Hall_Utils')
            
            paths_to_add = [
                matlab_dir,
                pc3d_utils_dir,
            ]
            
            for path in paths_to_add:
                if os.path.exists(path):
                    _matlab_engine.addpath(path, nargout=0)
                    logger.info(f"Added MATLAB path: {path}")
                else:
                    logger.warning(f"MATLAB path not found: {path}")
                
            logger.info("MATLAB Engine initialized successfully")
            
        except ImportError as e:
            raise MatlabEngineError(
                "MATLAB Engine for Python not installed. "
                "Install from MATLAB: cd 'C:\\Program Files\\MATLAB\\R2025b\\extern\\engines\\python' && python setup.py install"
            ) from e
        except Exception as e:
            raise MatlabEngineError(f"Failed to initialize MATLAB Engine: {str(e)}") from e
    
    return _matlab_engine


def shutdown_matlab_engine():
    """Shutdown the MATLAB Engine if it's running."""
    global _matlab_engine
    if _matlab_engine is not None:
        try:
            _matlab_engine.quit()
            logger.info("MATLAB Engine shutdown successfully")
        except Exception as e:
            logger.warning(f"Error shutting down MATLAB Engine: {str(e)}")
        finally:
            _matlab_engine = None


def validate_cdm_for_pc(cdm) -> tuple[bool, Optional[str]]:
    """Validate that a CDM has all required data for Pc calculation.
    
    Args:
        cdm: CDM model instance
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = [
        ('obj1_position_x', 'Object 1 X position'),
        ('obj1_position_y', 'Object 1 Y position'),
        ('obj1_position_z', 'Object 1 Z position'),
        ('obj1_velocity_x', 'Object 1 X velocity'),
        ('obj1_velocity_y', 'Object 1 Y velocity'),
        ('obj1_velocity_z', 'Object 1 Z velocity'),
        ('obj2_position_x', 'Object 2 X position'),
        ('obj2_position_y', 'Object 2 Y position'),
        ('obj2_position_z', 'Object 2 Z position'),
        ('obj2_velocity_x', 'Object 2 X velocity'),
        ('obj2_velocity_y', 'Object 2 Y velocity'),
        ('obj2_velocity_z', 'Object 2 Z velocity'),
        ('obj1_covariance_matrix', 'Object 1 covariance matrix'),
        ('obj2_covariance_matrix', 'Object 2 covariance matrix'),
        ('hard_body_radius', 'Hard body radius'),
    ]
    
    missing_fields = []
    for field_name, display_name in required_fields:
        value = getattr(cdm, field_name, None)
        if value is None:
            missing_fields.append(display_name)
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Validate hard body radius
    if cdm.hard_body_radius <= 0:
        return False, "Hard body radius must be greater than 0"
    
    # Validate covariance matrices structure
    for obj_num in [1, 2]:
        cov_matrix = getattr(cdm, f'obj{obj_num}_covariance_matrix')
        
        if not isinstance(cov_matrix, list):
            return False, f"Object {obj_num} covariance matrix must be a nested array"
        
        # Check if it's 6x6 or 3x3
        if len(cov_matrix) not in [3, 6]:
            return False, f"Object {obj_num} covariance matrix must be 3x3 or 6x6, got {len(cov_matrix)}x?"
        
        # Validate dimensions
        for i, row in enumerate(cov_matrix):
            if not isinstance(row, list) or len(row) != len(cov_matrix):
                return False, f"Object {obj_num} covariance matrix row {i} has incorrect dimensions"
    
    return True, None


def cdm_to_matlab_params(cdm) -> Dict[str, Any]:
    """Convert CDM model data to MATLAB function parameters.
    
    Args:
        cdm: CDM model instance
        
    Returns:
        Dictionary with MATLAB-ready parameters
        
    Raises:
        PcCalculationError: If data conversion fails
    """
    try:
        import matlab
        
        # Position vectors (convert to MATLAB double arrays as [1x3] row vectors)
        # MATLAB functions expect [nx3] format where n=1 for single conjunction
        r1 = matlab.double([[
            float(cdm.obj1_position_x),
            float(cdm.obj1_position_y),
            float(cdm.obj1_position_z),
        ]])
        
        r2 = matlab.double([[
            float(cdm.obj2_position_x),
            float(cdm.obj2_position_y),
            float(cdm.obj2_position_z),
        ]])
        
        # Velocity vectors as [1x3] row vectors
        v1 = matlab.double([[
            float(cdm.obj1_velocity_x),
            float(cdm.obj1_velocity_y),
            float(cdm.obj1_velocity_z),
        ]])
        
        v2 = matlab.double([[
            float(cdm.obj2_velocity_x),
            float(cdm.obj2_velocity_y),
            float(cdm.obj2_velocity_z),
        ]])
        
        # Covariance matrices (6x6 format)
        cov1 = matlab.double(cdm.obj1_covariance_matrix)
        cov2 = matlab.double(cdm.obj2_covariance_matrix)
        
        # Hard body radius (scalar)
        HBR = float(cdm.hard_body_radius)
        
        return {
            'r1': r1,
            'v1': v1,
            'cov1': cov1,
            'r2': r2,
            'v2': v2,
            'cov2': cov2,
            'HBR': HBR,
        }
        
    except Exception as e:
        raise PcCalculationError(f"Failed to convert CDM data to MATLAB parameters: {str(e)}") from e


def calculate_pc_multistep(cdm, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Calculate probability of collision using CARA's PcMultiStep algorithm.
    
    This is the recommended method as it automatically selects the best
    calculation approach (2D-Pc, 2D-Nc, or 3D-Nc) based on the conjunction geometry.
    
    Args:
        cdm: CDM model instance with complete state vectors and covariances
        params: Optional MATLAB parameters structure
        
    Returns:
        Dictionary containing:
            - Pc: Probability of collision (float)
            - method: Method used (str)
            - details: Additional calculation details (dict)
            - success: Calculation success flag (bool)
            
    Raises:
        PcCalculationError: If calculation fails
    """
    # Validate input data
    is_valid, error_msg = validate_cdm_for_pc(cdm)
    if not is_valid:
        raise PcCalculationError(error_msg)
    
    try:
        # Get MATLAB Engine
        eng = get_matlab_engine()
        
        # Convert CDM to MATLAB parameters
        matlab_params = cdm_to_matlab_params(cdm)
        
        # Build params structure if provided
        if params is None:
            params_struct = eng.struct()
        else:
            params_struct = eng.struct(params)
        
        logger.info(f"Calculating Pc for CDM #{cdm.id} using PcMultiStep")
        
        # Call MATLAB PcMultiStep function
        # [Pc, out] = PcMultiStep(r1, v1, C1, r2, v2, C2, HBR, params)
        try:
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
        except Exception as matlab_error:
            # Try PcCircle as fallback
            logger.warning(f"PcMultiStep failed, trying PcCircle: {str(matlab_error)}")
            Pc, out = eng.PcCircle(
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
            method_used = 'PcCircle (fallback)'
        else:
            method_used = 'PcMultiStep'
        
        # Convert MATLAB output to Python
        pc_value = float(Pc)
        
        # Extract details from output structure
        details = {}
        if out is not None:
            try:
                # MATLAB struct fields are accessible as attributes
                out_dict = {}
                for field in dir(out):
                    if not field.startswith('_'):
                        try:
                            value = getattr(out, field)
                            # Convert MATLAB types to Python
                            if hasattr(value, '__iter__') and not isinstance(value, str):
                                out_dict[field] = list(value)
                            else:
                                out_dict[field] = float(value) if isinstance(value, (int, float)) else str(value)
                        except:
                            pass
                details = out_dict
            except Exception as e:
                logger.warning(f"Could not extract output details: {str(e)}")
        
        logger.info(f"Pc calculation successful: {pc_value:.6e}")
        
        return {
            'Pc': pc_value,
            'method': method_used,
            'details': details,
            'success': True,
        }
        
    except MatlabEngineError as e:
        logger.error(f"MATLAB Engine error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Pc calculation failed: {str(e)}")
        raise PcCalculationError(f"Pc calculation failed: {str(e)}") from e


def calculate_pc_circle(cdm) -> Dict[str, Any]:
    """Calculate Pc using the fast 2D circular integration method.
    
    This is faster than PcMultiStep but less robust for edge cases.
    Good for screening/bulk processing.
    
    Args:
        cdm: CDM model instance
        
    Returns:
        Dictionary with Pc and calculation details
    """
    is_valid, error_msg = validate_cdm_for_pc(cdm)
    if not is_valid:
        raise PcCalculationError(error_msg)
    
    try:
        eng = get_matlab_engine()
        matlab_params = cdm_to_matlab_params(cdm)
        
        logger.info(f"Calculating Pc for CDM #{cdm.id} using PcCircle")
        
        Pc, out = eng.PcCircle(
            matlab_params['r1'],
            matlab_params['v1'],
            matlab_params['cov1'],
            matlab_params['r2'],
            matlab_params['v2'],
            matlab_params['cov2'],
            matlab_params['HBR'],
            nargout=2
        )
        
        return {
            'Pc': float(Pc),
            'method': 'PcCircle',
            'success': True,
        }
        
    except Exception as e:
        raise PcCalculationError(f"PcCircle calculation failed: {str(e)}") from e


def calculate_pc_dilution(cdm, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Analyze Pc dilution and calculate maximum possible Pc.
    
    Determines if the conjunction is in the "dilution region" where
    covariance scaling can increase Pc.
    
    Args:
        cdm: CDM model instance
        params: Optional parameters (e.g., PriSecScaling, RedFact)
        
    Returns:
        Dictionary containing:
            - PcOne: Nominal Pc (no covariance scaling)
            - PcMax: Maximum achievable Pc
            - SfMax: Scale factor at maximum Pc
            - Diluted: Boolean flag if dilution detected
    """
    is_valid, error_msg = validate_cdm_for_pc(cdm)
    if not is_valid:
        raise PcCalculationError(error_msg)
    
    try:
        eng = get_matlab_engine()
        matlab_params = cdm_to_matlab_params(cdm)
        
        if params is None:
            params_struct = eng.struct()
        else:
            params_struct = eng.struct(params)
        
        logger.info(f"Calculating Pc dilution for CDM #{cdm.id}")
        
        PcOne, Diluted, PcMax, SfMax, Pc, Sf, conv, iter_count = eng.PcDilution(
            matlab_params['r1'],
            matlab_params['v1'],
            matlab_params['cov1'],
            matlab_params['r2'],
            matlab_params['v2'],
            matlab_params['cov2'],
            matlab_params['HBR'],
            params_struct,
            nargout=8
        )
        
        return {
            'PcOne': float(PcOne),
            'PcMax': float(PcMax),
            'SfMax': float(SfMax),
            'Diluted': bool(Diluted),
            'converged': bool(conv),
            'iterations': int(iter_count),
            'method': 'PcDilution',
            'success': True,
        }
        
    except Exception as e:
        raise PcCalculationError(f"PcDilution calculation failed: {str(e)}") from e


def batch_calculate_pc(cdms: List, method: str = 'multistep') -> List[Dict[str, Any]]:
    """Calculate Pc for multiple CDMs in batch.
    
    Args:
        cdms: List of CDM model instances
        method: Calculation method ('multistep', 'circle', or 'dilution')
        
    Returns:
        List of result dictionaries, one per CDM
    """
    results = []
    
    for cdm in cdms:
        try:
            if method == 'multistep':
                result = calculate_pc_multistep(cdm)
            elif method == 'circle':
                result = calculate_pc_circle(cdm)
            elif method == 'dilution':
                result = calculate_pc_dilution(cdm)
            else:
                result = {
                    'success': False,
                    'error': f'Unknown method: {method}',
                    'cdm_id': cdm.id,
                }
            
            result['cdm_id'] = cdm.id
            results.append(result)
            
        except Exception as e:
            results.append({
                'success': False,
                'error': str(e),
                'cdm_id': cdm.id,
            })
    
    return results


def update_cdm_with_pc_result(cdm, pc_result: Dict[str, Any], save: bool = True):
    """Update a CDM instance with calculated Pc result.
    
    Args:
        cdm: CDM model instance
        pc_result: Result dictionary from calculate_pc_* functions
        save: Whether to save the CDM instance
    """
    if pc_result.get('success'):
        # Get Pc value (might be 'Pc', 'PcOne', or 'PcMax' depending on method)
        pc_value = pc_result.get('Pc') or pc_result.get('PcOne')
        
        if pc_value is not None:
            cdm.collision_probability = Decimal(str(pc_value))
            cdm.collision_probability_method = pc_result.get('method', 'CARA')
            
            if save:
                cdm.save()
                logger.info(f"Updated CDM #{cdm.id} with Pc={pc_value:.6e}")
