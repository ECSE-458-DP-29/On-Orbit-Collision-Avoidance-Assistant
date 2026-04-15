from decimal import Decimal

import pytest
from django.urls import reverse

from core.tests.factories import CDMFactory, UserFactory


@pytest.mark.django_db
class TestManageCdmsPcModelSelection:
    def test_manage_cdms_uses_selected_pc_model_for_display(self, client):
        user = UserFactory(role='observer')
        client.force_login(user)

        cdm_alfano = CDMFactory(
            collision_probability=Decimal('0.00010'),
            collision_probability_multistep=Decimal('0.00010'),
            collision_probability_alfano=Decimal('0.02000'),
            collision_probability_monte_carlo=Decimal('0.00500'),
        )
        cdm_other = CDMFactory(
            collision_probability=Decimal('0.00020'),
            collision_probability_multistep=Decimal('0.00020'),
            collision_probability_alfano=Decimal('0.00030'),
            collision_probability_monte_carlo=Decimal('0.00040'),
        )

        response = client.get(reverse('manage-cdms'), {'pc_model': 'alfano'})

        assert response.status_code == 200
        assert response.context['filters']['pc_model'] == 'alfano'

        selected_probs = {
            cdm.id: cdm.selected_collision_probability
            for cdm in response.context['cdms']
        }
        assert selected_probs[cdm_alfano.id] == cdm_alfano.collision_probability_alfano
        assert selected_probs[cdm_other.id] == cdm_other.collision_probability_alfano
        assert b'Pc' in response.content

    def test_manage_cdms_applies_pc_filters_to_selected_model(self, client):
        user = UserFactory(role='observer')
        client.force_login(user)

        high_alfano = CDMFactory(
            collision_probability=Decimal('0.00001'),
            collision_probability_multistep=Decimal('0.00001'),
            collision_probability_alfano=Decimal('0.01500'),
            collision_probability_monte_carlo=Decimal('0.00002'),
        )
        low_alfano = CDMFactory(
            collision_probability=Decimal('0.10000'),
            collision_probability_multistep=Decimal('0.10000'),
            collision_probability_alfano=Decimal('0.00001'),
            collision_probability_monte_carlo=Decimal('0.10000'),
        )

        response = client.get(
            reverse('manage-cdms'),
            {
                'pc_model': 'alfano',
                'pc_min': '0.01000',
            },
        )

        assert response.status_code == 200
        result_ids = {cdm.id for cdm in response.context['cdms']}
        assert high_alfano.id in result_ids
        assert low_alfano.id not in result_ids

    def test_manage_cdms_shows_cdm_source_method_for_non_calculated_pc(self, client):
        user = UserFactory(role='observer')
        client.force_login(user)

        cdm = CDMFactory(
            collision_probability=Decimal('0.00000100942'),
            collision_probability_multistep=Decimal('0.00000100942'),
            collision_probability_alfano=Decimal('0.00000100942'),
            collision_probability_monte_carlo=Decimal('0.00000100942'),
            collision_probability_method='FOSTER-1992',
        )

        response = client.get(reverse('manage-cdms'), {'pc_model': 'multistep'})

        assert response.status_code == 200
        row = next(item for item in response.context['cdms'] if item.id == cdm.id)
        assert row.selected_pc_is_source is True
        assert row.selected_pc_method_label == 'FOSTER-1992'
        assert b'CDM: FOSTER-1992' in response.content

    def test_manage_cdms_shows_calculated_method_label_for_calculated_pc(self, client):
        user = UserFactory(role='observer')
        client.force_login(user)

        cdm = CDMFactory(
            collision_probability=Decimal('0.0002'),
            collision_probability_multistep=Decimal('0.0002'),
            collision_probability_alfano=Decimal('0.0003'),
            collision_probability_monte_carlo=Decimal('0.0004'),
            collision_probability_method='PcMultiStep',
        )

        response = client.get(reverse('manage-cdms'), {'pc_model': 'alfano'})

        assert response.status_code == 200
        row = next(item for item in response.context['cdms'] if item.id == cdm.id)
        assert row.selected_pc_is_source is False
        assert row.selected_pc_method_label == 'PcCircle (Alfano-based)'
        assert b'PcCircle (Alfano-based)' in response.content

    def test_manage_cdms_does_not_run_all_model_backfill_on_page_load(self, client, monkeypatch):
        user = UserFactory(role='observer')
        client.force_login(user)

        CDMFactory(
            collision_probability=Decimal('0.0002'),
            collision_probability_multistep=Decimal('0.0002'),
            collision_probability_alfano=Decimal('0.0003'),
            collision_probability_monte_carlo=Decimal('0.0004'),
            collision_probability_method='PcMultiStep',
        )

        def _unexpected_all_model_call(*args, **kwargs):
            raise AssertionError('calculate_all_pc_models should not be called by manage_cdms')

        monkeypatch.setattr('core.api.views.calculate_all_pc_models', _unexpected_all_model_call)

        response = client.get(reverse('manage-cdms'), {'pc_model': 'multistep'})
        assert response.status_code == 200
