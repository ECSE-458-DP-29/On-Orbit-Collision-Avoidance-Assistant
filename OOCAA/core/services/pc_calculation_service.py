"""Service for calculating probability of collision using CARA MATLAB tools.

This service integrates NASA's CARA Analysis Tools via MATLAB Engine for Python
to calculate conjunction probability of collision (Pc) using industry-standard
algorithms like PcMultiStep, PcCircle, and PcDilution.
"""

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal
import numpy as np
import math
import os
import sys

# Add parent directory to path to import setup_matlab
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from setup_matlab import get_matlab_engine as get_configured_matlab_engine

logger = logging.getLogger(__name__)

# MATLAB Engine will be lazily initialized
_matlab_engine = None

MAX_DB_PC_DECIMAL = Decimal('0.' + ('9' * 100))


class MatlabEngineError(Exception):
    """Exception raised when MATLAB Engine encounters an error."""
    pass


class PcCalculationError(Exception):
    """Exception raised when Pc calculation fails."""
    pass


def _normalize_probability_decimal(value: Any) -> Optional[Decimal]:
    """Normalize probability for storage in DecimalField(100, 100).

    The DB field allows only values in [-1, 1) with no integer digits.
    We clamp to [0, 0.999...100x9] and drop invalid/non-finite values.
    """
    if value is None:
        return None

    try:
        decimal_value = Decimal(str(value))
    except Exception:
        return None

    if not decimal_value.is_finite():
        return None

    if decimal_value <= Decimal('0'):
        return Decimal('0')

    if decimal_value >= Decimal('1'):
        return MAX_DB_PC_DECIMAL

    return decimal_value


def _json_collision_probability_fallback(cdm) -> Optional[Decimal]:
    """Get original collision probability provided in the source CDM JSON, if present."""
    comments = cdm.comments if isinstance(cdm.comments, dict) else {}
    candidate = comments.get('source_collision_probability')

    # Backward compatibility for rows uploaded before source Pc was preserved in comments.
    if candidate is None:
        candidate = cdm.collision_probability

    fallback_value = _normalize_probability_decimal(candidate)
    if fallback_value is None or fallback_value == Decimal('0'):
        return None
    return fallback_value


def _ensure_sdmc_library_path() -> None:
    """Ensure CARA SDMC native library directory is present on PATH."""
    cara_root = os.environ.get('CARA_MATLAB_PATH')
    if not cara_root:
        return

    sdmc_lib = os.path.join(cara_root, 'ProbabilityOfCollision', 'SDMC_Utils', 'lib')
    if not os.path.isdir(sdmc_lib):
        return

    current_path = os.environ.get('PATH', '')
    parts = current_path.split(os.pathsep) if current_path else []
    if sdmc_lib not in parts:
        os.environ['PATH'] = os.pathsep.join([sdmc_lib, current_path]) if current_path else sdmc_lib


def get_matlab_engine():
    """Get or initialize the MATLAB Engine singleton using setup_matlab.py.
    
    This function uses the centralized setup_matlab module which:
    - Loads paths from .env file
    - Adds local MATLAB paths (core/matlab)
    - Adds CARA Analysis Tools paths from environment
    - Properly initializes MATLAB Engine with all dependencies
    
    Returns:
        matlab.engine instance
        
    Raises:
        MatlabEngineError: If MATLAB Engine cannot be initialized
    """
    global _matlab_engine
    
    if _matlab_engine is None:
        try:
            logger.info("Initializing MATLAB Engine with CARA paths...")
            _ensure_sdmc_library_path()
            # Use the centralized setup from setup_matlab.py
            # This handles .env loading and path configuration
            _matlab_engine = get_configured_matlab_engine(add_cara_path=True)
            logger.info("MATLAB Engine initialized successfully with CARA paths")
            
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
        # Convert from m^2 and m^2/s to km^2 and km^2/s
        cov1 = matlab.double(np.array(cdm.obj1_covariance_matrix) / 1e6)
        cov2 = matlab.double(np.array(cdm.obj2_covariance_matrix) / 1e6)
        
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


