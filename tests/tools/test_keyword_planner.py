import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.keyword_planner import generate_keyword_ideas


def _idea(text, searches, low_micros, high_micros):
    idea = MagicMock()
    idea.text = text
    m = idea.keyword_idea_metrics
    m.avg_monthly_searches = searches
    m.competition.name = "LOW"
    m.competition_index = 25
    m.low_top_of_page_bid_micros = low_micros
    m.high_top_of_page_bid_micros = high_micros
    return idea


def test_generate_keyword_ideas_maps_metrics(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.keyword_planner.get_ads_client", return_value=mock_client
    )
    service = mock_client.get_service.return_value
    service.generate_keyword_ideas.return_value = [
        _idea("zapatos lima", 1000, 500_000, 2_000_000),
        _idea("botas mujer", 500, 300_000, 1_500_000),
    ]

    out = generate_keyword_ideas("123", ["zapatos"], geo_target_ids=["1003840"])

    assert out["total"] == 2
    first = out["keyword_ideas"][0]
    assert first["keyword"] == "zapatos lima"
    assert first["avg_monthly_searches"] == 1000
    assert first["low_cpc_usd"] == 0.5
    assert first["high_cpc_usd"] == 2.0
