"""Shared budget tools — portfolio budget management across campaigns."""

from typing import Any

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import execute_gaql, get_ads_client


@mcp.tool()
def create_shared_budget(
    customer_id: str,
    name: str,
    amount_micros: int,
    delivery_method: str = "STANDARD",
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Creates a shared (portfolio) campaign budget that multiple campaigns can use.

  A shared budget automatically redistributes spend across all campaigns
  assigned to it, maximizing overall performance within the total daily limit.
  Useful for managing budgets across related campaigns without manually
  adjusting each one.

  After creation, use assign_campaign_budget to attach campaigns to this budget.

  Args:
      customer_id: The ID of the customer account (digits only).
      name: Display name for the shared budget.
      amount_micros: Daily budget in micros (1 USD = 1,000,000 micros).
          E.g. 50_000_000 = $50/day.
      delivery_method: STANDARD (spread evenly) or ACCELERATED (spend as fast
          as possible). Defaults to STANDARD.
      login_customer_id: Optional MCC account ID.

  Returns:
      budget_id and resource_name of the created shared budget.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  budget = ads_client.get_type("CampaignBudget")
  budget.name = name
  budget.amount_micros = amount_micros
  budget.explicitly_shared = True
  budget.delivery_method = getattr(
      ads_client.enums.BudgetDeliveryMethodEnum, delivery_method
  )

  operation = ads_client.get_type("CampaignBudgetOperation")
  operation.create = budget

  try:
    response = ads_client.get_service("CampaignBudgetService").mutate_campaign_budgets(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  resource_name = response.results[0].resource_name
  return {
      "budget_id": resource_name.split("/")[-1],
      "resource_name": resource_name,
      "name": name,
      "amount_usd": amount_micros / 1_000_000,
  }


@mcp.tool()
def list_shared_budgets(
    customer_id: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Lists all shared (portfolio) budgets in the account with their assignments.

  Args:
      customer_id: The ID of the customer account (digits only).
      login_customer_id: Optional MCC account ID.

  Returns:
      List of shared budgets with id, name, daily amount, and assigned campaigns.
  """
  query = """
    SELECT
      campaign_budget.id,
      campaign_budget.name,
      campaign_budget.amount_micros,
      campaign_budget.explicitly_shared,
      campaign_budget.reference_count,
      campaign_budget.status,
      campaign_budget.delivery_method,
      campaign_budget.resource_name
    FROM campaign_budget
    WHERE campaign_budget.explicitly_shared = TRUE
      AND campaign_budget.status = ENABLED
    ORDER BY campaign_budget.name
  """
  result = execute_gaql(query=query, customer_id=customer_id,
                        login_customer_id=login_customer_id)

  budgets = [
      {
          "budget_id": row.get("campaign_budget.id"),
          "name": row.get("campaign_budget.name"),
          "amount_micros": row.get("campaign_budget.amount_micros"),
          "amount_usd": (row.get("campaign_budget.amount_micros") or 0) / 1_000_000,
          "campaigns_count": row.get("campaign_budget.reference_count"),
          "delivery_method": row.get("campaign_budget.delivery_method"),
          "status": row.get("campaign_budget.status"),
          "resource_name": row.get("campaign_budget.resource_name"),
      }
      for row in result["data"]
  ]

  return {"shared_budgets": budgets, "total": len(budgets)}


@mcp.tool()
def assign_campaign_budget(
    customer_id: str,
    campaign_id: str,
    budget_id: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Assigns a shared budget to a campaign, replacing its current budget.

  After assignment, the campaign draws from the shared budget pool rather
  than having an individual daily limit. Use list_shared_budgets to find
  available budget IDs.

  Args:
      customer_id: The ID of the customer account (digits only).
      campaign_id: The campaign to update.
      budget_id: ID of the shared budget (from create_shared_budget or
          list_shared_budgets).
      login_customer_id: Optional MCC account ID.

  Returns:
      campaign resource_name confirming the budget assignment.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  campaign = ads_client.get_type("Campaign")
  campaign.resource_name = f"customers/{customer_id}/campaigns/{campaign_id}"
  campaign.campaign_budget = (
      f"customers/{customer_id}/campaignBudgets/{budget_id}"
  )

  operation = ads_client.get_type("CampaignOperation")
  operation.update = campaign
  operation.update_mask.paths.append("campaign_budget")

  try:
    response = ads_client.get_service("CampaignService").mutate_campaigns(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "campaign_resource_name": response.results[0].resource_name,
      "campaign_id": campaign_id,
      "budget_id": budget_id,
  }
