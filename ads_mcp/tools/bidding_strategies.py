"""Portfolio bidding strategy tools — shared automated bidding across campaigns."""

from typing import Any, Literal

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import execute_gaql, get_ads_client


BiddingStrategyType = Literal[
    "TARGET_CPA",
    "TARGET_ROAS",
    "MAXIMIZE_CONVERSIONS",
    "MAXIMIZE_CONVERSION_VALUE",
    "TARGET_IMPRESSION_SHARE",
    "TARGET_SPEND",
]


@mcp.tool()
def create_portfolio_bidding_strategy(
    customer_id: str,
    name: str,
    strategy_type: BiddingStrategyType,
    target_cpa_micros: int | None = None,
    target_roas: float | None = None,
    target_impression_share_micros: int | None = None,
    impression_share_location: str = "ANYWHERE_ON_PAGE",
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Creates a portfolio (shared) bidding strategy usable across multiple campaigns.

  Portfolio strategies let Google optimize bids across all assigned campaigns
  as a single pool, often outperforming per-campaign strategies when the
  individual campaigns have low conversion volume.

  Strategy types and required params:
    - TARGET_CPA: set target_cpa_micros (e.g. 5_000_000 = $5.00 per conversion)
    - TARGET_ROAS: set target_roas (e.g. 4.0 = 400% return on ad spend)
    - MAXIMIZE_CONVERSIONS: no extra params needed
    - MAXIMIZE_CONVERSION_VALUE: no extra params needed
    - TARGET_IMPRESSION_SHARE: set target_impression_share_micros (e.g.
        700_000 = 70%) and impression_share_location
    - TARGET_SPEND: no extra params needed (maximizes clicks within budget)

  After creation, use assign_portfolio_strategy to attach campaigns.

  Args:
      customer_id: The ID of the customer account (digits only).
      name: Display name for the strategy.
      strategy_type: One of TARGET_CPA, TARGET_ROAS, MAXIMIZE_CONVERSIONS,
          MAXIMIZE_CONVERSION_VALUE, TARGET_IMPRESSION_SHARE, TARGET_SPEND.
      target_cpa_micros: Target CPA in micros. Required for TARGET_CPA.
      target_roas: Target ROAS as a float (4.0 = 400%). Required for TARGET_ROAS.
      target_impression_share_micros: Target IS in micros (700000 = 70%).
          Required for TARGET_IMPRESSION_SHARE.
      impression_share_location: Where to target IS. ANYWHERE_ON_PAGE,
          TOP_OF_PAGE, or ABSOLUTE_TOP_OF_PAGE. Defaults to ANYWHERE_ON_PAGE.
      login_customer_id: Optional MCC account ID.

  Returns:
      strategy_id and resource_name of the created bidding strategy.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  strategy = ads_client.get_type("BiddingStrategy")
  strategy.name = name

  if strategy_type == "TARGET_CPA":
    if target_cpa_micros is None:
      raise ToolError("target_cpa_micros is required for TARGET_CPA.")
    strategy.target_cpa.target_cpa_micros = target_cpa_micros

  elif strategy_type == "TARGET_ROAS":
    if target_roas is None:
      raise ToolError("target_roas is required for TARGET_ROAS.")
    strategy.target_roas.target_roas = target_roas

  elif strategy_type == "MAXIMIZE_CONVERSIONS":
    strategy.maximize_conversions.target_cpa_micros = 0

  elif strategy_type == "MAXIMIZE_CONVERSION_VALUE":
    strategy.maximize_conversion_value.target_roas = 0

  elif strategy_type == "TARGET_IMPRESSION_SHARE":
    if target_impression_share_micros is None:
      raise ToolError(
          "target_impression_share_micros is required for TARGET_IMPRESSION_SHARE."
      )
    strategy.target_impression_share.location = getattr(
        ads_client.enums.TargetImpressionShareLocationEnum,
        impression_share_location,
    )
    strategy.target_impression_share.location_fraction_micros = (
        target_impression_share_micros
    )
    strategy.target_impression_share.cpc_bid_ceiling_micros = 0

  elif strategy_type == "TARGET_SPEND":
    strategy.target_spend.cpc_bid_ceiling_micros = 0

  operation = ads_client.get_type("BiddingStrategyOperation")
  operation.create = strategy

  try:
    response = ads_client.get_service(
        "BiddingStrategyService"
    ).mutate_bidding_strategies(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  resource_name = response.results[0].resource_name
  return {
      "strategy_id": resource_name.split("/")[-1],
      "resource_name": resource_name,
      "name": name,
      "strategy_type": strategy_type,
  }


@mcp.tool()
def list_portfolio_bidding_strategies(
    customer_id: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Lists all portfolio (shared) bidding strategies in the account.

  Args:
      customer_id: The ID of the customer account (digits only).
      login_customer_id: Optional MCC account ID.

  Returns:
      List of strategies with id, name, type, status, and campaign count.
  """
  query = """
    SELECT
      bidding_strategy.id,
      bidding_strategy.name,
      bidding_strategy.type,
      bidding_strategy.status,
      bidding_strategy.campaign_count,
      bidding_strategy.non_removed_campaign_count,
      bidding_strategy.resource_name
    FROM bidding_strategy
    ORDER BY bidding_strategy.name
  """
  result = execute_gaql(
      query=query,
      customer_id=customer_id,
      login_customer_id=login_customer_id,
  )

  strategies = [
      {
          "strategy_id": row.get("bidding_strategy.id"),
          "name": row.get("bidding_strategy.name"),
          "type": row.get("bidding_strategy.type"),
          "status": row.get("bidding_strategy.status"),
          "campaign_count": row.get("bidding_strategy.campaign_count"),
          "active_campaigns": row.get("bidding_strategy.non_removed_campaign_count"),
          "resource_name": row.get("bidding_strategy.resource_name"),
      }
      for row in result["data"]
  ]

  return {"strategies": strategies, "total": len(strategies)}


@mcp.tool()
def assign_portfolio_strategy(
    customer_id: str,
    campaign_id: str,
    strategy_id: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Assigns a portfolio bidding strategy to a campaign.

  Replaces the campaign's current bidding strategy with the shared portfolio
  strategy. Use list_portfolio_bidding_strategies to find strategy IDs.

  Args:
      customer_id: The ID of the customer account (digits only).
      campaign_id: The campaign to update.
      strategy_id: ID of the portfolio strategy (from create or list).
      login_customer_id: Optional MCC account ID.

  Returns:
      campaign resource_name confirming the strategy assignment.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  campaign = ads_client.get_type("Campaign")
  campaign.resource_name = f"customers/{customer_id}/campaigns/{campaign_id}"
  campaign.bidding_strategy = (
      f"customers/{customer_id}/biddingStrategies/{strategy_id}"
  )

  operation = ads_client.get_type("CampaignOperation")
  operation.update = campaign
  operation.update_mask.paths.append("bidding_strategy")

  try:
    response = ads_client.get_service("CampaignService").mutate_campaigns(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "campaign_resource_name": response.results[0].resource_name,
      "campaign_id": campaign_id,
      "strategy_id": strategy_id,
  }
