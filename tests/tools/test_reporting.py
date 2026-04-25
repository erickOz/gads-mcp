import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.api import execute_gaql, get_ads_client
from ads_mcp.tools.reporting import get_campaign_performance, DATE_RANGES


@pytest.fixture(autouse=True)
def mock_ads_client(mocker):
    mocker.patch("ads_mcp.tools.api.get_ads_client")

def test_get_campaign_performance_invalid_date_range():
    with pytest.raises(Exception, match="Invalid date_range"):
        get_campaign_performance("123", "INVALID_RANGE")

def test_get_campaign_performance_success_all_campaigns(mocker):
    mock_execute_gaql = mocker.patch("ads_mcp.tools.reporting.execute_gaql")
    mock_execute_gaql.return_value = {
        "data": [
            {
                "campaign": {"id": "1", "name": "Campaign A"},
                "metrics": {
                    "impressions": 1000,
                    "clicks": 100,
                    "cost_micros": 100000000,
                    "conversions": 10.0,
                    "ctr": 0.1,
                    "average_cpc": 1000000,
                },
            },
            {
                "campaign": {"id": "2", "name": "Campaign B"},
                "metrics": {
                    "impressions": 500,
                    "clicks": 50,
                    "cost_micros": 50000000,
                    "conversions": 5.0,
                    "ctr": 0.1,
                    "average_cpc": 1000000,
                },
            },
        ]
    }

    result = get_campaign_performance("123", "LAST_7_DAYS")

    mock_execute_gaql.assert_called_once()
    assert "campaign_performance" in result
    assert len(result["campaign_performance"]) == 2
    assert result["campaign_performance"][0]["campaign_id"] == "1"
    assert result["campaign_performance"][0]["cost"] == 100.0
    assert result["campaign_performance"][0]["average_cpc"] == 1.0

def test_get_campaign_performance_success_filtered_campaigns(mocker):
    mock_execute_gaql = mocker.patch("ads_mcp.tools.reporting.execute_gaql")
    mock_execute_gaql.return_value = {
        "data": [
            {
                "campaign": {"id": "1", "name": "Campaign A"},
                "metrics": {
                    "impressions": 1000,
                    "clicks": 100,
                    "cost_micros": 100000000,
                    "conversions": 10.0,
                    "ctr": 0.1,
                    "average_cpc": 1000000,
                },
            }
        ]
    }

    result = get_campaign_performance("123", "LAST_7_DAYS", campaign_ids=["1"])

    mock_execute_gaql.assert_called_once()
    assert "campaign_performance" in result
    assert len(result["campaign_performance"]) == 1
    assert result["campaign_performance"][0]["campaign_id"] == "1"

def test_get_campaign_performance_empty_data(mocker):
    mock_execute_gaql = mocker.patch("ads_mcp.tools.reporting.execute_gaql")
    mock_execute_gaql.return_value = {"data": []}

    result = get_campaign_performance("123", "THIS_MONTH")

    assert "campaign_performance" in result
    assert len(result["campaign_performance"]) == 0
