import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.bidding_strategies import (
    create_portfolio_bidding_strategy,
    list_portfolio_bidding_strategies,
    assign_portfolio_strategy,
)


def _client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.bidding_strategies.get_ads_client",
        return_value=mock_client,
    )
    return mock_client, mock_client.get_service.return_value


def _result(resource_name):
    r = MagicMock()
    r.resource_name = resource_name
    return r


def test_create_portfolio_strategy_target_cpa(mocker):
    _c, service = _client(mocker)
    service.mutate_bidding_strategies.return_value.results = [
        _result("customers/123/biddingStrategies/888")
    ]

    result = create_portfolio_bidding_strategy(
        "123", "tCPA Lima", strategy_type="TARGET_CPA", target_cpa_micros=5_000_000
    )

    service.mutate_bidding_strategies.assert_called_once()
    assert result["strategy_id"] == "888"
    assert result["strategy_type"] == "TARGET_CPA"


def test_list_portfolio_strategies_maps_flat_keys(mocker):
    mock_execute = mocker.patch(
        "ads_mcp.tools.bidding_strategies.execute_gaql"
    )
    mock_execute.return_value = {
        "data": [
            {
                "bidding_strategy.id": "888",
                "bidding_strategy.name": "tCPA Lima",
                "bidding_strategy.type": "TARGET_CPA",
                "bidding_strategy.status": "ENABLED",
                "bidding_strategy.campaign_count": 4,
                "bidding_strategy.non_removed_campaign_count": 3,
                "bidding_strategy.resource_name": "customers/123/biddingStrategies/888",
            }
        ]
    }

    result = list_portfolio_bidding_strategies("123")

    assert result["total"] == 1
    s = result["strategies"][0]
    assert s["strategy_id"] == "888"
    assert s["active_campaigns"] == 3


def test_assign_portfolio_strategy(mocker):
    _c, service = _client(mocker)
    service.mutate_campaigns.return_value.results = [
        _result("customers/123/campaigns/555")
    ]

    result = assign_portfolio_strategy("123", "555", "888")

    service.mutate_campaigns.assert_called_once()
    assert result["campaign_id"] == "555"
    assert result["strategy_id"] == "888"
