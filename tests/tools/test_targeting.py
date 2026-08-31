import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.targeting import (
    add_location_targets,
    list_ad_group_demographics,
    list_campaign_locations,
    remove_campaign_criteria,
)


def _results(*resource_names):
    out = []
    for rn in resource_names:
        r = MagicMock()
        r.resource_name = rn
        out.append(r)
    return out


def test_add_location_targets_one_op_per_geo(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.targeting.get_ads_client", return_value=mock_client
    )
    service = mock_client.get_service.return_value
    service.mutate_campaign_criteria.return_value.results = _results(
        "customers/123/campaignCriteria/555~1",
        "customers/123/campaignCriteria/555~2",
    )

    # 2604 = Peru, 1003840 = Lima
    result = add_location_targets("123", "555", ["2604", "1003840"])

    service.mutate_campaign_criteria.assert_called_once()
    _, kwargs = service.mutate_campaign_criteria.call_args
    assert len(kwargs["operations"]) == 2
    assert result["added"] == 2
    assert result["negative"] is False


def _location_responses():
    """The two payloads list_campaign_locations reads, in call order."""
    criteria = {
        "data": [
            {
                "campaign_criterion.criterion_id": "1",
                "campaign_criterion.negative": False,
                "campaign_criterion.location.geo_target_constant": "geoTargetConstants/2604",
            }
        ]
    }
    geo = {
        "data": [
            {
                "geo_target_constant.id": "2604",
                "geo_target_constant.name": "Peru",
                "geo_target_constant.country_code": "PE",
                "geo_target_constant.target_type": "Country",
                "geo_target_constant.canonical_name": "Peru",
            }
        ]
    }
    return [criteria, geo]


def test_list_campaign_locations_parses_geo_id_from_resource(mocker):
    mock_execute = mocker.patch("ads_mcp.tools.targeting.execute_gaql")
    mock_execute.side_effect = _location_responses()

    result = list_campaign_locations("123", "555")

    assert result["count"] == 1
    loc = result["locations"][0]
    assert loc["geo_target_id"] == "2604"
    assert loc["country_code"] == "PE"
    assert loc["name"] == "Peru"


def test_list_campaign_locations_resolves_geo_names_separately(mocker):
    # Regression guard for B-12: v24 rejects selecting geo_target_constant.*
    # from campaign_criterion (PROHIBITED_RESOURCE_TYPE_IN_SELECT_CLAUSE), so
    # the names must come from a second query against geo_target_constant.
    mock_execute = mocker.patch("ads_mcp.tools.targeting.execute_gaql")
    mock_execute.side_effect = _location_responses()

    list_campaign_locations("123", "555")

    assert mock_execute.call_count == 2
    criteria_query = mock_execute.call_args_list[0].kwargs["query"]
    assert "geo_target_constant." not in criteria_query
    geo_query = mock_execute.call_args_list[1].kwargs["query"]
    assert "FROM geo_target_constant" in geo_query
    assert "IN (2604)" in geo_query


def test_list_campaign_locations_skips_geo_lookup_when_empty(mocker):
    # No LOCATION criteria means no IDs to resolve: the second query would be
    # an `IN ()` that the API rejects, so it must not be issued at all.
    mock_execute = mocker.patch("ads_mcp.tools.targeting.execute_gaql")
    mock_execute.return_value = {"data": []}

    result = list_campaign_locations("123", "555")

    assert result["count"] == 0
    assert mock_execute.call_count == 1


def test_list_ad_group_demographics_filters_by_campaign_id(mocker):
    # Regression guard for B-12: `ad_group.campaign.id` is not a v24 field
    # (UNRECOGNIZED_FIELD). From ad_group_criterion the filter is `campaign.id`.
    mock_execute = mocker.patch("ads_mcp.tools.targeting.execute_gaql")
    mock_execute.return_value = {"data": []}

    list_ad_group_demographics("123", "555")

    age_gender_query = mock_execute.call_args_list[0].kwargs["query"]
    assert "ad_group.campaign.id" not in age_gender_query
    assert "WHERE campaign.id = 555" in age_gender_query


def test_list_campaign_locations_rejects_non_numeric_campaign_id(mocker):
    # campaign_id is interpolated unquoted into the GAQL WHERE clause.
    mocker.patch("ads_mcp.tools.targeting.execute_gaql")
    with pytest.raises(Exception, match="must contain digits only"):
        list_campaign_locations("123", "555 OR 1=1")


def test_remove_campaign_criteria_counts_input(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.targeting.get_ads_client", return_value=mock_client
    )
    rns = [
        "customers/123/campaignCriteria/555~1",
        "customers/123/campaignCriteria/555~2",
    ]

    result = remove_campaign_criteria("123", rns)

    mock_client.get_service.return_value.mutate_campaign_criteria.assert_called_once()
    assert result["removed"] == 2
