import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.api import get_ads_client, execute_gaql
from ads_mcp.tools.recommendations import list_recommendations, apply_recommendation

@pytest.fixture(autouse=True)
def mock_ads_client(mocker):
    mocker.patch("ads_mcp.tools.api.get_ads_client")

def test_list_recommendations(mocker):
    mock_execute_gaql = mocker.patch("ads_mcp.tools.recommendations.execute_gaql")
    mock_execute_gaql.return_value = {
        "data": [
            {
                "recommendation": {
                    "resource_name": "customers/123/recommendations/456",
                    "type": "KEYWORD",
                    "campaign": "customers/123/campaigns/789",
                    "impact": {
                        "base_metrics": {"impressions": 1000.0},
                        "metrics": {"impressions": 1200.0}
                    }
                }
            }
        ]
    }

    result = list_recommendations("123")

    mock_execute_gaql.assert_called_once()
    assert "recommendations" in result
    assert len(result["recommendations"]) == 1
    rec = result["recommendations"][0]
    assert rec["resource_name"] == "customers/123/recommendations/456"
    assert rec["type"] == "KEYWORD"
    assert rec["impact_absolute"] == 1200.0

def test_apply_recommendation(mocker):
    mock_client = MagicMock()
    mocker.patch("ads_mcp.tools.recommendations.get_ads_client", return_value=mock_client)

    mock_service = mock_client.get_service.return_value
    mock_result = MagicMock()
    mock_result.resource_name = "customers/123/recommendations/456-applied"
    mock_service.apply_recommendation.return_value.results = [mock_result]

    recommendation_rn = "customers/123/recommendations/456"
    result = apply_recommendation("123", recommendation_rn)

    mock_client.get_service.assert_called_with("RecommendationService")
    mock_service.apply_recommendation.assert_called_once()
    assert "applied_recommendation_resource_name" in result
    assert result["applied_recommendation_resource_name"] == mock_result.resource_name
