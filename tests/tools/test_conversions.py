import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.conversions import (
    create_conversion_action,
    upload_click_conversions,
)


def _client(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.conversions.get_ads_client", return_value=mock_client
    )
    return mock_client, mock_client.get_service.return_value


def test_create_conversion_action_returns_id(mocker):
    _c, service = _client(mocker)
    result = MagicMock()
    result.resource_name = "customers/123/conversionActions/9001"
    service.mutate_conversion_actions.return_value.results = [result]

    out = create_conversion_action("123", "Lead Form", category="LEAD")

    service.mutate_conversion_actions.assert_called_once()
    assert out["conversion_id"] == "9001"
    assert out["category"] == "LEAD"


def test_upload_click_conversions_counts_successes(mocker):
    _c, service = _client(mocker)
    response = service.upload_click_conversions.return_value
    # Two rows; only those with a truthy gclid count as successful.
    ok = MagicMock(gclid="abc")
    bad = MagicMock(gclid="")
    response.results = [ok, bad]
    response.partial_failure_error.code = 0  # no partial failures to parse

    out = upload_click_conversions(
        "123",
        [
            {
                "gclid": "abc",
                "conversion_action_id": "9001",
                "conversion_date_time": "2026-01-15 14:30:00+00:00",
                "conversion_value": 50.0,
            },
            {
                "gclid": "def",
                "conversion_action_id": "9001",
                "conversion_date_time": "2026-01-15 14:31:00+00:00",
                "conversion_value": 25.0,
            },
        ],
    )

    assert out["successful_count"] == 1
    assert out["failed_count"] == 1


def test_upload_click_conversions_rejects_empty(mocker):
    _client(mocker)
    with pytest.raises(Exception, match="cannot be empty"):
        upload_click_conversions("123", [])
