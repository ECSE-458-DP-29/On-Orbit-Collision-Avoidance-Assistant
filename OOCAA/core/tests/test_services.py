import json
import pytest
from decimal import Decimal
from django.test import TestCase
from core.services.cdm_service import parse_cdm_json
from core.services.pc_calculation_service import (
    calculate_all_pc_models,
    update_cdm_with_pc_result,
    update_cdm_with_all_pc_results,
)
from core.models import CDM, SpaceObject
from core.tests.factories import CDMFactory, SpaceObjectFactory, EventFactory


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

    def test_parse_cdm_json_creates_space_objects(self):
        """Test that parse_cdm_json creates or fetches space objects correctly."""
        cdm_data = {
            "CCSDS_CDM_VERS": "1.0",
            "CREATION_DATE": "2025-01-20T08:12:49Z",
            "ORIGINATOR": "TestOrg",
            "MESSAGE_ID": "TEST_MSG_001",
            "TCA": "2025-01-25T07:24:13Z",
            "MISS_DISTANCE": "31612",
            "COLLISION_PROBABILITY": "1.3e-08",
            "SAT1_OBJECT_DESIGNATOR": "99999",
            "SAT1_OBJECT_NAME": "TestSat1",
            "SAT1_OBJECT_TYPE": "PAYLOAD",
            "SAT1_OPERATOR_ORGANIZATION": "TestOrg1",
            "SAT1_MANEUVERABLE": "NO",
            "SAT1_X": "1000.0",
            "SAT1_Y": "2000.0",
            "SAT1_Z": "3000.0",
            "SAT1_X_DOT": "-5.0",
            "SAT1_Y_DOT": "6.0",
            "SAT1_Z_DOT": "0.5",
            "SAT2_OBJECT_DESIGNATOR": "88888",
            "SAT2_OBJECT_NAME": "TestSat2",
            "SAT2_OBJECT_TYPE": "DEBRIS",
            "SAT2_OPERATOR_ORGANIZATION": "TestOrg2",
            "SAT2_MANEUVERABLE": "YES",
            "SAT2_X": "2000.0",
            "SAT2_Y": "3000.0",
            "SAT2_Z": "4000.0",
            "SAT2_X_DOT": "-8.0",
            "SAT2_Y_DOT": "10.0",
            "SAT2_Z_DOT": "1.5",
        }
        
        cdm, obj1, obj2 = parse_cdm_json(cdm_data)
        
        self.assertIsNotNone(obj1)
        self.assertIsNotNone(obj2)
        self.assertEqual(obj1.object_designator, "99999")
        self.assertEqual(obj2.object_designator, "88888")



@pytest.mark.django_db
class TestCDMFactoryAndRelationships:
    """Additional tests for CDM factory and relationships."""

    def test_cdm_factory_creates_related_objects(self):
        """Test CDM factory creates related space objects."""
        cdm = CDMFactory()
        assert cdm.obj1 is not None
        assert cdm.obj2 is not None
        assert SpaceObject.objects.filter(id=cdm.obj1.id).exists()
        assert SpaceObject.objects.filter(id=cdm.obj2.id).exists()

    def test_multiple_cdms_for_same_objects(self):
        """Test creating multiple CDMs for same object pair."""
        obj1 = SpaceObjectFactory()
        obj2 = SpaceObjectFactory()
        
        cdm1 = CDMFactory(obj1=obj1, obj2=obj2)
        cdm2 = CDMFactory(obj1=obj1, obj2=obj2)
        
        assert cdm1.id != cdm2.id
        assert cdm1.obj1 == cdm2.obj1
    
    def test_cdm_with_event_relationship(self):
        """Test CDM with associated event."""
        obj1 = SpaceObjectFactory()
        obj2 = SpaceObjectFactory()
        event = EventFactory(obj1=obj1, obj2=obj2)
        cdm = CDMFactory(obj1=obj1, obj2=obj2, event=event)
        
        assert cdm.event == event
        assert event.obj1 == obj1
        assert event.obj2 == obj2


