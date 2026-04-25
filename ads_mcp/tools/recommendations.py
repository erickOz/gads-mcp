"""Tools for fetching and applying Google Ads API recommendations."""

from typing import Any

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import get_ads_client, execute_gaql


@mcp.tool()
def list_recommendations(
    customer_id: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Lists active optimization recommendations for a customer account.

  Returns recommendation type, affected campaign/ad group, and estimated
  impact on impressions.

  Args:
      customer_id: The ID of the customer account (digits only).
      login_customer_id: Optional MCC account ID.

  Returns:
      A list of recommendations with type, resource_name, and impact.
  """
  gaql_query = """
    SELECT
      recommendation.resource_name,
      recommendation.type,
      recommendation.impact,
      recommendation.campaign,
      recommendation.ad_group
    FROM recommendation
  """

  response = execute_gaql(
      query=gaql_query,
      customer_id=customer_id,
      login_customer_id=login_customer_id,
  )

  # execute_gaql returns flat keys: "recommendation.type", etc.
  processed_data = []
  for row in response["data"]:
    impact = row.get("recommendation.impact") or {}
    base_metrics = impact.get("baseMetrics") or {}
    projected_metrics = impact.get("metrics") or {}
    processed_data.append({
        "resource_name": row.get("recommendation.resource_name"),
        "type": row.get("recommendation.type"),
        "campaign": row.get("recommendation.campaign"),
        "ad_group": row.get("recommendation.ad_group"),
        "base_impressions": base_metrics.get("impressions"),
        "projected_impressions": projected_metrics.get("impressions"),
    })

  return {"recommendations": processed_data}


@mcp.tool()
def apply_recommendation(
    customer_id: str,
    recommendation_resource_name: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Applies a specific optimization recommendation.

  Use list_recommendations to get the recommendation_resource_name first.

  Args:
      customer_id: The ID of the customer account (digits only).
      recommendation_resource_name: The resource name of the recommendation
          (e.g. customers/123/recommendations/456).
      login_customer_id: Optional MCC account ID.

  Returns:
      Resource name of the applied recommendation.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  recommendation_service = ads_client.get_service("RecommendationService")
  operation = ads_client.get_type("ApplyRecommendationOperation")
  operation.resource_name = recommendation_resource_name

  try:
    response = recommendation_service.apply_recommendation(
        customer_id=customer_id,
        operations=[operation],
    )
    return {"applied_resource_name": response.results[0].resource_name}
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e
