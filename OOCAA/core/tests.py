import json
import math
from django.test import TestCase
from core.services.cdm_service import parse_cdm_json
from core.services.pc_calculation_service import calculate_pc_multistep, calculate_pc_circle, calculate_pc_dilution
from core.models import CDM, SpaceObject


class CDMServiceTest(TestCase):
    def test_parse_cdm_json_with_provided_data(self):
        # JSON data as provided (list with one CDM dict)
        cdm_json_str = '''[{"CCSDS_CDM_VERS":"1.0","CREATION_DATE":"2025-01-20T08:12:49.526","ORIGINATOR":"CSpoc","MESSAGE_ID":"5741_conj50_7046","TCA":"2025-01-25T07:24:13.000","MISS_DISTANCE":"31612","COLLISION_PROBABILITY":"1.3470000000000034e-08","SAT1_OBJECT":"OBJECT1","SAT1_OBJECT_DESIGNATOR":"39265","SAT1_CATALOG_NAME":"SATCAT","SAT1_OBJECT_NAME":"CASSIOPE","SAT1_INTERNATIONAL_DESIGNATOR":"2013-055A","SAT1_OBJECT_TYPE":"PAYLOAD","SAT1_OPERATOR_ORGANIZATION":"CSA","SAT1_COVARIANCE_METHOD":"CALCULATED","SAT1_MANEUVERABLE":"NO","SAT1_REFERENCE_FRAME":"ITRF","SAT1_X":"893.2881302848575","SAT1_Y":"742.1116994805794","SAT1_Z":"7170.904591941126","SAT1_X_DOT":"-4.1894033396829595","SAT1_Y_DOT":"5.920251359621457","SAT1_Z_DOT":"0.02921623106465332","SAT1_CR_R":"70.74921999999998","SAT1_CT_R":"-846.8535","SAT1_CT_T":"92438.33000000003","SAT1_CN_R":"-6.0794969999999955","SAT1_CN_T":"143.41039999999998","SAT1_CN_N":"44.9022","SAT1_CRDOT_R":"0.7401715999999998","SAT1_CRDOT_T":"-95.80014000000001","SAT1_CRDOT_N":"-0.13916969999999979","SAT1_CRDOT_RDOT":"0.09971835000000001","SAT1_CTDOT_R":"-0.07367386999999978","SAT1_CTDOT_T":"0.7183661999999981","SAT1_CTDOT_N":"0.006190040999999978","SAT1_CTDOT_RDOT":"-0.000597340499999998","SAT1_CTDOT_TDOT":"7.705020999999956e-05","SAT1_CNDOT_R":"0.007611995999999894","SAT1_CNDOT_T":"0.013135319999999732","SAT1_CNDOT_N":"0.013351359999999817","SAT1_CNDOT_RDOT":"-1.540397999999972e-05","SAT1_CNDOT_TDOT":"-8.032752999999863e-06","SAT1_CNDOT_NDOT":"3.2427949999999104e-05","SAT2_OBJECT":"OBJECT1","SAT2_OBJECT_DESIGNATOR":"44322","SAT2_CATALOG_NAME":"SATCAT","SAT2_OBJECT_NAME":"RCM-1","SAT2_INTERNATIONAL_DESIGNATOR":"2019-033A","SAT2_OBJECT_TYPE":"PAYLOAD","SAT2_EPHEMERIS_NAME":"NONE","SAT2_COVARIANCE_METHOD":"CALCULATED","SAT2_MANEUVERABLE":"YES","SAT2_REFERENCE_FRAME":"ITRF","SAT2_X":"1786.393860569715","SAT2_Y":"1502.7850989611588","SAT2_Z":"14316.21998388225","SAT2_X_DOT":"-8.403406679365919","SAT2_Y_DOT":"21.629002719242916","SAT2_Z_DOT":"7.160232462129307","SAT2_CR_R":"5326.218999999997","SAT2_CT_R":"-1160480.9999999995","SAT2_CT_T":"501480300.00000006","SAT2_CN_R":"1243.8049999999998","SAT2_CN_T":"28041.019999999953","SAT2_CN_N":"1585.3010000000002","SAT2_CRDOT_R":"1220.9649999999997","SAT2_CRDOT_T":"-527741.8000000002","SAT2_CRDOT_N":"-29.147989999999993","SAT2_CRDOT_RDOT":"555.3798","SAT2_CTDOT_R":"-4.366282999999997","SAT2_CTDOT_T":"686.8412999999996","SAT2_CTDOT_N":"-1.337925999999999","SAT2_CTDOT_RDOT":"-0.7225055999999995","SAT2_CTDOT_TDOT":"0.0038612039999999953","SAT2_CNDOT_R":"6.915582280167703","SAT2_CNDOT_T":"1720.1076856702405","SAT2_CNDOT_N":"13.939652991049556","SAT2_CNDOT_RDOT":"-0.3657449000000001","SAT2_CNDOT_TDOT":"-0.0018407309999999987","SAT2_CNDOT_NDOT":"0.006105515999999999","SAT2_OPERATOR_ORGANIZATION":"CSA"}]'''
        
        # Parse the JSON
        cdm_list = json.loads(cdm_json_str)
        cdm_data = cdm_list[0]  # Extract the CDM dict
        
        # Call the parse function
        cdm, obj1, obj2 = parse_cdm_json(cdm_data)
        
        # Assertions to verify parsing and creation
        self.assertIsInstance(cdm, CDM)
        self.assertEqual(cdm.message_id, "5741_conj50_7046")
        self.assertEqual(cdm.originator, "CSpoc")
        self.assertEqual(cdm.ccsds_version, "1.0")
        
        # Check that SpaceObjects were created/fetched
        self.assertIsNotNone(cdm.obj1)
        self.assertIsNotNone(cdm.obj2)
        self.assertEqual(cdm.obj1.object_designator, "39265")
        self.assertEqual(cdm.obj2.object_designator, "44322")
        
        # Check state vectors (example)
        self.assertIn("x_km", cdm.state_vector_obj1)
        self.assertEqual(cdm.state_vector_obj1["x_km"], "893.2881302848575")

    def test_probability_of_collision_calculation(self):
        # Use the same CDM data
        cdm_json_str = '''[{"CCSDS_CDM_VERS":"1.0","CREATION_DATE":"2025-01-20T08:12:49.526","ORIGINATOR":"CSpoc","MESSAGE_ID":"5741_conj50_7046","TCA":"2025-01-25T07:24:13.000","MISS_DISTANCE":"1732","COLLISION_PROBABILITY":"1.3470000000000034e-08","SAT1_OBJECT":"OBJECT1","SAT1_OBJECT_DESIGNATOR":"39265","SAT1_CATALOG_NAME":"SATCAT","SAT1_OBJECT_NAME":"CASSIOPE","SAT1_INTERNATIONAL_DESIGNATOR":"2013-055A","SAT1_OBJECT_TYPE":"PAYLOAD","SAT1_OPERATOR_ORGANIZATION":"CSA","SAT1_COVARIANCE_METHOD":"CALCULATED","SAT1_MANEUVERABLE":"NO","SAT1_REFERENCE_FRAME":"ITRF","SAT1_X":"893.2881302848575","SAT1_Y":"742.1116994805794","SAT1_Z":"7170.904591941126","SAT1_X_DOT":"-4.1894033396829595","SAT1_Y_DOT":"5.920251359621457","SAT1_Z_DOT":"0.02921623106465332","SAT1_CR_R":"1000000.0","SAT1_CT_R":"0.0","SAT1_CT_T":"1000000.0","SAT1_CN_R":"0.0","SAT1_CN_T":"0.0","SAT1_CN_N":"1000000.0","SAT1_CRDOT_R":"0.0","SAT1_CRDOT_T":"0.0","SAT1_CRDOT_N":"0.0","SAT1_CRDOT_RDOT":"100000.0","SAT1_CTDOT_R":"0.0","SAT1_CTDOT_T":"100000.0","SAT1_CTDOT_N":"0.0","SAT1_CTDOT_RDOT":"0.0","SAT1_CTDOT_TDOT":"100000.0","SAT1_CNDOT_R":"0.0","SAT1_CNDOT_T":"0.0","SAT1_CNDOT_N":"0.0","SAT1_CNDOT_RDOT":"0.0","SAT1_CNDOT_TDOT":"0.0","SAT1_CNDOT_NDOT":"100000.0","SAT2_OBJECT":"OBJECT1","SAT2_OBJECT_DESIGNATOR":"44322","SAT2_CATALOG_NAME":"SATCAT","SAT2_OBJECT_NAME":"RCM-1","SAT2_INTERNATIONAL_DESIGNATOR":"2019-033A","SAT2_OBJECT_TYPE":"PAYLOAD","SAT2_EPHEMERIS_NAME":"NONE","SAT2_COVARIANCE_METHOD":"CALCULATED","SAT2_MANEUVERABLE":"YES","SAT2_REFERENCE_FRAME":"ITRF","SAT2_X":"894.2881302848575","SAT2_Y":"743.1116994805794","SAT2_Z":"7171.904591941126","SAT2_X_DOT":"-4.0894033396829595","SAT2_Y_DOT":"6.020251359621457","SAT2_Z_DOT":"0.12921623106465332","SAT2_CR_R":"1000000.0","SAT2_CT_R":"0.0","SAT2_CT_T":"1000000.0","SAT2_CN_R":"0.0","SAT2_CN_T":"0.0","SAT2_CN_N":"1000000.0","SAT2_CRDOT_R":"0.0","SAT2_CRDOT_T":"0.0","SAT2_CRDOT_N":"0.0","SAT2_CRDOT_RDOT":"100000.0","SAT2_CTDOT_R":"0.0","SAT2_CTDOT_T":"100000.0","SAT2_CTDOT_N":"0.0","SAT2_CTDOT_RDOT":"0.0","SAT2_CTDOT_TDOT":"100000.0","SAT2_CNDOT_R":"0.0","SAT2_CNDOT_T":"0.0","SAT2_CNDOT_N":"0.0","SAT2_CNDOT_RDOT":"0.0","SAT2_CNDOT_TDOT":"0.0","SAT2_CNDOT_NDOT":"100000.0","SAT2_OPERATOR_ORGANIZATION":"CSA"}]'''
        
        # Parse the JSON
        cdm_list = json.loads(cdm_json_str)
        cdm_data = cdm_list[0]
        
        # Create the CDM
        cdm, obj1, obj2 = parse_cdm_json(cdm_data)
        
        # Test probability calculation using all methods and compare results
        methods = [
            ("PcMultiStep", calculate_pc_multistep, "Pc"),
            ("PcCircle", calculate_pc_circle, "Pc"),
            ("PcDilution", calculate_pc_dilution, "PcOne"),
        ]
        
        results = {}
        for method_name, func, key in methods:
            try:
                result = func(cdm)
                pc_value = result[key]
                results[method_name] = pc_value
                print(f"Collision Probability ({key}) using {method_name}: {pc_value}")
                
                # Assertions for the result
                self.assertIsInstance(result, dict)
                self.assertIn(key, result)
                self.assertIn("method", result)
                self.assertEqual(result["method"], method_name)
                # Check that Pc is a number
                self.assertIsInstance(pc_value, (int, float))
                
            except Exception as e:
                # Fail the test with the actual error for debugging
                self.fail(f"Probability calculation failed for {method_name}: {str(e)}")
        
        # Print comparison
        print("\nComparison of Pc values:")
        for method, pc in results.items():
            print(f"{method}: {pc}")
        
        # Ensure all methods produced finite results
        for method, pc in results.items():
            self.assertTrue(pc >= 0, f"Pc for {method} should be non-negative")
            self.assertFalse(math.isnan(pc), f"Pc for {method} should not be NaN")