@pytest.mark.django_db
class TestPcResultPersistence:
    def test_update_cdm_with_individual_model_results(self):
        cdm = CDMFactory(
            collision_probability=None,
            collision_probability_multistep=None,
            collision_probability_alfano=None,
            collision_probability_monte_carlo=None,
        )

        update_cdm_with_pc_result(cdm, {'success': True, 'Pc': 1e-4, 'method': 'PcMultiStep'}, save=False)
        update_cdm_with_pc_result(cdm, {'success': True, 'Pc': 2e-4, 'method': 'PcCircle'}, save=False)
        update_cdm_with_pc_result(cdm, {'success': True, 'Pc': 3e-4, 'method': 'MonteCarlo'}, save=False)

        assert cdm.collision_probability_multistep == Decimal('0.0001')
        assert cdm.collision_probability_alfano == Decimal('0.0002')
        assert cdm.collision_probability_monte_carlo == Decimal('0.0003')
        assert cdm.collision_probability == Decimal('0.0001')

    def test_update_cdm_with_all_model_results(self):
        cdm = CDMFactory(
            collision_probability=None,
            collision_probability_multistep=None,
            collision_probability_alfano=None,
            collision_probability_monte_carlo=None,
        )

        update_cdm_with_all_pc_results(
            cdm,
            {
                'success': True,
                'multistep': 4e-5,
                'alfano': 5e-5,
                'monte_carlo': 6e-5,
            },
            save=False,
        )

        assert cdm.collision_probability == Decimal('0.00004')
        assert cdm.collision_probability_multistep == Decimal('0.00004')
        assert cdm.collision_probability_alfano == Decimal('0.00005')
        assert cdm.collision_probability_monte_carlo == Decimal('0.00006')

    def test_model_probability_accessor_uses_legacy_fallback_for_multistep(self):
        cdm = CDMFactory(
            collision_probability=Decimal('0.00007'),
            collision_probability_multistep=None,
            collision_probability_alfano=Decimal('0.00008'),
            collision_probability_monte_carlo=Decimal('0.00009'),
        )

        assert cdm.get_collision_probability_for_model('multistep') == Decimal('0.00007')
        assert cdm.get_collision_probability_for_model('alfano') == Decimal('0.00008')
        assert cdm.get_collision_probability_for_model('monte_carlo') == Decimal('0.00009')

    def test_calculate_all_models_has_python_fallbacks_without_matlab(self, monkeypatch):
        from core.services import pc_calculation_service as pcs

        def _raise_matlab_error():
            raise pcs.MatlabEngineError('MATLAB unavailable in test')

        monkeypatch.setattr(pcs, 'get_matlab_engine', _raise_matlab_error)

        cdm = CDMFactory(
            collision_probability=None,
            collision_probability_multistep=None,
            collision_probability_alfano=None,
            collision_probability_monte_carlo=None,
            obj1_position_x=7000000.0,
            obj1_position_y=0.0,
            obj1_position_z=0.0,
            obj1_velocity_x=0.0,
            obj1_velocity_y=7500.0,
            obj1_velocity_z=0.0,
            obj2_position_x=7000010.0,
            obj2_position_y=2.0,
            obj2_position_z=0.5,
            obj2_velocity_x=0.0,
            obj2_velocity_y=7500.1,
            obj2_velocity_z=0.0,
            obj1_covariance_matrix=[
                [100.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 100.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 100.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            ],
            obj2_covariance_matrix=[
                [100.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 100.0, 0.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 100.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            ],
            hard_body_radius=10.0,
        )

        result = calculate_all_pc_models(cdm, None)

        assert result['multistep'] is not None
        assert result['alfano'] is not None
        assert result['monte_carlo'] is not None
        assert 0.0 <= result['multistep'] <= 1.0
        assert 0.0 <= result['alfano'] <= 1.0
        assert 0.0 <= result['monte_carlo'] <= 1.0

    def test_update_all_pc_results_clamps_values_to_db_safe_range(self):
        cdm = CDMFactory(
            collision_probability=None,
            collision_probability_multistep=None,
            collision_probability_alfano=None,
            collision_probability_monte_carlo=None,
            comments={},
        )

        update_cdm_with_all_pc_results(
            cdm,
            {
                'success': True,
                'multistep': 1.2,
                'alfano': 2.0,
                'monte_carlo': 10.0,
            },
            save=False,
        )

        max_allowed = Decimal('0.' + ('9' * 100))
        assert cdm.collision_probability == max_allowed
        assert cdm.collision_probability_multistep == max_allowed
        assert cdm.collision_probability_alfano == max_allowed
        assert cdm.collision_probability_monte_carlo == max_allowed

    def test_update_all_pc_results_uses_source_json_pc_when_all_zero(self):
        cdm = CDMFactory(
            collision_probability=Decimal('0.00000001347'),
            collision_probability_multistep=None,
            collision_probability_alfano=None,
            collision_probability_monte_carlo=None,
            comments={'source_collision_probability': '1.347e-08'},
        )

        update_cdm_with_all_pc_results(
            cdm,
            {
                'success': True,
                'multistep': 0.0,
                'alfano': 0.0,
                'monte_carlo': 0.0,
            },
            save=False,
        )

        fallback = Decimal('1.347e-08')
        assert cdm.collision_probability == fallback
        assert cdm.collision_probability_multistep == fallback
        assert cdm.collision_probability_alfano == fallback
        assert cdm.collision_probability_monte_carlo == fallback