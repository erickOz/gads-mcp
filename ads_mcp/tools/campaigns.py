"""Campaign and shared set management tools for the Google Ads API."""

from typing import Literal

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import get_ads_client


CampaignStatus = Literal["ENABLED", "PAUSED"]
BiddingStrategy = Literal["MANUAL_CPC", "MAXIMIZE_CLICKS", "MAXIMIZE_CONVERSIONS", "TARGET_CPA", "TARGET_ROAS"]
MatchType = Literal["EXACT", "PHRASE", "BROAD"]


@mcp.tool()
def create_campaign(
    customer_id: str,
    name: str,
    daily_budget_micros: int,
    status: CampaignStatus = "PAUSED",
    bidding_strategy: BiddingStrategy = "MANUAL_CPC",
    target_cpa_micros: int | None = None,
    target_roas: float | None = None,
    enable_search_network: bool = True,
    enable_search_partners: bool = False,
    login_customer_id: str | None = None,
) -> dict:
  """Creates a Search campaign with a new dedicated budget.

  For TARGET_CPA, provide target_cpa_micros (e.g. 5000000 = $5.00 USD).
  For TARGET_ROAS, provide target_roas as a decimal (e.g. 3.5 = 350% ROAS).
  Campaigns are created as PAUSED by default for safety.

  Args:
      customer_id: The ID of the customer account (digits only).
      name: Name for the campaign.
      daily_budget_micros: Daily budget in micros (e.g. 10000000 = $10.00 USD).
      status: Initial status: ENABLED or PAUSED. Defaults to PAUSED.
      bidding_strategy: MANUAL_CPC, MAXIMIZE_CLICKS, MAXIMIZE_CONVERSIONS,
          TARGET_CPA, or TARGET_ROAS. Defaults to MANUAL_CPC.
      target_cpa_micros: Target CPA in micros. Required for TARGET_CPA.
      target_roas: Target ROAS as decimal. Required for TARGET_ROAS.
      enable_search_network: Target Google Search. Defaults to True.
      enable_search_partners: Target Search Partners. Defaults to False.
      login_customer_id: Optional MCC account ID.

  Returns:
      campaign_id, campaign resource_name, and budget resource_name.
  """
  if bidding_strategy == "TARGET_CPA" and target_cpa_micros is None:
    raise ToolError("target_cpa_micros is required for TARGET_CPA bidding strategy.")
  if bidding_strategy == "TARGET_ROAS" and target_roas is None:
    raise ToolError("target_roas is required for TARGET_ROAS bidding strategy.")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  # Step 1: create budget
  budget = ads_client.get_type("CampaignBudget")
  budget.name = f"{name} Budget"
  budget.amount_micros = daily_budget_micros
  budget.delivery_method = (
      ads_client.enums.BudgetDeliveryMethodEnum.STANDARD
  )
  budget.explicitly_shared = False

  budget_op = ads_client.get_type("CampaignBudgetOperation")
  budget_op.create = budget

  try:
    budget_response = ads_client.get_service(
        "CampaignBudgetService"
    ).mutate_campaign_budgets(customer_id=customer_id, operations=[budget_op])
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  budget_resource_name = budget_response.results[0].resource_name

  # Step 2: create campaign
  campaign = ads_client.get_type("Campaign")
  campaign.name = name
  campaign.status = getattr(ads_client.enums.CampaignStatusEnum, status)
  campaign.advertising_channel_type = (
      ads_client.enums.AdvertisingChannelTypeEnum.SEARCH
  )
  campaign.campaign_budget = budget_resource_name
  campaign.network_settings.target_google_search = enable_search_network
  campaign.network_settings.target_search_network = enable_search_partners

  if bidding_strategy == "MANUAL_CPC":
    campaign.manual_cpc.enhanced_cpc_enabled = False
  elif bidding_strategy == "MAXIMIZE_CLICKS":
    campaign.maximize_clicks.CopyFrom(ads_client.get_type("MaximizeClicks"))
  elif bidding_strategy == "MAXIMIZE_CONVERSIONS":
    campaign.maximize_conversions.CopyFrom(
        ads_client.get_type("MaximizeConversions")
    )
  elif bidding_strategy == "TARGET_CPA":
    campaign.target_cpa.target_cpa_micros = target_cpa_micros
  elif bidding_strategy == "TARGET_ROAS":
    campaign.target_roas.target_roas = target_roas

  from google.ads.googleads.v23.enums.types.eu_political_advertising_status import EuPoliticalAdvertisingStatusEnum
  campaign.contains_eu_political_advertising = (
      EuPoliticalAdvertisingStatusEnum.EuPoliticalAdvertisingStatus.DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING
  )

  campaign_op = ads_client.get_type("CampaignOperation")
  campaign_op.create = campaign

  try:
    campaign_response = ads_client.get_service(
        "CampaignService"
    ).mutate_campaigns(customer_id=customer_id, operations=[campaign_op])
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  resource_name = campaign_response.results[0].resource_name
  campaign_id = resource_name.split("/")[-1]

  return {
      "campaign_id": campaign_id,
      "resource_name": resource_name,
      "budget_resource_name": budget_resource_name,
  }


