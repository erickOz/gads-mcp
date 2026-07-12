import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.assets import (
    add_callout_assets,
    add_sitelink_assets,
    list_assets,
    remove_assets,
)


def _client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.assets.get_ads_client", return_value=mock_client
    )
    return mock_client, mock_client.get_service.return_value


def _result(resource_name):
    r = MagicMock()
    r.resource_name = resource_name
    return r


def test_add_callout_assets_account_level(mocker):
    _c, service = _client(mocker)
    service.mutate_assets.return_value.results = [
        _result("customers/123/assets/1"),
        _result("customers/123/assets/2"),
    ]
    # ACCOUNT level links via mutate_customer_assets.
    service.mutate_customer_assets.return_value.results = [
        _result("customers/123/customerAssets/1~CALLOUT"),
        _result("customers/123/customerAssets/2~CALLOUT"),
    ]

    out = add_callout_assets("123", ["Envío gratis", "Soporte 24/7"])

    service.mutate_assets.assert_called_once()
    assert out["assets_created"] == 2
    assert out["level"] == "ACCOUNT"


def test_add_callout_assets_rejects_too_long(mocker):
    _client(mocker)
    with pytest.raises(Exception, match="exceed 25 characters"):
        add_callout_assets("123", ["x" * 26])


def test_add_callout_assets_campaign_level_requires_campaign_id(mocker):
    _client(mocker)
    with pytest.raises(Exception, match="campaign_id is required"):
        add_callout_assets("123", ["Envío gratis"], level="CAMPAIGN")


def test_add_sitelink_assets_account_level(mocker):
    _c, service = _client(mocker)
    service.mutate_assets.return_value.results = [_result("customers/123/assets/1")]
    service.mutate_customer_assets.return_value.results = [
        _result("customers/123/customerAssets/1~SITELINK")
    ]

    out = add_sitelink_assets(
        "123",
        [{"link_text": "Contacto", "final_url": "https://x.com/c"}],
    )

    service.mutate_assets.assert_called_once()
    assert out["assets_created"] == 1


def test_add_sitelink_assets_requires_final_url(mocker):
    _client(mocker)
    with pytest.raises(Exception, match="link_text and final_url are required"):
        add_sitelink_assets("123", [{"link_text": "Solo texto"}])


def test_list_assets_maps_callout_content(mocker):
    mock_execute = mocker.patch("ads_mcp.tools.assets.execute_gaql")
    mock_execute.return_value = {
        "data": [
            {
                "customer_asset.resource_name": "customers/123/customerAssets/1~CALLOUT",
                "customer_asset.field_type": "CALLOUT",
                "asset.id": "1",
                "asset.resource_name": "customers/123/assets/1",
                "asset.type": "CALLOUT",
                "asset.callout_asset.callout_text": "Envío gratis",
            }
        ]
    }

    out = list_assets("123")

    assert out["count"] == 1
    entry = out["assets"][0]
    assert entry["field_type"] == "CALLOUT"
    assert entry["callout_text"] == "Envío gratis"


def test_remove_assets_counts_removed(mocker):
    _c, service = _client(mocker)
    service.mutate_customer_assets.return_value.results = [
        _result("x"),
        _result("y"),
    ]

    out = remove_assets(
        "123",
        ["customers/123/customerAssets/1~CALLOUT", "customers/123/customerAssets/2~CALLOUT"],
        level="ACCOUNT",
    )

    assert out["removed"] == 2
    assert out["level"] == "ACCOUNT"
