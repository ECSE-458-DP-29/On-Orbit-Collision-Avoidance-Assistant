import pytest
from decimal import Decimal

from core.tests.factories import CDMFactory


@pytest.mark.django_db
def test_dashboard_distribution_counts_zero_values_for_selected_model(client):
    # 2 high-risk and 2 low-risk (including explicit zero), all in multistep model.
    CDMFactory(collision_probability_multistep=Decimal('0.0'), collision_probability=None)
    CDMFactory(collision_probability_multistep=Decimal('0.0000005'), collision_probability=None)
    CDMFactory(collision_probability_multistep=Decimal('0.01'), collision_probability=None)
    CDMFactory(collision_probability_multistep=Decimal('0.02'), collision_probability=None)

    response = client.get('/api/dashboard-data/', {'pc_model': 'multistep'})
    assert response.status_code == 200

    payload = response.json()
    bins = payload['collision_probability_distribution']

    # Low bins
    assert bins['0-1e-6'] == 2
    assert bins['1e-6-1e-5'] == 0
    # High bins
    assert bins['1e-2-0.1'] == 2

    stats = payload['statistics']
    assert stats['selected_probability_model'] == 'multistep'
    assert stats['high_risk_count'] == 2
    assert stats['low_risk_count'] == 2


@pytest.mark.django_db
def test_dashboard_uses_selected_probability_model(client):
    # The same CDM has different probabilities by model.
    CDMFactory(
        collision_probability_multistep=Decimal('0.02'),
        collision_probability_alfano=Decimal('0.0000002'),
        collision_probability_monte_carlo=Decimal('0.0002'),
        collision_probability=Decimal('0.02'),
    )

    resp_multi = client.get('/api/dashboard-data/', {'pc_model': 'multistep'})
    resp_alfano = client.get('/api/dashboard-data/', {'pc_model': 'alfano'})

    assert resp_multi.status_code == 200
    assert resp_alfano.status_code == 200

    multi = resp_multi.json()
    alfano = resp_alfano.json()

    assert multi['statistics']['selected_probability_model'] == 'multistep'
    assert alfano['statistics']['selected_probability_model'] == 'alfano'

    # For multistep, 0.02 falls in 1e-2-0.1.
    assert multi['collision_probability_distribution']['1e-2-0.1'] == 1
    # For alfano, 2e-7 falls in 0-1e-6.
    assert alfano['collision_probability_distribution']['0-1e-6'] == 1

    # Sanity check: model switch changes risk classification.
    assert multi['statistics']['high_risk_count'] == 1
    assert alfano['statistics']['high_risk_count'] == 0


@pytest.mark.django_db
def test_dashboard_invalid_model_falls_back_to_multistep(client):
    CDMFactory(collision_probability_multistep=Decimal('0.005'), collision_probability=Decimal('0.005'))

    response = client.get('/api/dashboard-data/', {'pc_model': 'not_a_model'})
    assert response.status_code == 200
    payload = response.json()

    assert payload['statistics']['selected_probability_model'] == 'multistep'
    assert payload['collision_probability_distribution']['1e-3-1e-2'] == 1
