"""Performance Max campaign tools for the Google Ads API."""

from typing import Literal

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import get_ads_client


PMaxBiddingStrategy = Literal[
    "MAXIMIZE_CONVERSIONS",
    "MAXIMIZE_CONVERSION_VALUE",
]


@mcp.tool()
def create_performance_max_campaign(
    customer_id: str,
    name: str,
    daily_budget_micros: int,
    final_url: str,
    business_name: str,
    headlines: list[str],
    long_headlines: list[str],
    descriptions: list[str],
    bidding_strategy: PMaxBiddingStrategy = "MAXIMIZE_CONVERSIONS",
    target_cpa_micros: int | None = None,
    target_roas: float | None = None,
    asset_group_name: str | None = None,
    landscape_image_asset_resource_names: list[str] | None = None,
    square_image_asset_resource_names: list[str] | None = None,
    logo_asset_resource_names: list[str] | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Creates a Performance Max campaign with an asset group and text assets.

  Performance Max uses AI to serve across all Google channels (Search, Display,
  YouTube, Gmail, Discover, Maps). Recommended when you have conversion tracking
  set up and want Google to find customers across all surfaces.

  Text asset requirements:
  - headlines: 3–5 short headlines (max 30 chars each)
  - long_headlines: 1–5 long headlines (max 90 chars each)
  - descriptions: 2–5 descriptions (max 90 chars each)
  - business_name: 1 name (max 25 chars)

  Image assets are optional at creation time (campaign starts PAUSED).
  Upload images first via add_image_asset and pass their resource names here,
  or add them after creation. PMax requires images to serve at full capacity:
  - landscape_image_asset_resource_names: 1.91:1 ratio (min 600x314px)
  - square_image_asset_resource_names: 1:1 ratio (min 300x300px)
  - logo_asset_resource_names: 1:1 ratio (min 128x128px)

  Bidding:
  - MAXIMIZE_CONVERSIONS: maximize conversions within budget (optionally with target CPA).
  - MAXIMIZE_CONVERSION_VALUE: maximize revenue (optionally with target ROAS).

  Args:
      customer_id: The ID of the customer account (digits only).
      name: Campaign name.
      daily_budget_micros: Daily budget in micros (e.g. 30000000 = $30.00 USD).
      final_url: Main landing page URL for the asset group.
      business_name: Brand/business name shown in the ad (max 25 chars).
      headlines: List of 3–5 short headlines (each max 30 chars).
      long_headlines: List of 1–5 long headlines (each max 90 chars).
      descriptions: List of 2–5 descriptions (each max 90 chars).
      bidding_strategy: MAXIMIZE_CONVERSIONS or MAXIMIZE_CONVERSION_VALUE.
      target_cpa_micros: Optional target CPA for MAXIMIZE_CONVERSIONS.
      target_roas: Optional target ROAS (decimal) for MAXIMIZE_CONVERSION_VALUE.
      asset_group_name: Optional name for the asset group. Defaults to "{name} - Assets".
      landscape_image_asset_resource_names: Optional pre-uploaded image asset resource names.
      square_image_asset_resource_names: Optional pre-uploaded square image asset resource names.
      logo_asset_resource_names: Optional pre-uploaded logo asset resource names.
      login_customer_id: Optional MCC account ID.

  Returns:
      campaign_id, asset_group_id, and resource names for the created entities.
  """
  if len(business_name) > 25:
    raise ToolError(f"business_name '{business_name}' exceeds 25 characters.")
  if not (3 <= len(headlines) <= 5):
    raise ToolError("Provide between 3 and 5 headlines.")
  if not (1 <= len(long_headlines) <= 5):
    raise ToolError("Provide between 1 and 5 long headlines.")
  if not (2 <= len(descriptions) <= 5):
    raise ToolError("Provide between 2 and 5 descriptions.")

  headline_errors = [f'"{h}" ({len(h)} chars)' for h in headlines if len(h) > 30]
  if headline_errors:
    raise ToolError(f"Headlines exceed 30 characters: {', '.join(headline_errors)}")

  long_headline_errors = [f'"{h}" ({len(h)} chars)' for h in long_headlines if len(h) > 90]
  if long_headline_errors:
    raise ToolError(f"Long headlines exceed 90 characters: {', '.join(long_headline_errors)}")

  description_errors = [f'"{d}" ({len(d)} chars)' for d in descriptions if len(d) > 90]
  if description_errors:
    raise ToolError(f"Descriptions exceed 90 characters: {', '.join(description_errors)}")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  # Step 1: Create budget
  budget = ads_client.get_type("CampaignBudget")
  budget.name = f"{name} Budget"
  budget.amount_micros = daily_budget_micros
  budget.delivery_method = ads_client.enums.BudgetDeliveryMethodEnum.STANDARD
  budget.explicitly_shared = False

  budget_op = ads_client.get_type("CampaignBudgetOperation")
  budget_op.create = budget

  try:
    budget_response = ads_client.get_service("CampaignBudgetService").mutate_campaign_budgets(
        customer_id=customer_id, operations=[budget_op]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  budget_resource_name = budget_response.results[0].resource_name

  # Step 2: Create PMax campaign (always PAUSED for safety)
  campaign = ads_client.get_type("Campaign")
  campaign.name = name
  campaign.status = ads_client.enums.CampaignStatusEnum.PAUSED
  campaign.advertising_channel_type = (
      ads_client.enums.AdvertisingChannelTypeEnum.PERFORMANCE_MAX
  )
  campaign.campaign_budget = budget_resource_name

  if bidding_strategy == "MAXIMIZE_CONVERSIONS":
    campaign.maximize_conversions.CopyFrom(ads_client.get_type("MaximizeConversions"))
    if target_cpa_micros:
      campaign.maximize_conversions.target_cpa_micros = target_cpa_micros
  elif bidding_strategy == "MAXIMIZE_CONVERSION_VALUE":
    campaign.maximize_conversion_value.CopyFrom(
        ads_client.get_type("MaximizeConversionValue")
    )
    if target_roas:
      campaign.maximize_conversion_value.target_roas = target_roas

  campaign_op = ads_client.get_type("CampaignOperation")
  campaign_op.create = campaign

  try:
    campaign_response = ads_client.get_service("CampaignService").mutate_campaigns(
        customer_id=customer_id, operations=[campaign_op]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  campaign_resource_name = campaign_response.results[0].resource_name
  campaign_id = campaign_resource_name.split("/")[-1]

  # Step 3: Create asset group
  ag_name = asset_group_name or f"{name} - Assets"
  asset_group = ads_client.get_type("AssetGroup")
  asset_group.name = ag_name
  asset_group.campaign = campaign_resource_name
  asset_group.final_urls.append(final_url)
  asset_group.status = ads_client.enums.AssetGroupStatusEnum.PAUSED

  ag_op = ads_client.get_type("AssetGroupOperation")
  ag_op.create = asset_group

  try:
    ag_response = ads_client.get_service("AssetGroupService").mutate_asset_groups(
        customer_id=customer_id, operations=[ag_op]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  ag_resource_name = ag_response.results[0].resource_name
  asset_group_id = ag_resource_name.split("/")[-1]

  # Step 4: Create text assets and link to asset group
  AssetGroupAssetFieldType = ads_client.enums.AssetFieldTypeEnum

  text_asset_specs = []
  for text in headlines:
    text_asset_specs.append((text, AssetGroupAssetFieldType.HEADLINE))
  for text in long_headlines:
    text_asset_specs.append((text, AssetGroupAssetFieldType.LONG_HEADLINE))
  for text in descriptions:
    text_asset_specs.append((text, AssetGroupAssetFieldType.DESCRIPTION))
  text_asset_specs.append((business_name, AssetGroupAssetFieldType.BUSINESS_NAME))

  asset_ops = []
  for text, _ in text_asset_specs:
    asset = ads_client.get_type("Asset")
    asset.text_asset.text = text
    a_op = ads_client.get_type("AssetOperation")
    a_op.create = asset
    asset_ops.append(a_op)

  try:
    asset_response = ads_client.get_service("AssetService").mutate_assets(
        customer_id=customer_id, operations=asset_ops
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  created_asset_rns = [r.resource_name for r in asset_response.results]

  # Step 5: Link text assets to asset group
  aga_ops = []
  for asset_rn, (_, field_type) in zip(created_asset_rns, text_asset_specs):
    aga = ads_client.get_type("AssetGroupAsset")
    aga.asset_group = ag_resource_name
    aga.asset = asset_rn
    aga.field_type = field_type
    aga_op = ads_client.get_type("AssetGroupAssetOperation")
    aga_op.create = aga
    aga_ops.append(aga_op)

  # Step 6: Link any pre-uploaded image assets
  image_specs = []
  for rn in (landscape_image_asset_resource_names or []):
    image_specs.append((rn, AssetGroupAssetFieldType.MARKETING_IMAGE))
  for rn in (square_image_asset_resource_names or []):
    image_specs.append((rn, AssetGroupAssetFieldType.SQUARE_MARKETING_IMAGE))
  for rn in (logo_asset_resource_names or []):
    image_specs.append((rn, AssetGroupAssetFieldType.LOGO))

  for asset_rn, field_type in image_specs:
    aga = ads_client.get_type("AssetGroupAsset")
    aga.asset_group = ag_resource_name
    aga.asset = asset_rn
    aga.field_type = field_type
    aga_op = ads_client.get_type("AssetGroupAssetOperation")
    aga_op.create = aga
    aga_ops.append(aga_op)

  try:
    ads_client.get_service("AssetGroupAssetService").mutate_asset_group_assets(
        customer_id=customer_id, operations=aga_ops
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  result = {
      "campaign_id": campaign_id,
      "campaign_resource_name": campaign_resource_name,
      "asset_group_id": asset_group_id,
      "asset_group_resource_name": ag_resource_name,
      "budget_resource_name": budget_resource_name,
      "text_assets_created": len(created_asset_rns),
      "image_assets_linked": len(image_specs),
      "status": "PAUSED",
      "note": (
          "Campaign created in PAUSED state. Add image assets via add_image_asset "
          "and link them using the asset_group_resource_name, then enable when ready."
          if not image_specs else
          "Campaign created in PAUSED state. Enable when ready."
      ),
  }
  if target_cpa_micros:
    result["target_cpa"] = round(target_cpa_micros / 1_000_000, 2)
  if target_roas:
    result["target_roas"] = target_roas

  return result
