import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.targeting import (
    add_location_targets,
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


def test_list_campaign_locations_parses_geo_id_from_resource(mocker):
    mock_execute = mocker.patch("ads_mcp.tools.targeting.execute_gaql")
    mock_execute.return_value = {
        "data": [
            {
                "campaign_criterion.criterion_id": "1",
                "campaign_criterion.negative": False,
                "campaign_criterion.location.geo_target_constant": "geoTargetConstants/2604",
                "geo_target_constant.name": "Peru",
                "geo_target_constant.country_code": "PE",
                "geo_target_constant.target_type": "Country",
                "geo_target_constant.canonical_name": "Peru",
            }
        ]
    }

    result = list_campaign_locations("123", "555")

    assert result["count"] == 1
    loc = result["locations"][0]
    assert loc["geo_target_id"] == "2604"
    assert loc["country_code"] == "PE"


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
