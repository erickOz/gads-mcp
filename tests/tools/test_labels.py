import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.labels import create_label, list_labels, apply_labels


def _client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.labels.get_ads_client", return_value=mock_client
    )
    return mock_client, mock_client.get_service.return_value


def _result(resource_name):
    r = MagicMock()
    r.resource_name = resource_name
    return r


def test_create_label_returns_id(mocker):
    _c, service = _client(mocker)
    service.mutate_labels.return_value.results = [
        _result("customers/123/labels/42")
    ]

    result = create_label("123", "Brand", description="branded terms")

    service.mutate_labels.assert_called_once()
    assert result["label_id"] == "42"
    assert result["name"] == "Brand"


def test_list_labels_maps_flat_keys(mocker):
    mock_execute = mocker.patch("ads_mcp.tools.labels.execute_gaql")
    mock_execute.return_value = {
        "data": [
            {
                "label.id": "42",
                "label.name": "Brand",
                "label.status": "ENABLED",
                "label.text_label.description": "branded terms",
                "label.text_label.background_color": "#FF0000",
            }
        ]
    }

    result = list_labels("123")

    assert result["total"] == 1
    assert result["labels"][0]["label_id"] == "42"


def test_apply_labels_to_campaigns(mocker):
    _c, service = _client(mocker)
    service.mutate_campaign_labels.return_value.results = [
        _result("x"),
        _result("y"),
    ]

    result = apply_labels("123", "42", entity_type="CAMPAIGN", entity_ids=["1", "2"])

    service.mutate_campaign_labels.assert_called_once()
    assert result["applied"] == 2
    assert result["entity_type"] == "CAMPAIGN"


def test_apply_labels_requires_ad_group_for_keyword(mocker):
    _client(mocker)
    with pytest.raises(Exception, match="ad_group_id is required"):
        apply_labels("123", "42", entity_type="KEYWORD", entity_ids=["1"])