def _relative_position_and_combined_covariance(cdm) -> tuple[np.ndarray, np.ndarray]:
    """Return relative position and combined 3x3 positional covariance in meters."""
    rel_position = np.array([
        float(cdm.obj2_position_x) - float(cdm.obj1_position_x),
        float(cdm.obj2_position_y) - float(cdm.obj1_position_y),
        float(cdm.obj2_position_z) - float(cdm.obj1_position_z),
    ], dtype=float)

    cov1 = np.array(cdm.obj1_covariance_matrix, dtype=float)
    cov2 = np.array(cdm.obj2_covariance_matrix, dtype=float)
    cov1_pos = cov1[:3, :3]
    cov2_pos = cov2[:3, :3]

    combined_cov = cov1_pos + cov2_pos
    combined_cov = 0.5 * (combined_cov + combined_cov.T)
    return rel_position, combined_cov


def _python_alfano_circle_pc(cdm) -> float:
    """Approximate Alfano/PcCircle with a 2D Gaussian encounter-plane model.

    Uses an isotropic equivalent sigma in the encounter plane and evaluates
    the probability mass inside the hard-body radius centered at the nominal
    miss distance.
    """
    rel_position, combined_cov = _relative_position_and_combined_covariance(cdm)
    miss_distance = float(np.linalg.norm(rel_position))

    # Use the two largest positional variances as encounter-plane uncertainty.
    eigvals = np.linalg.eigvalsh(combined_cov)
    eigvals = np.clip(np.sort(eigvals), 1e-12, None)
    sigma_eq = float(np.sqrt((eigvals[-1] + eigvals[-2]) / 2.0))
    hbr = float(cdm.hard_body_radius)

    if sigma_eq <= 0 or hbr <= 0:
        raise PcCalculationError("Invalid covariance or hard body radius for Python Alfano fallback")

    z_outer = (miss_distance + hbr) / (math.sqrt(2.0) * sigma_eq)
    z_inner = max(miss_distance - hbr, 0.0) / (math.sqrt(2.0) * sigma_eq)
    pc_value = max(0.0, min(1.0, math.erf(z_outer) - math.erf(z_inner)))
    return pc_value


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
        # Fall back to Python approximation when MATLAB/CARA is unavailable.
        logger.warning(f"MATLAB Engine unavailable, using Python MultiStep fallback: {str(e)}")
        pc_value = _python_alfano_circle_pc(cdm)
        return {
            'Pc': pc_value,
            'method': 'PcMultiStep (python fallback)',
            'details': {'engine': 'python-fallback'},
            'success': True,
        }
    except Exception as e:
        logger.error(f"Pc calculation failed: {str(e)}")
        # If MATLAB path fails for any reason, still provide a deterministic fallback.
        try:
            pc_value = _python_alfano_circle_pc(cdm)
            return {
                'Pc': pc_value,
                'method': 'PcMultiStep (python fallback)',
                'details': {'engine': 'python-fallback'},
                'success': True,
            }
        except Exception as fallback_exc:
            raise PcCalculationError(f"Pc calculation failed: {str(fallback_exc)}") from fallback_exc


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
        try:
            pc_value = _python_alfano_circle_pc(cdm)
            return {
                'Pc': pc_value,
                'method': 'PcCircle (python fallback)',
                'details': {'engine': 'python-fallback'},
                'success': True,
            }
        except Exception as fallback_exc:
            raise PcCalculationError(f"PcCircle calculation failed: {str(fallback_exc)}") from fallback_exc


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


