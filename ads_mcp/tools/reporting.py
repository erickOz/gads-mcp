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
