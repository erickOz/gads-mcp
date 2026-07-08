import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.mutate import (
    _coerce_list,
    add_keywords,
    add_negative_keywords,
    update_keyword_status,
    update_keyword_bid,
    create_ad_group,
)


def _mock_client(mocker, results):
    """Patches get_ads_client and returns (client, service) mocks.

    `results` is the list assigned to every mutate_* call's .results.
    """
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.mutate.get_ads_client", return_value=mock_client
    )
    service = mock_client.get_service.return_value
    for mutate_method in (
        "mutate_ad_group_criteria",
        "mutate_ad_groups",
    ):
        getattr(service, mutate_method).return_value.results = results
    return mock_client, service


def _results(*resource_names):
    out = []
    for rn in resource_names:
        r = MagicMock()
        r.resource_name = rn
        out.append(r)
    return out


def test_add_keywords_builds_one_op_per_keyword(mocker):
    _client, service = _mock_client(
        mocker,
        _results(
            "customers/123/adGroupCriteria/456~1",
            "customers/123/adGroupCriteria/456~2",
        ),
    )

    result = add_keywords("123", "456", ["zapatos", "botas"], match_type="EXACT")

    service.mutate_ad_group_criteria.assert_called_once()
    _, kwargs = service.mutate_ad_group_criteria.call_args
    assert kwargs["customer_id"] == "123"
    assert len(kwargs["operations"]) == 2  # one op per keyword
    assert result["added"] == 2
    assert len(result["resource_names"]) == 2


def test_coerce_list_parses_json_string_to_list():
    # MCP sometimes serializes list args as JSON strings; _coerce_list (run as a
    # pydantic BeforeValidator at the MCP boundary) normalizes them back.
    assert _coerce_list('["a", "b"]') == ["a", "b"]


def test_coerce_list_wraps_plain_string_and_passes_lists_through():
    assert _coerce_list("plain") == ["plain"]  # non-JSON string -> single item
    assert _coerce_list(["x", "y"]) == ["x", "y"]  # already a list


def test_add_negative_keywords(mocker):
    _client, service = _mock_client(
        mocker, _results("customers/123/adGroupCriteria/456~9")
    )

    result = add_negative_keywords("123", "456", ["gratis"])

    service.mutate_ad_group_criteria.assert_called_once()
    assert result["added"] == 1


def test_update_keyword_status_sets_status_and_count(mocker):
    _client, service = _mock_client(
        mocker,
        _results(
            "customers/123/adGroupCriteria/456~1",
            "customers/123/adGroupCriteria/456~2",
        ),
    )

    result = update_keyword_status("123", "456", ["1", "2"], status="PAUSED")

    assert result["updated"] == 2
    assert result["status"] == "PAUSED"


def test_update_keyword_bid_reports_micros_and_currency(mocker):
    _client, service = _mock_client(
        mocker, _results("customers/123/adGroupCriteria/456~1")
    )

    result = update_keyword_bid("123", "456", ["1"], cpc_bid_micros=1_500_000)

    assert result["updated"] == 1
    assert result["cpc_bid_micros"] == 1_500_000
    assert result["cpc_bid_currency"] == 1.5


def test_create_ad_group_extracts_id_from_resource_name(mocker):
    _client, service = _mock_client(
        mocker, _results("customers/123/adGroups/789")
    )

    result = create_ad_group("123", "555", "Brand", cpc_bid_micros=1_000_000)

    service.mutate_ad_groups.assert_called_once()
    assert result["resource_name"] == "customers/123/adGroups/789"
    assert result["ad_group_id"] == "789"
