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
        assert b'Pc (Alfano)' in response.content

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
