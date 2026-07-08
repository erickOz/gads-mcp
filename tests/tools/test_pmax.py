import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.pmax import create_performance_max_campaign


def _result(resource_name):
    r = MagicMock()
    r.resource_name = resource_name
    return r


def test_create_pmax_orchestrates_all_steps(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.pmax.get_ads_client", return_value=mock_client
    )
    service = mock_client.get_service.return_value
    service.mutate_campaign_budgets.return_value.results = [
        _result("customers/123/campaignBudgets/500")
    ]
    service.mutate_campaigns.return_value.results = [
        _result("customers/123/campaigns/600")
    ]
    service.mutate_asset_groups.return_value.results = [
        _result("customers/123/assetGroups/700")
    ]
    # 3 headlines + 1 long + 2 descriptions + 1 business_name = 7 text assets
    service.mutate_assets.return_value.results = [
        _result(f"customers/123/assets/{i}") for i in range(7)
    ]

    out = create_performance_max_campaign(
        customer_id="123",
        name="PMax Store",
        daily_budget_micros=30_000_000,
        final_url="https://example.com",
        business_name="Mi Tienda",
        headlines=["h1", "h2", "h3"],
        long_headlines=["long headline one"],
        descriptions=["desc one", "desc two"],
    )

    service.mutate_campaign_budgets.assert_called_once()
    service.mutate_campaigns.assert_called_once()
    service.mutate_asset_groups.assert_called_once()
    service.mutate_assets.assert_called_once()
    service.mutate_asset_group_assets.assert_called_once()

    assert out["campaign_id"] == "600"
    assert out["asset_group_id"] == "700"
    assert out["text_assets_created"] == 7
    assert out["status"] == "PAUSED"
