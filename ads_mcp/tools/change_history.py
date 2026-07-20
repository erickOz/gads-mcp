"""Change history tools — audit trail for account changes."""

from datetime import date, datetime, timedelta
from typing import Any, Literal, get_args

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import execute_gaql
from ads_mcp.tools.validation import validate_date, validate_enum


ChangeResourceType = Literal[
    "AD",
    "AD_GROUP",
    "AD_GROUP_AD",
    "AD_GROUP_ASSET",
    "AD_GROUP_BID_MODIFIER",
    "AD_GROUP_CRITERION",
    "ASSET",
    "CAMPAIGN",
    "CAMPAIGN_ASSET",
    "CAMPAIGN_BUDGET",
    "CAMPAIGN_CRITERION",
    "AD_GROUP_FEED",
    "CAMPAIGN_FEED",
    "FEED",
    "FEED_ITEM",
]


@mcp.tool()
def get_change_history(
    customer_id: str,
    start_date: str,
    end_date: str | None = None,
    resource_type: ChangeResourceType | None = None,
    limit: int = 100,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Gets the account change history — who changed what and when.

  Returns a log of granular changes to campaigns, ad groups, ads, keywords,
  budgets, and more. Only covers the last 30 days. Use this to audit
  recent changes, verify automations, or investigate unexpected behavior.

  Args:
      customer_id: The ID of the customer account (digits only).
      start_date: Start date in "YYYY-MM-DD" format. Max 30 days back.
      end_date: Optional end date in "YYYY-MM-DD" format.
      resource_type: Optional filter. One of: AD, AD_GROUP, AD_GROUP_AD,
          CAMPAIGN, CAMPAIGN_BUDGET, CAMPAIGN_CRITERION, AD_GROUP_CRITERION,
          ASSET, etc. If omitted, returns all change types.
      limit: Max rows to return. Defaults to 100.
      login_customer_id: Optional MCC account ID.

  Returns:
      List of changes with timestamp, user_email, resource_type, operation,
      changed_fields, and old/new resource snapshots.
  """
  validate_date(start_date, "start_date")
  # The change_event resource only exposes the last 30 days; a start_date older
  # than that is rejected (START_DATE_TOO_OLD). Clamp it to the earliest date the
  # API will accept so a "last N days" call never errors on the boundary.
  earliest = date.today() - timedelta(days=29)
  if datetime.strptime(start_date, "%Y-%m-%d").date() < earliest:
    start_date = earliest.isoformat()
  # The change_event resource requires a BOUNDED date range; with only a lower
  # bound the API rejects the query (CHANGE_DATE_RANGE_INFINITE). Default the
  # upper bound to today so the common "since <date>" call works.
  if end_date is None:
    end_date = date.today().isoformat()
  validate_date(end_date, "end_date")
  query = f"""
    SELECT
      change_event.change_date_time,
      change_event.change_resource_type,
      change_event.change_resource_name,
      change_event.resource_change_operation,
      change_event.changed_fields,
      change_event.user_email,
      change_event.client_type
    FROM change_event
    WHERE change_event.change_date_time >= '{start_date} 00:00:00'
      AND change_event.change_date_time <= '{end_date} 23:59:59'
  """
  if resource_type:
    validate_enum(resource_type, get_args(ChangeResourceType), "resource_type")
    query += f"\n      AND change_event.change_resource_type = '{resource_type}'"
  query += f"""
    ORDER BY change_event.change_date_time DESC
    LIMIT {limit}
  """

  result = execute_gaql(
      query=query,
      customer_id=customer_id,
      login_customer_id=login_customer_id,
  )

  changes = [
      {
          "timestamp": row.get("change_event.change_date_time"),
          "resource_type": row.get("change_event.change_resource_type"),
          "resource_name": row.get("change_event.change_resource_name"),
          "operation": row.get("change_event.resource_change_operation"),
          "changed_fields": row.get("change_event.changed_fields"),
          "user_email": row.get("change_event.user_email"),
          "client_type": row.get("change_event.client_type"),
      }
      for row in result["data"]
  ]

  return {"changes": changes, "total": len(changes)}
