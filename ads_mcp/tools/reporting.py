"""Reporting tools for the Google Ads API."""

from typing import Any, Literal

from fastmcp.exceptions import ToolError

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import execute_gaql


DateRange = Literal[
    "TODAY",
    "YESTERDAY",
    "LAST_7_DAYS",
    "LAST_14_DAYS",
    "LAST_30_DAYS",
    "THIS_MONTH",
    "LAST_MONTH",
]


@mcp.tool()
def get_campaign_performance(
    customer_id: str,
    date_range: DateRange,
    campaign_ids: list[str] | None = None,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Retrieves key performance metrics for campaigns without writing GAQL.

  Returns impressions, clicks, cost, conversions, CTR, and average CPC.
  Cost and average_cpc are returned in the account's currency (not micros).

  Args:
      customer_id: The ID of the customer account (digits only).
      date_range: Predefined date range: TODAY, YESTERDAY, LAST_7_DAYS,
          LAST_14_DAYS, LAST_30_DAYS, THIS_MONTH, or LAST_MONTH.
      campaign_ids: Optional list of campaign IDs to filter results.
          If None, all campaigns are returned.
      login_customer_id: Optional MCC account ID.

  Returns:
      A list of campaign performance rows sorted by impressions descending.
  """
  gaql_query = f"""
    SELECT
      campaign.id,
      campaign.name,
      campaign.status,
      metrics.impressions,
      metrics.clicks,
      metrics.cost_micros,
      metrics.conversions,
      metrics.ctr,
      metrics.average_cpc
    FROM campaign
    WHERE segments.date DURING {date_range}
      AND campaign.status != 'REMOVED'
  """

  if campaign_ids:
    ids_str = ", ".join(f"'{cid}'" for cid in campaign_ids)
    gaql_query += f" AND campaign.id IN ({ids_str})"

  gaql_query += """
    ORDER BY metrics.impressions DESC
  """

  response = execute_gaql(
      query=gaql_query,
      customer_id=customer_id,
      login_customer_id=login_customer_id,
  )

  # execute_gaql returns flat keys: "campaign.id", "metrics.cost_micros", etc.
  processed_data = []
  for row in response["data"]:
    cost_micros = row.get("metrics.cost_micros", 0) or 0
    avg_cpc_micros = row.get("metrics.average_cpc", 0) or 0
    processed_data.append({
        "campaign_id": row.get("campaign.id"),
        "campaign_name": row.get("campaign.name"),
        "campaign_status": row.get("campaign.status"),
        "impressions": row.get("metrics.impressions", 0),
        "clicks": row.get("metrics.clicks", 0),
        "cost": round(cost_micros / 1_000_000, 2),
        "conversions": round(row.get("metrics.conversions", 0.0) or 0.0, 2),
        "ctr": round(row.get("metrics.ctr", 0.0) or 0.0, 4),
        "average_cpc": round(avg_cpc_micros / 1_000_000, 2),
    })

  return {"campaign_performance": processed_data}


@mcp.tool()
def get_search_terms_report(
    customer_id: str,
    date_range: DateRange,
    campaign_ids: list[str] | None = None,
    ad_group_ids: list[str] | None = None,
    min_impressions: int = 0,
    limit: int = 500,
    login_customer_id: str | None = None,
) -> dict:
  """Returns the search terms report with performance metrics.

  Critical for discovering new negative keywords and keyword expansion
  opportunities. Shows actual queries that triggered your ads.

  Use campaign_ids or ad_group_ids to scope the query and reduce response time.
  Increase min_impressions to filter noise and speed up results.

  Args:
      customer_id: The ID of the customer account (digits only).
      date_range: Predefined date range.
      campaign_ids: Optional list of campaign IDs to filter.
      ad_group_ids: Optional list of ad group IDs to filter.
      min_impressions: Only return terms with at least this many impressions.
          Defaults to 0 (all terms). Use 5-10 to reduce noise.
      limit: Maximum number of rows to return. Defaults to 500.
      login_customer_id: Optional MCC account ID.

  Returns:
      List of search terms with impressions, clicks, cost, conversions, CTR,
      avg CPC, and match status (ADDED, EXCLUDED, NONE).
  """
  gaql = f"""
    SELECT
      search_term_view.search_term,
      search_term_view.status,
      campaign.id,
      campaign.name,
      ad_group.id,
      ad_group.name,
      metrics.impressions,
      metrics.clicks,
      metrics.cost_micros,
      metrics.conversions,
      metrics.ctr,
      metrics.average_cpc
    FROM search_term_view
    WHERE segments.date DURING {date_range}
  """

  if campaign_ids:
    ids_str = ", ".join(f"'{cid}'" for cid in campaign_ids)
    gaql += f" AND campaign.id IN ({ids_str})"
  if ad_group_ids:
    ids_str = ", ".join(f"'{aid}'" for aid in ad_group_ids)
    gaql += f" AND ad_group.id IN ({ids_str})"
  if min_impressions > 0:
    gaql += f" AND metrics.impressions >= {min_impressions}"

  gaql += f" ORDER BY metrics.impressions DESC LIMIT {limit}"

  response = execute_gaql(query=gaql, customer_id=customer_id, login_customer_id=login_customer_id)

  rows = []
  for row in response["data"]:
    cost_micros = row.get("metrics.cost_micros", 0) or 0
    avg_cpc_micros = row.get("metrics.average_cpc", 0) or 0
    rows.append({
        "search_term": row.get("search_term_view.search_term"),
        "status": row.get("search_term_view.status"),
        "campaign_id": row.get("campaign.id"),
        "campaign_name": row.get("campaign.name"),
        "ad_group_id": row.get("ad_group.id"),
        "ad_group_name": row.get("ad_group.name"),
        "impressions": row.get("metrics.impressions", 0),
        "clicks": row.get("metrics.clicks", 0),
        "cost": round(cost_micros / 1_000_000, 2),
        "conversions": round(row.get("metrics.conversions", 0.0) or 0.0, 2),
        "ctr": round(row.get("metrics.ctr", 0.0) or 0.0, 4),
        "average_cpc": round(avg_cpc_micros / 1_000_000, 2),
    })

  return {"search_terms": rows, "total": len(rows)}


@mcp.tool()
def get_keyword_performance(
    customer_id: str,
    date_range: DateRange,
    campaign_ids: list[str] | None = None,
    ad_group_ids: list[str] | None = None,
    include_paused: bool = True,
    limit: int = 500,
    login_customer_id: str | None = None,
) -> dict:
  """Returns keyword-level performance metrics including Quality Score.

  Returns criterion_id for each keyword — use those IDs directly with
  update_keyword_status or update_keyword_bid without a separate lookup.

  Use campaign_ids or ad_group_ids to scope the query and reduce response time.

  Args:
      customer_id: The ID of the customer account (digits only).
      date_range: Predefined date range.
      campaign_ids: Optional list of campaign IDs to filter.
      ad_group_ids: Optional list of ad group IDs to filter.
      include_paused: Include PAUSED keywords. Defaults to True.
      limit: Maximum number of rows to return. Defaults to 500.
      login_customer_id: Optional MCC account ID.

  Returns:
      List of keywords with criterion_id, text, match type, status, QS,
      current bid, impressions, clicks, cost, conversions, CTR, avg CPC,
      and impression share metrics.
  """
  gaql = f"""
    SELECT
      ad_group_criterion.criterion_id,
      ad_group_criterion.keyword.text,
      ad_group_criterion.keyword.match_type,
      ad_group_criterion.status,
      ad_group_criterion.quality_info.quality_score,
      ad_group_criterion.quality_info.search_predicted_ctr,
      ad_group_criterion.quality_info.ad_relevance,
      ad_group_criterion.quality_info.landing_page_experience,
      ad_group_criterion.effective_cpc_bid_micros,
      ad_group_criterion.cpc_bid_micros,
      campaign.id,
      campaign.name,
      ad_group.id,
      ad_group.name,
      metrics.impressions,
      metrics.clicks,
      metrics.cost_micros,
      metrics.conversions,
      metrics.ctr,
      metrics.average_cpc,
      metrics.search_impression_share,
      metrics.search_top_impression_share
    FROM keyword_view
    WHERE segments.date DURING {date_range}
      AND ad_group_criterion.negative = FALSE
      AND ad_group_criterion.status != 'REMOVED'
  """

  if not include_paused:
    gaql += " AND ad_group_criterion.status = 'ENABLED'"
  if campaign_ids:
    ids_str = ", ".join(f"'{cid}'" for cid in campaign_ids)
    gaql += f" AND campaign.id IN ({ids_str})"
  if ad_group_ids:
    ids_str = ", ".join(f"'{aid}'" for aid in ad_group_ids)
    gaql += f" AND ad_group.id IN ({ids_str})"

  gaql += f" ORDER BY metrics.impressions DESC LIMIT {limit}"

  response = execute_gaql(query=gaql, customer_id=customer_id, login_customer_id=login_customer_id)

  rows = []
  for row in response["data"]:
    cost_micros = row.get("metrics.cost_micros", 0) or 0
    avg_cpc_micros = row.get("metrics.average_cpc", 0) or 0
    cpc_bid = row.get("ad_group_criterion.cpc_bid_micros", 0) or 0
    eff_cpc = row.get("ad_group_criterion.effective_cpc_bid_micros", 0) or 0
    rows.append({
        "criterion_id": row.get("ad_group_criterion.criterion_id"),
        "keyword": row.get("ad_group_criterion.keyword.text"),
        "match_type": row.get("ad_group_criterion.keyword.match_type"),
        "status": row.get("ad_group_criterion.status"),
        "quality_score": row.get("ad_group_criterion.quality_info.quality_score"),
        "expected_ctr": row.get("ad_group_criterion.quality_info.search_predicted_ctr"),
        "ad_relevance": row.get("ad_group_criterion.quality_info.ad_relevance"),
        "landing_page_exp": row.get("ad_group_criterion.quality_info.landing_page_experience"),
        "cpc_bid": round(cpc_bid / 1_000_000, 2) if cpc_bid else None,
        "effective_cpc_bid": round(eff_cpc / 1_000_000, 2) if eff_cpc else None,
        "campaign_id": row.get("campaign.id"),
        "campaign_name": row.get("campaign.name"),
        "ad_group_id": row.get("ad_group.id"),
        "ad_group_name": row.get("ad_group.name"),
        "impressions": row.get("metrics.impressions", 0),
        "clicks": row.get("metrics.clicks", 0),
        "cost": round(cost_micros / 1_000_000, 2),
        "conversions": round(row.get("metrics.conversions", 0.0) or 0.0, 2),
        "ctr": round(row.get("metrics.ctr", 0.0) or 0.0, 4),
        "average_cpc": round(avg_cpc_micros / 1_000_000, 2),
        "search_impression_share": row.get("metrics.search_impression_share"),
        "search_top_impression_share": row.get("metrics.search_top_impression_share"),
    })

  return {"keywords": rows, "total": len(rows)}


@mcp.tool()
def get_ad_performance(
    customer_id: str,
    date_range: DateRange,
    campaign_ids: list[str] | None = None,
    ad_group_ids: list[str] | None = None,
    limit: int = 200,
    login_customer_id: str | None = None,
) -> dict:
  """Returns ad-level performance metrics including RSA asset strength.

  For RSAs, includes ad_strength (EXCELLENT, GOOD, POOR, etc.) to guide
  creative optimization decisions.

  Args:
      customer_id: The ID of the customer account (digits only).
      date_range: Predefined date range.
      campaign_ids: Optional list of campaign IDs to filter.
      ad_group_ids: Optional list of ad group IDs to filter.
      limit: Maximum number of rows to return. Defaults to 200.
      login_customer_id: Optional MCC account ID.

  Returns:
      List of ads with ad_id, type, status, ad_strength, approval status,
      impressions, clicks, cost, conversions, CTR, and avg CPC.
  """
  gaql = f"""
    SELECT
      ad_group_ad.ad.id,
      ad_group_ad.ad.name,
      ad_group_ad.ad.type_,
      ad_group_ad.status,
      ad_group_ad.ad_strength,
      ad_group_ad.policy_summary.approval_status,
      campaign.id,
      campaign.name,
      ad_group.id,
      ad_group.name,
      metrics.impressions,
      metrics.clicks,
      metrics.cost_micros,
      metrics.conversions,
      metrics.ctr,
      metrics.average_cpc
    FROM ad_group_ad
    WHERE segments.date DURING {date_range}
      AND ad_group_ad.status != 'REMOVED'
  """

  if campaign_ids:
    ids_str = ", ".join(f"'{cid}'" for cid in campaign_ids)
    gaql += f" AND campaign.id IN ({ids_str})"
  if ad_group_ids:
    ids_str = ", ".join(f"'{aid}'" for aid in ad_group_ids)
    gaql += f" AND ad_group.id IN ({ids_str})"

  gaql += f" ORDER BY metrics.impressions DESC LIMIT {limit}"

  response = execute_gaql(query=gaql, customer_id=customer_id, login_customer_id=login_customer_id)

  rows = []
  for row in response["data"]:
    cost_micros = row.get("metrics.cost_micros", 0) or 0
    avg_cpc_micros = row.get("metrics.average_cpc", 0) or 0
    rows.append({
        "ad_id": row.get("ad_group_ad.ad.id"),
        "ad_name": row.get("ad_group_ad.ad.name"),
        "ad_type": row.get("ad_group_ad.ad.type_"),
        "status": row.get("ad_group_ad.status"),
        "ad_strength": row.get("ad_group_ad.ad_strength"),
        "approval_status": row.get("ad_group_ad.policy_summary.approval_status"),
        "campaign_id": row.get("campaign.id"),
        "campaign_name": row.get("campaign.name"),
        "ad_group_id": row.get("ad_group.id"),
        "ad_group_name": row.get("ad_group.name"),
        "impressions": row.get("metrics.impressions", 0),
        "clicks": row.get("metrics.clicks", 0),
        "cost": round(cost_micros / 1_000_000, 2),
        "conversions": round(row.get("metrics.conversions", 0.0) or 0.0, 2),
        "ctr": round(row.get("metrics.ctr", 0.0) or 0.0, 4),
        "average_cpc": round(avg_cpc_micros / 1_000_000, 2),
    })

  return {"ads": rows, "total": len(rows)}


@mcp.tool()
def get_quality_score_report(
    customer_id: str,
    campaign_ids: list[str] | None = None,
    ad_group_ids: list[str] | None = None,
    min_quality_score: int | None = None,
    limit: int = 500,
    login_customer_id: str | None = None,
) -> dict:
  """Returns current Quality Score breakdown for all active keywords.

  Quality Score reflects the current value — it is not segmented by date.
  QS of 0 means Google has not yet assigned a score (insufficient data).

  Components returned:
  - quality_score: 1-10 (0 = not assigned)
  - expected_ctr: ABOVE_AVERAGE, AVERAGE, BELOW_AVERAGE
  - ad_relevance: ABOVE_AVERAGE, AVERAGE, BELOW_AVERAGE
  - landing_page_exp: ABOVE_AVERAGE, AVERAGE, BELOW_AVERAGE

  Args:
      customer_id: The ID of the customer account (digits only).
      campaign_ids: Optional list of campaign IDs to filter.
      ad_group_ids: Optional list of ad group IDs to filter.
      min_quality_score: Only return keywords with QS >= this value.
          Use to find low-QS keywords (e.g. min_quality_score=1, filter in code).
      limit: Maximum number of rows to return. Defaults to 500.
      login_customer_id: Optional MCC account ID.

  Returns:
      List of keywords with QS breakdown, sorted by quality_score ascending
      (worst first) to prioritize optimization.
  """
  gaql = """
    SELECT
      ad_group_criterion.criterion_id,
      ad_group_criterion.keyword.text,
      ad_group_criterion.keyword.match_type,
      ad_group_criterion.status,
      ad_group_criterion.quality_info.quality_score,
      ad_group_criterion.quality_info.search_predicted_ctr,
      ad_group_criterion.quality_info.ad_relevance,
      ad_group_criterion.quality_info.landing_page_experience,
      campaign.id,
      campaign.name,
      ad_group.id,
      ad_group.name
    FROM keyword_view
    WHERE ad_group_criterion.negative = FALSE
      AND ad_group_criterion.status != 'REMOVED'
      AND campaign.status != 'REMOVED'
  """

  if campaign_ids:
    ids_str = ", ".join(f"'{cid}'" for cid in campaign_ids)
    gaql += f" AND campaign.id IN ({ids_str})"
  if ad_group_ids:
    ids_str = ", ".join(f"'{aid}'" for aid in ad_group_ids)
    gaql += f" AND ad_group.id IN ({ids_str})"

  gaql += f" ORDER BY ad_group_criterion.quality_info.quality_score ASC LIMIT {limit}"

  response = execute_gaql(query=gaql, customer_id=customer_id, login_customer_id=login_customer_id)

  rows = []
  for row in response["data"]:
    qs = row.get("ad_group_criterion.quality_info.quality_score") or 0
    if min_quality_score is not None and qs < min_quality_score:
      continue
    rows.append({
        "criterion_id": row.get("ad_group_criterion.criterion_id"),
        "keyword": row.get("ad_group_criterion.keyword.text"),
        "match_type": row.get("ad_group_criterion.keyword.match_type"),
        "status": row.get("ad_group_criterion.status"),
        "quality_score": qs,
        "expected_ctr": row.get("ad_group_criterion.quality_info.search_predicted_ctr"),
        "ad_relevance": row.get("ad_group_criterion.quality_info.ad_relevance"),
        "landing_page_exp": row.get("ad_group_criterion.quality_info.landing_page_experience"),
        "campaign_id": row.get("campaign.id"),
        "campaign_name": row.get("campaign.name"),
        "ad_group_id": row.get("ad_group.id"),
        "ad_group_name": row.get("ad_group.name"),
    })

  return {"keywords": rows, "total": len(rows)}


@mcp.tool()
def list_conversion_actions(
    customer_id: str,
    include_removed: bool = False,
    login_customer_id: str | None = None,
) -> dict:
  """Lists all conversion actions configured in the account.

  Use this to audit tracking setup, get conversion IDs for reporting,
  or verify configuration before creating new conversion actions.

  Args:
      customer_id: The ID of the customer account (digits only).
      include_removed: Include removed/inactive conversion actions.
          Defaults to False.
      login_customer_id: Optional MCC account ID.

  Returns:
      List of conversion actions with id, name, status, type, category,
      counting type, default value, and lookback window configuration.
  """
  gaql = """
    SELECT
      conversion_action.id,
      conversion_action.name,
      conversion_action.status,
      conversion_action.type_,
      conversion_action.category,
      conversion_action.counting_type,
      conversion_action.value_settings.default_value,
      conversion_action.value_settings.default_currency_code,
      conversion_action.value_settings.always_use_default_value,
      conversion_action.click_through_lookback_window_days,
      conversion_action.view_through_lookback_window_days,
      conversion_action.include_in_conversions_metric
    FROM conversion_action
  """

  if not include_removed:
    gaql += " WHERE conversion_action.status != 'REMOVED'"

  gaql += " ORDER BY conversion_action.name ASC"

  response = execute_gaql(query=gaql, customer_id=customer_id, login_customer_id=login_customer_id)

  rows = []
  for row in response["data"]:
    default_value = row.get("conversion_action.value_settings.default_value", 0) or 0
    rows.append({
        "conversion_id": row.get("conversion_action.id"),
        "name": row.get("conversion_action.name"),
        "status": row.get("conversion_action.status"),
        "type": row.get("conversion_action.type_"),
        "category": row.get("conversion_action.category"),
        "counting_type": row.get("conversion_action.counting_type"),
        "default_value": default_value,
        "currency": row.get("conversion_action.value_settings.default_currency_code"),
        "always_use_default_value": row.get("conversion_action.value_settings.always_use_default_value"),
        "click_through_lookback_days": row.get("conversion_action.click_through_lookback_window_days"),
        "view_through_lookback_days": row.get("conversion_action.view_through_lookback_window_days"),
        "include_in_conversions_metric": row.get("conversion_action.include_in_conversions_metric"),
    })

  return {"conversion_actions": rows, "total": len(rows)}


@mcp.tool()
def get_auction_insights(
    customer_id: str,
    date_range: DateRange,
    campaign_ids: list[str] | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Returns Auction Insights report showing competitor overlap and positioning.

  Reveals which competitors are bidding on the same auctions and how your
  impression share, overlap rate, and position compare to theirs.

  Metrics returned:
  - search_impression_share: Your IS vs total eligible impressions.
  - overlap_rate: How often a competitor's ad appeared when yours did.
  - position_above_rate: How often competitor appeared above yours.
  - search_top_impression_share: Impressions at top of page / eligible.
  - search_abs_top_impression_share: Impressions in position 1 / eligible.
  - outranking_share: How often you ranked above competitor or they didn't show.

  Args:
      customer_id: The ID of the customer account (digits only).
      date_range: Predefined date range (minimum LAST_7_DAYS recommended).
      campaign_ids: Optional list of campaign IDs to filter.
      login_customer_id: Optional MCC account ID.

  Returns:
      List of competitor domains with auction insight metrics per campaign.
  """
  gaql = f"""
    SELECT
      campaign.id,
      campaign.name,
      segments.auction_insight.domain,
      metrics.search_impression_share,
      metrics.search_overlap_rate,
      metrics.search_position_above_rate,
      metrics.search_top_impression_share,
      metrics.search_absolute_top_impression_share,
      metrics.search_outranking_share
    FROM campaign
    WHERE segments.date DURING {date_range}
      AND campaign.status != 'REMOVED'
  """

  if campaign_ids:
    ids_str = ", ".join(f"'{cid}'" for cid in campaign_ids)
    gaql += f" AND campaign.id IN ({ids_str})"

  gaql += " ORDER BY metrics.search_impression_share DESC"

  response = execute_gaql(query=gaql, customer_id=customer_id, login_customer_id=login_customer_id)

  rows = []
  for row in response["data"]:
    rows.append({
        "campaign_id": row.get("campaign.id"),
        "campaign_name": row.get("campaign.name"),
        "competitor_domain": row.get("segments.auction_insight.domain"),
        "impression_share": row.get("metrics.search_impression_share"),
        "overlap_rate": row.get("metrics.search_overlap_rate"),
        "position_above_rate": row.get("metrics.search_position_above_rate"),
        "top_impression_share": row.get("metrics.search_top_impression_share"),
        "abs_top_impression_share": row.get("metrics.search_absolute_top_impression_share"),
        "outranking_share": row.get("metrics.search_outranking_share"),
    })

  return {"auction_insights": rows, "total": len(rows)}
