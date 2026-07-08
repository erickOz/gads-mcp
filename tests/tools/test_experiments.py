import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.experiments import (
    create_experiment,
    list_experiments,
    schedule_experiment,
    end_experiment,
)


def _client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.experiments.get_ads_client", return_value=mock_client
    )
    return mock_client, mock_client.get_service.return_value


def _result(resource_name):
    r = MagicMock()
    r.resource_name = resource_name
    return r


def test_create_experiment_builds_two_arms(mocker):
    _c, service = _client(mocker)
    service.mutate_experiments.return_value.results = [
        _result("customers/123/experiments/77")
    ]
    service.mutate_experiment_arms.return_value.results = [
        _result("customers/123/experimentArms/77~control"),
        _result("customers/123/experimentArms/77~treatment"),
    ]

    result = create_experiment("123", "Test A", campaign_id="555", traffic_split_percent=40)

    assert result["experiment_id"] == "77"
    assert result["status"] == "SETUP"
    assert result["traffic_split"] == "60/40"


def test_create_experiment_rejects_bad_split(mocker):
    _client(mocker)
    with pytest.raises(Exception, match="between 1 and 99"):
        create_experiment("123", "x", campaign_id="555", traffic_split_percent=0)


def test_list_experiments_validates_status_filter(mocker):
    mocker.patch("ads_mcp.tools.experiments.execute_gaql")
    with pytest.raises(Exception, match="Must be one of"):
        list_experiments("123", status_filter="BOGUS")


def test_list_experiments_maps_flat_keys(mocker):
    mock_execute = mocker.patch("ads_mcp.tools.experiments.execute_gaql")
    mock_execute.return_value = {
        "data": [
            {
                "experiment.id": "77",
                "experiment.name": "Test A",
                "experiment.status": "SETUP",
                "experiment.resource_name": "customers/123/experiments/77",
            }
        ]
    }

    result = list_experiments("123")

    assert result["total"] == 1
    assert result["experiments"][0]["experiment_id"] == "77"


def test_schedule_experiment_returns_initiated(mocker):
    _client(mocker)
    out = schedule_experiment("123", "77")
    assert out["status"] == "INITIATED"


def test_end_experiment_returns_ended(mocker):
    _client(mocker)
    out = end_experiment("123", "77")
    assert out["status"] == "ENDED"
