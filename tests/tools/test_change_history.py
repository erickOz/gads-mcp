import pytest

from ads_mcp.tools.change_history import get_change_history


def test_get_change_history_maps_flat_keys(mocker):
    mock_execute = mocker.patch("ads_mcp.tools.change_history.execute_gaql")
    mock_execute.return_value = {
        "data": [
            {
                "change_event.change_date_time": "2026-07-01 10:00:00",
                "change_event.change_resource_type": "CAMPAIGN",
                "change_event.change_resource_name": "customers/123/campaigns/9",
                "change_event.resource_change_operation": "UPDATE",
                "change_event.changed_fields": "campaign.status",
                "change_event.user_email": "user@example.com",
                "change_event.client_type": "GOOGLE_ADS_WEB_CLIENT",
            }
        ]
    }

    result = get_change_history("123", "2026-07-01")

    assert result["total"] == 1
    change = result["changes"][0]
    assert change["resource_type"] == "CAMPAIGN"
    assert change["user_email"] == "user@example.com"


def test_get_change_history_rejects_bad_date(mocker):
    # start_date is interpolated into a GAQL string literal.
    mocker.patch("ads_mcp.tools.change_history.execute_gaql")
    with pytest.raises(Exception, match="YYYY-MM-DD"):
        get_change_history("123", "2026-07-01' OR '1'='1")


def test_get_change_history_rejects_bad_resource_type(mocker):
    mocker.patch("ads_mcp.tools.change_history.execute_gaql")
    with pytest.raises(Exception, match="Must be one of"):
        get_change_history("123", "2026-07-01", resource_type="BOGUS")
