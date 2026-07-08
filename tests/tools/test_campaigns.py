import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.campaigns import (
    create_campaign,
    update_campaign_status,
    update_campaign_budget,
)


def _client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.campaigns.get_ads_client", return_value=mock_client
    )
    return mock_client, mock_client.get_service.return_value


def _result(resource_name):
    r = MagicMock()
    r.resource_name = resource_name
    return r


def test_create_campaign_creates_budget_then_campaign(mocker):
    _c, service = _client(mocker)
    # Two-step mutate: budget first, then campaign.
    service.mutate_campaign_budgets.return_value.results = [
        _result("customers/123/campaignBudgets/10")
    ]
    service.mutate_campaigns.return_value.results = [
        _result("customers/123/campaigns/20")
    ]

    result = create_campaign("123", "Search Brand", daily_budget_micros=10_000_000)

    service.mutate_campaign_budgets.assert_called_once()
    service.mutate_campaigns.assert_called_once()
    assert result["campaign_id"] == "20"
    assert result["budget_resource_name"] == "customers/123/campaignBudgets/10"


def test_create_campaign_target_cpa_requires_micros(mocker):
    _client(mocker)
    with pytest.raises(Exception, match="target_cpa_micros is required"):
        create_campaign(
            "123", "x", daily_budget_micros=10_000_000, bidding_strategy="TARGET_CPA"
        )


def test_create_campaign_target_roas_requires_value(mocker):
    _client(mocker)
    with pytest.raises(Exception, match="target_roas is required"):
        create_campaign(
            "123", "x", daily_budget_micros=10_000_000, bidding_strategy="TARGET_ROAS"
        )


def test_update_campaign_status(mocker):
    _c, service = _client(mocker)
    service.mutate_campaigns.return_value.results = [
        _result("customers/123/campaigns/20")
    ]

    result = update_campaign_status("123", "20", status="PAUSED")

    service.mutate_campaigns.assert_called_once()
    assert result["resource_name"] == "customers/123/campaigns/20"


def test_update_campaign_budget(mocker):
    _c, service = _client(mocker)
    service.mutate_campaign_budgets.return_value.results = [
        _result("customers/123/campaignBudgets/10")
    ]

    result = update_campaign_budget("123", "10", daily_budget_micros=15_000_000)

    service.mutate_campaign_budgets.assert_called_once()
    assert "resource_name" in result