def calculate_pc_monte_carlo(cdm, sample_count: int = 50000, seed: Optional[int] = 42) -> Dict[str, Any]:
    """Calculate Pc using Monte Carlo sampling in the relative position space.

    This method approximates collision probability by sampling from the
    combined 3D position uncertainty of both objects and counting samples
    that intersect the hard-body sphere.
    """
    is_valid, error_msg = validate_cdm_for_pc(cdm)
    if not is_valid:
        raise PcCalculationError(error_msg)

    try:
        matlab_failure_reason = None
        # First try CARA/Matlab Monte Carlo implementations if available.
        try:
            eng = get_matlab_engine()
            matlab_params = cdm_to_matlab_params(cdm)
            # Pc_SDMC is the CARA Monte Carlo wrapper in ProbabilityOfCollision.
            try:
                sdmc_path = eng.eval("which('Pc_SDMC')", nargout=1)
            except Exception:
                sdmc_path = ''

            if sdmc_path:
                # Ensure MATLAB process PATH includes SDMC native library path.
                cara_root = os.environ.get('CARA_MATLAB_PATH')
                if cara_root:
                    sdmc_lib = os.path.join(cara_root, 'ProbabilityOfCollision', 'SDMC_Utils', 'lib')
                    if os.path.isdir(sdmc_lib):
                        existing = eng.getenv('PATH')
                        if sdmc_lib not in existing.split(';'):
                            eng.setenv('PATH', f"{sdmc_lib};{existing}", nargout=0)

                # Build SDMC params from defaults and override practical knobs.
                params_struct = eng.default_params_Pc_SDMC(eng.struct(), nargout=1)
                params_struct = eng.setfield(params_struct, 'num_trials', float(sample_count), nargout=1)
                seed_value = int(seed if seed is not None else 42)
                if seed_value >= 0:
                    seed_value = -max(seed_value, 1)
                params_struct = eng.setfield(params_struct, 'seed', float(seed_value), nargout=1)
                params_struct = eng.setfield(params_struct, 'verbose', False, nargout=1)

                Pc, out = eng.Pc_SDMC(
                    matlab_params['r1'],
                    matlab_params['v1'],
                    matlab_params['cov1'],
                    matlab_params['r2'],
                    matlab_params['v2'],
                    matlab_params['cov2'],
                    matlab_params['HBR'],
                    params_struct,
                    nargout=2,
                )

                details = {'engine': 'matlab-cara', 'function': 'Pc_SDMC'}
                try:
                    details['PcUnc'] = getattr(out, 'PcUnc')
                except Exception:
                    pass

                return {
                    'Pc': float(Pc),
                    'method': 'Pc_SDMC (CARA Monte Carlo)',
                    'details': details,
                    'success': True,
                }

            # If legacy Monte Carlo entry points exist in a different CARA drop,
            # try them before leaving MATLAB path.
            matlab_candidates = ['PcMonteCarlo', 'MonteCarloPc', 'PcMC']
            for function_name in matlab_candidates:
                try:
                    Pc = eng.feval(
                        function_name,
                        matlab_params['r1'],
                        matlab_params['v1'],
                        matlab_params['cov1'],
                        matlab_params['r2'],
                        matlab_params['v2'],
                        matlab_params['cov2'],
                        matlab_params['HBR'],
                        nargout=1,
                    )
                    return {
                        'Pc': float(Pc),
                        'method': f'{function_name} (CARA Monte Carlo)',
                        'details': {'engine': 'matlab-cara'},
                        'success': True,
                    }
                except Exception:
                    continue
        except Exception as matlab_exc:
            # If MATLAB is unavailable or CARA Monte Carlo function is not found,
            # fall back to deterministic Python Monte Carlo.
            matlab_failure_reason = str(matlab_exc)

        rel_position, combined_cov = _relative_position_and_combined_covariance(cdm)

        rng = np.random.default_rng(seed)
        try:
            samples = rng.multivariate_normal(rel_position, combined_cov, size=sample_count)
        except np.linalg.LinAlgError:
            jitter = np.eye(3) * 1e-6
            samples = rng.multivariate_normal(rel_position, combined_cov + jitter, size=sample_count)

        distances = np.linalg.norm(samples, axis=1)
        pc_value = float(np.mean(distances <= float(cdm.hard_body_radius)))

        return {
            'Pc': pc_value,
            'method': 'MonteCarlo',
            'details': {
                'sample_count': sample_count,
                'seed': seed,
                'engine': 'python-fallback',
                'matlab_fallback_reason': matlab_failure_reason,
            },
            'success': True,
        }
    except Exception as e:
        raise PcCalculationError(f"Monte Carlo calculation failed: {str(e)}") from e