@mcp.tool()
def update_campaign_status(
    customer_id: str,
    campaign_id: str,
    status: CampaignStatus,
    login_customer_id: str | None = None,
) -> dict:
  """Enables or pauses a campaign.

  Args:
      customer_id: The ID of the customer account (digits only).
      campaign_id: The ID of the campaign to update.
      status: New status: ENABLED or PAUSED.
      login_customer_id: Optional MCC account ID.

  Returns:
      Resource name of the updated campaign.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  campaign = ads_client.get_type("Campaign")
  campaign.resource_name = f"customers/{customer_id}/campaigns/{campaign_id}"
  campaign.status = getattr(ads_client.enums.CampaignStatusEnum, status)

  operation = ads_client.get_type("CampaignOperation")
  operation.update = campaign
  operation.update_mask.paths.append("status")

  try:
    response = ads_client.get_service("CampaignService").mutate_campaigns(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {"resource_name": response.results[0].resource_name}


@mcp.tool()
def update_campaign_budget(
    customer_id: str,
    budget_id: str,
    daily_budget_micros: int,
    login_customer_id: str | None = None,
) -> dict:
  """Updates the daily budget amount of a campaign budget.

  Use execute_gaql to get budget_id:
  SELECT campaign_budget.id FROM campaign_budget WHERE campaign.id = X

  Args:
      customer_id: The ID of the customer account (digits only).
      budget_id: The ID of the campaign budget to update.
      daily_budget_micros: New daily budget in micros (e.g. 20000000 = $20.00 USD).
      login_customer_id: Optional MCC account ID.

  Returns:
      Resource name of the updated budget.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  budget = ads_client.get_type("CampaignBudget")
  budget.resource_name = (
      f"customers/{customer_id}/campaignBudgets/{budget_id}"
  )
  budget.amount_micros = daily_budget_micros

  operation = ads_client.get_type("CampaignBudgetOperation")
  operation.update = budget
  operation.update_mask.paths.append("amount_micros")

  try:
    response = ads_client.get_service(
        "CampaignBudgetService"
    ).mutate_campaign_budgets(customer_id=customer_id, operations=[operation])
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {"resource_name": response.results[0].resource_name}


@mcp.tool()
def create_shared_negative_list(
    customer_id: str,
    name: str,
    keywords: list[str],
    match_type: MatchType = "PHRASE",
    campaign_ids: list[str] | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Creates a shared negative keyword list and optionally links it to campaigns.

  A shared list lets you apply the same negative keywords across multiple
  campaigns at once. You can also link it later via the Google Ads UI.

  Args:
      customer_id: The ID of the customer account (digits only).
      name: Name for the shared negative keyword list.
      keywords: List of negative keyword texts to add to the list.
      match_type: EXACT, PHRASE, or BROAD. Defaults to PHRASE.
      campaign_ids: Optional list of campaign IDs to link the list to immediately.
      login_customer_id: Optional MCC account ID.

  Returns:
      shared_set_id, resource_name, keywords added, and campaigns linked.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  # Step 1: create the shared set
  shared_set = ads_client.get_type("SharedSet")
  shared_set.name = name
  shared_set.type_ = ads_client.enums.SharedSetTypeEnum.NEGATIVE_KEYWORDS

  shared_set_op = ads_client.get_type("SharedSetOperation")
  shared_set_op.create = shared_set

  try:
    ss_response = ads_client.get_service("SharedSetService").mutate_shared_sets(
        customer_id=customer_id, operations=[shared_set_op]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  shared_set_resource = ss_response.results[0].resource_name
  shared_set_id = shared_set_resource.split("/")[-1]

  # Step 2: add keywords to the shared set
  criterion_ops = []
  for kw_text in keywords:
    criterion = ads_client.get_type("SharedCriterion")
    criterion.shared_set = shared_set_resource
    criterion.keyword.text = kw_text
    criterion.keyword.match_type = getattr(
        ads_client.enums.KeywordMatchTypeEnum, match_type
    )
    op = ads_client.get_type("SharedCriterionOperation")
    op.create = criterion
    criterion_ops.append(op)

  try:
    ads_client.get_service("SharedCriterionService").mutate_shared_criteria(
        customer_id=customer_id, operations=criterion_ops
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  # Step 3: link to campaigns if provided
  linked_campaigns = []
  if campaign_ids:
    link_ops = []
    for campaign_id in campaign_ids:
      link = ads_client.get_type("CampaignSharedSet")
      link.campaign = f"customers/{customer_id}/campaigns/{campaign_id}"
      link.shared_set = shared_set_resource
      op = ads_client.get_type("CampaignSharedSetOperation")
      op.create = link
      link_ops.append(op)

    try:
      ads_client.get_service(
          "CampaignSharedSetService"
      ).mutate_campaign_shared_sets(
          customer_id=customer_id, operations=link_ops
      )
      linked_campaigns = campaign_ids
    except GoogleAdsException as e:
      raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "shared_set_id": shared_set_id,
      "resource_name": shared_set_resource,
      "keywords_added": len(keywords),
      "campaigns_linked": linked_campaigns,
  }
