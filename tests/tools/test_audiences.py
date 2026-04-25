import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.api import get_ads_client, execute_gaql
from ads_mcp.tools.audiences import list_audiences, create_audience, apply_audience_to_ad_group

@pytest.fixture(autouse=True)
def mock_ads_client(mocker):
    mocker.patch("ads_mcp.tools.api.get_ads_client")

def test_list_audiences(mocker):
    mock_execute_gaql = mocker.patch("ads_mcp.tools.audiences.execute_gaql")
    mock_execute_gaql.return_value = {
        "data": [
            {
                "user_list": {
                    "resource_name": "customers/123/userLists/456",
                    "id": "456",
                    "name": "All Visitors 30 Days",
                    "type": "REMARKETING",
                    "membership_status": "OPEN",
                    "size_for_search": 10000
                }
            }
        ]
    }

    result = list_audiences("123")

    mock_execute_gaql.assert_called_once()
    assert "audiences" in result
    assert len(result["audiences"]) == 1
    audience = result["audiences"][0]
    assert audience["id"] == "456"
    assert audience["name"] == "All Visitors 30 Days"
    assert audience["type"] == "REMARKETING"
    assert audience["size_for_search"] == 10000

def test_create_audience(mocker):
    mock_client = MagicMock()
    mocker.patch("ads_mcp.tools.audiences.get_ads_client", return_value=mock_client)
    mock_service = mock_client.get_service.return_value
    mock_result = MagicMock()
    mock_result.resource_name = "customers/123/userLists/789"
    mock_service.mutate_user_lists.return_value.results = [mock_result]

    name = "Test Audience"
    description = "A test audience for website visitors"
    rule_items = [{"url_contains": "/test"}]
    membership_lifespan_days = 60

    result = create_audience(
        customer_id="123",
        name=name,
        description=description,
        rule_items=rule_items,
        membership_lifespan_days=membership_lifespan_days,
    )

    mock_client.get_service.assert_called_with("UserListService")
    mock_service.mutate_user_lists.assert_called_once()
    assert "resource_name" in result
    assert "id" in result
    assert result["id"] == "789"

def test_apply_audience_to_ad_group(mocker):
    mock_client = MagicMock()
    mocker.patch("ads_mcp.tools.audiences.get_ads_client", return_value=mock_client)
    mock_service = mock_client.get_service.return_value
    mock_result = MagicMock()
    mock_result.resource_name = "customers/123/adGroupCriteria/456~789"
    mock_service.mutate_ad_group_criteria.return_value.results = [mock_result]

    ad_group_id = "456"
    user_list_rn = "customers/123/userLists/789"

    result = apply_audience_to_ad_group(
        customer_id="123",
        ad_group_id=ad_group_id,
        user_list_resource_name=user_list_rn,
    )

    mock_client.get_service.assert_called_with("AdGroupCriterionService")
    mock_service.mutate_ad_group_criteria.assert_called_once()
    assert "resource_name" in result
    assert result["resource_name"] == "customers/123/adGroupCriteria/456~789"
