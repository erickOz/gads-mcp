import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.budgets import (
    create_shared_budget,
    list_shared_budgets,
    assign_campaign_budget,
)


def _client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.budgets.get_ads_client", return_value=mock_client
    )
    return mock_client, mock_client.get_service.return_value


def _result(resource_name):
    r = MagicMock()
    r.resource_name = resource_name
    return r


def test_create_shared_budget_returns_id_and_amount(mocker):
    _c, service = _client(mocker)
    service.mutate_campaign_budgets.return_value.results = [
        _result("customers/123/campaignBudgets/777")
    ]

    result = create_shared_budget("123", "Portfolio", amount_micros=20_000_000)

    service.mutate_campaign_budgets.assert_called_once()
    assert result["budget_id"] == "777"
    assert result["amount_usd"] == 20.0


def test_list_shared_budgets_maps_flat_keys(mocker):
    mock_execute = mocker.patch("ads_mcp.tools.budgets.execute_gaql")
    mock_execute.return_value = {
        "data": [
            {
                "campaign_budget.id": "777",
                "campaign_budget.name": "Portfolio",
                "campaign_budget.amount_micros": 20_000_000,
                "campaign_budget.reference_count": 3,
                "campaign_budget.delivery_method": "STANDARD",
                "campaign_budget.status": "ENABLED",
                "campaign_budget.resource_name": "customers/123/campaignBudgets/777",
            }
        ]
    }

    result = list_shared_budgets("123")

    assert result["total"] == 1
    b = result["shared_budgets"][0]
    assert b["budget_id"] == "777"
    assert b["amount_usd"] == 20.0
    assert b["campaigns_count"] == 3


def test_assign_campaign_budget(mocker):
    _c, service = _client(mocker)
    service.mutate_campaigns.return_value.results = [
        _result("customers/123/campaigns/555")
    ]

    result = assign_campaign_budget("123", "555", "777")

    service.mutate_campaigns.assert_called_once()
    assert result["campaign_id"] == "555"
    assert result["budget_id"] == "777"