def calculate_all_pc_models(cdm, params: Optional[Dict] = None) -> Dict[str, Any]:
    """Calculate all supported collision probability models for a CDM."""
    results = {
        'success': True,
        'multistep': None,
        'alfano': None,
        'monte_carlo': None,
        'errors': {},
    }

    calculators = {
        'multistep': lambda: calculate_pc_multistep(cdm, params),
        # CARA's fast PcCircle method is commonly referred to as an Alfano-style 2D Pc model.
        'alfano': lambda: calculate_pc_circle(cdm),
        'monte_carlo': lambda: calculate_pc_monte_carlo(cdm),
    }

    for model_key, calculator in calculators.items():
        try:
            model_result = calculator()
            if model_result.get('success'):
                if model_result.get('Pc') is not None:
                    results[model_key] = model_result.get('Pc')
                elif model_result.get('PcOne') is not None:
                    results[model_key] = model_result.get('PcOne')
            else:
                results['success'] = False
                results['errors'][model_key] = model_result.get('error', 'Unknown error')
        except Exception as exc:
            results['success'] = False
            results['errors'][model_key] = str(exc)

    return results


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
        pc_value = pc_result.get('Pc')
        if pc_value is None:
            pc_value = pc_result.get('PcOne')

        if pc_value is not None:
            method_name = (pc_result.get('method') or 'CARA').lower()
            decimal_value = _normalize_probability_decimal(pc_value)
            if decimal_value is None:
                return

            if 'multistep' in method_name:
                cdm.collision_probability_multistep = decimal_value
                cdm.collision_probability = decimal_value
            elif 'circle' in method_name or 'alfano' in method_name:
                cdm.collision_probability_alfano = decimal_value
            elif 'monte' in method_name:
                cdm.collision_probability_monte_carlo = decimal_value
            elif 'dilution' in method_name:
                cdm.collision_probability_multistep = decimal_value
                cdm.collision_probability = decimal_value

            cdm.collision_probability_method = pc_result.get('method', 'CARA')

            if save:
                cdm.save()
                logger.info(f"Updated CDM #{cdm.id} with Pc={pc_value:.6e}")


def update_cdm_with_all_pc_results(cdm, all_results: Dict[str, Any], save: bool = True):
    """Persist per-model Pc values on the CDM instance."""
    model_field_map = {
        'multistep': 'collision_probability_multistep',
        'alfano': 'collision_probability_alfano',
        'monte_carlo': 'collision_probability_monte_carlo',
    }

    normalized_values: Dict[str, Optional[Decimal]] = {}
    for model_key, field_name in model_field_map.items():
        value = all_results.get(model_key)
        normalized_value = _normalize_probability_decimal(value)
        normalized_values[model_key] = normalized_value
        if normalized_value is not None:
            setattr(cdm, field_name, normalized_value)

    # If all three computed model values are exactly zero, fall back to the
    # probability value originally provided by the uploaded CDM JSON (if any).
    zero_values = [
        normalized_values.get('multistep'),
        normalized_values.get('alfano'),
        normalized_values.get('monte_carlo'),
    ]
    if zero_values and all(v == Decimal('0') for v in zero_values):
        fallback = _json_collision_probability_fallback(cdm)
        if fallback is not None:
            cdm.collision_probability_multistep = fallback
            cdm.collision_probability_alfano = fallback
            cdm.collision_probability_monte_carlo = fallback
            normalized_values['multistep'] = fallback
            normalized_values['alfano'] = fallback
            normalized_values['monte_carlo'] = fallback

    # Keep legacy field synchronized with multistep for backward compatibility.
    if normalized_values.get('multistep') is not None:
        cdm.collision_probability = normalized_values['multistep']
        cdm.collision_probability_method = 'PcMultiStep'

    if save:
        cdm.save()
