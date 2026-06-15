"""Keyword Planner tools — research keyword ideas and traffic forecasts."""

from typing import Any, Literal

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import get_ads_client


KeywordPlanNetwork = Literal["GOOGLE_SEARCH", "GOOGLE_SEARCH_AND_PARTNERS"]

# Common language constant IDs
_LANGUAGE_IDS = {
    "en": 1000,
    "es": 1003,
    "pt": 1014,
    "fr": 1002,
    "de": 1001,
    "it": 1004,
    "ja": 1005,
    "ko": 1012,
    "zh": 1017,
    "ar": 1019,
}


@mcp.tool()
def generate_keyword_ideas(
    customer_id: str,
    seed_keywords: list[str],
    geo_target_ids: list[str] | None = None,
    language: str = "en",
    network: KeywordPlanNetwork = "GOOGLE_SEARCH",
    include_adult_keywords: bool = False,
    page_size: int = 100,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Generates keyword ideas based on seed keywords using the Keyword Planner.

  Returns keyword suggestions with monthly search volume, competition level,
  and estimated CPC ranges. Use this to discover new keywords, validate
  search demand before creating campaigns, or find negative keywords.

  Args:
      customer_id: The ID of the customer account (digits only).
      seed_keywords: List of seed keywords to base ideas on (max 20).
      geo_target_ids: List of geo target IDs to scope search volume to
          (e.g. ["2840"] for USA, ["2032"] for Peru). Use search_geo_targets
          to find IDs. If omitted, uses global volume.
      language: Language code for results. Supported: en, es, pt, fr, de,
          it, ja, ko, zh, ar. Defaults to "en".
      network: Search network for volume data. GOOGLE_SEARCH or
          GOOGLE_SEARCH_AND_PARTNERS. Defaults to GOOGLE_SEARCH.
      include_adult_keywords: Whether to include adult-content keywords.
          Defaults to False.
      page_size: Max number of keyword ideas to return (up to 1000).
          Defaults to 100.
      login_customer_id: Optional MCC account ID.

  Returns:
      List of keyword ideas with text, avg_monthly_searches, competition,
      competition_index, low_cpc_micros, high_cpc_micros.
  """
  if not seed_keywords:
    raise ToolError("seed_keywords cannot be empty.")
  if len(seed_keywords) > 20:
    raise ToolError("seed_keywords must have 20 or fewer entries.")

  language_id = _LANGUAGE_IDS.get(language.lower())
  if language_id is None:
    raise ToolError(
        f"Unsupported language '{language}'. Supported: {', '.join(_LANGUAGE_IDS)}"
    )

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  service = ads_client.get_service("KeywordPlanIdeaService")
  request = ads_client.get_type("GenerateKeywordIdeasRequest")
  request.customer_id = customer_id
  request.language = f"languageConstants/{language_id}"
  request.include_adult_keywords = include_adult_keywords
  request.keyword_plan_network = getattr(
      ads_client.enums.KeywordPlanNetworkEnum, network
  )
  request.page_size = page_size

  if geo_target_ids:
    for geo_id in geo_target_ids:
      request.geo_target_constants.append(f"geoTargetConstants/{geo_id}")

  request.keyword_seed.keywords.extend(seed_keywords)

  try:
    response = service.generate_keyword_ideas(request=request)
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  ideas = []
  for idea in response:
    m = idea.keyword_idea_metrics
    ideas.append({
        "keyword": idea.text,
        "avg_monthly_searches": m.avg_monthly_searches,
        "competition": m.competition.name,
        "competition_index": m.competition_index,
        "low_cpc_micros": m.low_top_of_page_bid_micros,
        "high_cpc_micros": m.high_top_of_page_bid_micros,
        "low_cpc_usd": round(m.low_top_of_page_bid_micros / 1_000_000, 2),
        "high_cpc_usd": round(m.high_top_of_page_bid_micros / 1_000_000, 2),
    })

  return {
      "keyword_ideas": ideas,
      "total": len(ideas),
      "seed_keywords": seed_keywords,
      "network": network,
  }


@mcp.tool()
def get_keyword_forecast(
    customer_id: str,
    keywords: list[dict],
    campaign_start_date: str,
    campaign_end_date: str,
    daily_budget_micros: int,
    max_cpc_bid_micros: int,
    geo_target_ids: list[str] | None = None,
    language: str = "en",
    network: KeywordPlanNetwork = "GOOGLE_SEARCH",
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Forecasts traffic, clicks, cost, and conversions for a set of keywords.

  Use before launching a campaign to estimate expected performance at a given
  budget and max CPC. Helps size budgets and set realistic expectations.

  Args:
      customer_id: The ID of the customer account (digits only).
      keywords: List of dicts with keys:
          - text: keyword text
          - match_type: BROAD, PHRASE, or EXACT
      campaign_start_date: Start date in "YYYY-MM-DD" format.
      campaign_end_date: End date in "YYYY-MM-DD" format.
      daily_budget_micros: Daily budget in micros (e.g. 10_000_000 = $10/day).
      max_cpc_bid_micros: Max CPC bid in micros (e.g. 1_000_000 = $1.00).
      geo_target_ids: Optional list of geo target IDs (e.g. ["2840"] for USA).
      language: Language code (en, es, pt, ...). Defaults to "en".
      network: GOOGLE_SEARCH or GOOGLE_SEARCH_AND_PARTNERS.
      login_customer_id: Optional MCC account ID.

  Returns:
      Forecasted impressions, clicks, cost, ctr, avg_cpc, conversions.
  """
  if not keywords:
    raise ToolError("keywords cannot be empty.")

  language_id = _LANGUAGE_IDS.get(language.lower())
  if language_id is None:
    raise ToolError(
        f"Unsupported language '{language}'. Supported: {', '.join(_LANGUAGE_IDS)}"
    )

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  service = ads_client.get_service("KeywordPlanIdeaService")

  # Build a KeywordPlan for forecasting
  plan_service = ads_client.get_service("KeywordPlanService")
  campaign_service = ads_client.get_service("KeywordPlanCampaignService")
  ad_group_service = ads_client.get_service("KeywordPlanAdGroupService")
  kw_service = ads_client.get_service("KeywordPlanAdGroupKeywordService")
  forecast_service = ads_client.get_service("KeywordPlanService")

  try:
    # Create keyword plan
    plan = ads_client.get_type("KeywordPlan")
    plan.name = f"Forecast {campaign_start_date} to {campaign_end_date}"
    plan.forecast_period.date_interval = (
        ads_client.enums.KeywordPlanForecastIntervalEnum.NEXT_MONTH
    )
    plan_op = ads_client.get_type("KeywordPlanOperation")
    plan_op.create = plan
    plan_res = plan_service.mutate_keyword_plans(
        customer_id=customer_id, operations=[plan_op]
    )
    plan_resource = plan_res.results[0].resource_name

    # Create keyword plan campaign
    kp_campaign = ads_client.get_type("KeywordPlanCampaign")
    kp_campaign.keyword_plan = plan_resource
    kp_campaign.name = "Forecast Campaign"
    kp_campaign.cpc_bid_micros = max_cpc_bid_micros
    kp_campaign.keyword_plan_network = getattr(
        ads_client.enums.KeywordPlanNetworkEnum, network
    )
    kp_campaign.language_constants.append(f"languageConstants/{language_id}")
    if geo_target_ids:
      for geo_id in geo_target_ids:
        geo = ads_client.get_type("KeywordPlanGeoTarget")
        geo.geo_target_constant = f"geoTargetConstants/{geo_id}"
        kp_campaign.geo_targets.append(geo)

    camp_op = ads_client.get_type("KeywordPlanCampaignOperation")
    camp_op.create = kp_campaign
    camp_res = campaign_service.mutate_keyword_plan_campaigns(
        customer_id=customer_id, operations=[camp_op]
    )
    campaign_resource = camp_res.results[0].resource_name

    # Create keyword plan ad group
    kp_ag = ads_client.get_type("KeywordPlanAdGroup")
    kp_ag.keyword_plan_campaign = campaign_resource
    kp_ag.name = "Forecast Ad Group"
    kp_ag.cpc_bid_micros = max_cpc_bid_micros
    ag_op = ads_client.get_type("KeywordPlanAdGroupOperation")
    ag_op.create = kp_ag
    ag_res = ad_group_service.mutate_keyword_plan_ad_groups(
        customer_id=customer_id, operations=[ag_op]
    )
    ag_resource = ag_res.results[0].resource_name

    # Add keywords
    kw_ops = []
    for kw in keywords:
      kp_kw = ads_client.get_type("KeywordPlanAdGroupKeyword")
      kp_kw.keyword_plan_ad_group = ag_resource
      kp_kw.text = kw["text"]
      kp_kw.match_type = getattr(
          ads_client.enums.KeywordMatchTypeEnum,
          kw.get("match_type", "BROAD"),
      )
      kp_kw.cpc_bid_micros = max_cpc_bid_micros
      op = ads_client.get_type("KeywordPlanAdGroupKeywordOperation")
      op.create = kp_kw
      kw_ops.append(op)

    kw_service.mutate_keyword_plan_ad_group_keywords(
        customer_id=customer_id, operations=kw_ops
    )

    # Generate forecast
    forecast_response = forecast_service.generate_forecast_metrics(
        keyword_plan=plan_resource
    )
    campaign_forecasts = forecast_response.campaign_forecasts

    # Aggregate across all ad groups
    total_impressions = 0.0
    total_clicks = 0.0
    total_cost_micros = 0.0
    total_conversions = 0.0

    for cf in campaign_forecasts:
      m = cf.campaign_forecast
      total_impressions += m.impressions
      total_clicks += m.clicks
      total_cost_micros += m.cost_micros
      total_conversions += m.conversions

    # Clean up the temporary plan
    remove_op = ads_client.get_type("KeywordPlanOperation")
    remove_op.remove = plan_resource
    plan_service.mutate_keyword_plans(
        customer_id=customer_id, operations=[remove_op]
    )

  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  avg_cpc_micros = (
      total_cost_micros / total_clicks if total_clicks > 0 else 0
  )

  return {
      "impressions": round(total_impressions),
      "clicks": round(total_clicks),
      "cost_micros": round(total_cost_micros),
      "cost_usd": round(total_cost_micros / 1_000_000, 2),
      "ctr": round(total_clicks / total_impressions, 4) if total_impressions else 0,
      "avg_cpc_micros": round(avg_cpc_micros),
      "avg_cpc_usd": round(avg_cpc_micros / 1_000_000, 2),
      "conversions": round(total_conversions, 1),
      "daily_budget_usd": daily_budget_micros / 1_000_000,
      "period": f"{campaign_start_date} to {campaign_end_date}",
  }
