"""Asset (ad extension) tools for the Google Ads API.

Covers Callout, Structured Snippet, and Sitelink assets
at account (customer), campaign, and ad group level.
"""

from typing import Literal

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import get_ads_client


AssetLevel = Literal["ACCOUNT", "CAMPAIGN", "AD_GROUP"]

# Valid headers for Structured Snippet assets (Google-defined list)
STRUCTURED_SNIPPET_HEADERS = [
    "Amenities", "Brands", "Courses", "Degree programs", "Destinations",
    "Featured hotels", "Insurance coverage", "Items", "Models",
    "Neighborhoods", "Service catalog", "Shows", "Styles", "Types",
]


def _link_assets(
    ads_client,
    customer_id: str,
    asset_resource_names: list[str],
    field_type_enum,
    level: AssetLevel,
    entity_id: str | None,
) -> list[str]:
  """Links a list of assets to an account, campaign, or ad group."""
  link_resource_names = []

  if level == "ACCOUNT":
    service = ads_client.get_service("CustomerAssetService")
    ops = []
    for asset_rn in asset_resource_names:
      link = ads_client.get_type("CustomerAsset")
      link.asset = asset_rn
      link.field_type = field_type_enum
      op = ads_client.get_type("CustomerAssetOperation")
      op.create = link
      ops.append(op)
    response = service.mutate_customer_assets(
        customer_id=customer_id, operations=ops
    )
    link_resource_names = [r.resource_name for r in response.results]

  elif level == "CAMPAIGN":
    service = ads_client.get_service("CampaignAssetService")
    ops = []
    for asset_rn in asset_resource_names:
      link = ads_client.get_type("CampaignAsset")
      link.asset = asset_rn
      link.campaign = f"customers/{customer_id}/campaigns/{entity_id}"
      link.field_type = field_type_enum
      op = ads_client.get_type("CampaignAssetOperation")
      op.create = link
      ops.append(op)
    response = service.mutate_campaign_assets(
        customer_id=customer_id, operations=ops
    )
    link_resource_names = [r.resource_name for r in response.results]

  elif level == "AD_GROUP":
    service = ads_client.get_service("AdGroupAssetService")
    ops = []
    for asset_rn in asset_resource_names:
      link = ads_client.get_type("AdGroupAsset")
      link.asset = asset_rn
      link.ad_group = f"customers/{customer_id}/adGroups/{entity_id}"
      link.field_type = field_type_enum
      op = ads_client.get_type("AdGroupAssetOperation")
      op.create = link
      ops.append(op)
    response = service.mutate_ad_group_assets(
        customer_id=customer_id, operations=ops
    )
    link_resource_names = [r.resource_name for r in response.results]

  return link_resource_names


@mcp.tool()
def add_callout_assets(
    customer_id: str,
    callout_texts: list[str],
    level: AssetLevel = "ACCOUNT",
    campaign_id: str | None = None,
    ad_group_id: str | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Creates Callout assets (Texto Destacado) and links them to an account, campaign, or ad group.

  Callouts are short phrases shown below the ad (e.g. "Free shipping", "24/7 support").
  Each callout text must be 25 characters or less.

  For level=CAMPAIGN, provide campaign_id.
  For level=AD_GROUP, provide ad_group_id.
  For level=ACCOUNT, no extra ID is needed.

  Args:
      customer_id: The ID of the customer account (digits only).
      callout_texts: List of callout texts (each ≤25 chars).
      level: Where to attach: ACCOUNT, CAMPAIGN, or AD_GROUP. Defaults to ACCOUNT.
      campaign_id: Required when level=CAMPAIGN.
      ad_group_id: Required when level=AD_GROUP.
      login_customer_id: Optional MCC account ID.

  Returns:
      Asset resource names and link resource names.
  """
  if level == "CAMPAIGN" and not campaign_id:
    raise ToolError("campaign_id is required when level=CAMPAIGN.")
  if level == "AD_GROUP" and not ad_group_id:
    raise ToolError("ad_group_id is required when level=AD_GROUP.")

  errors = [f'"{t}" ({len(t)} chars)' for t in callout_texts if len(t) > 25]
  if errors:
    raise ToolError(f"Callout texts exceed 25 characters: {', '.join(errors)}")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  # Create assets
  asset_ops = []
  for text in callout_texts:
    asset = ads_client.get_type("Asset")
    asset.callout_asset.callout_text = text
    op = ads_client.get_type("AssetOperation")
    op.create = asset
    asset_ops.append(op)

  try:
    asset_response = ads_client.get_service("AssetService").mutate_assets(
        customer_id=customer_id, operations=asset_ops
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  asset_resource_names = [r.resource_name for r in asset_response.results]

  field_type = ads_client.enums.AssetFieldTypeEnum.CALLOUT
  entity_id = campaign_id if level == "CAMPAIGN" else ad_group_id

  try:
    link_resource_names = _link_assets(
        ads_client, customer_id, asset_resource_names, field_type, level, entity_id
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "assets_created": len(asset_resource_names),
      "asset_resource_names": asset_resource_names,
      "link_resource_names": link_resource_names,
      "level": level,
  }


@mcp.tool()
def add_structured_snippet_assets(
    customer_id: str,
    header: str,
    values: list[str],
    level: AssetLevel = "ACCOUNT",
    campaign_id: str | None = None,
    ad_group_id: str | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Creates a Structured Snippet asset (Fragmento Estructurado) and links it.

  Structured snippets display a header and a list of values below the ad.
  Example: header="Types", values=["ERP", "CRM", "WMS"]

  Valid headers: Amenities, Brands, Courses, Degree programs, Destinations,
  Featured hotels, Insurance coverage, Items, Models, Neighborhoods,
  Service catalog, Shows, Styles, Types.

  Each value must be 25 characters or less. Minimum 3 values required.

  For level=CAMPAIGN, provide campaign_id.
  For level=AD_GROUP, provide ad_group_id.

  Args:
      customer_id: The ID of the customer account (digits only).
      header: The snippet header (must be one of the valid Google headers).
      values: List of snippet values (min 3, each ≤25 chars).
      level: Where to attach: ACCOUNT, CAMPAIGN, or AD_GROUP. Defaults to ACCOUNT.
      campaign_id: Required when level=CAMPAIGN.
      ad_group_id: Required when level=AD_GROUP.
      login_customer_id: Optional MCC account ID.

  Returns:
      Asset resource name and link resource name.
  """
  if level == "CAMPAIGN" and not campaign_id:
    raise ToolError("campaign_id is required when level=CAMPAIGN.")
  if level == "AD_GROUP" and not ad_group_id:
    raise ToolError("ad_group_id is required when level=AD_GROUP.")
  if header not in STRUCTURED_SNIPPET_HEADERS:
    raise ToolError(
        f"Invalid header '{header}'. Must be one of: {', '.join(STRUCTURED_SNIPPET_HEADERS)}"
    )
  if len(values) < 3:
    raise ToolError("At least 3 values are required for a Structured Snippet.")

  errors = [f'"{v}" ({len(v)} chars)' for v in values if len(v) > 25]
  if errors:
    raise ToolError(f"Values exceed 25 characters: {', '.join(errors)}")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  asset = ads_client.get_type("Asset")
  asset.structured_snippet_asset.header = header
  asset.structured_snippet_asset.values.extend(values)

  op = ads_client.get_type("AssetOperation")
  op.create = asset

  try:
    asset_response = ads_client.get_service("AssetService").mutate_assets(
        customer_id=customer_id, operations=[op]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  asset_resource_name = asset_response.results[0].resource_name

  field_type = ads_client.enums.AssetFieldTypeEnum.STRUCTURED_SNIPPET
  entity_id = campaign_id if level == "CAMPAIGN" else ad_group_id

  try:
    link_resource_names = _link_assets(
        ads_client,
        customer_id,
        [asset_resource_name],
        field_type,
        level,
        entity_id,
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "asset_resource_name": asset_resource_name,
      "link_resource_names": link_resource_names,
      "level": level,
      "header": header,
      "values_count": len(values),
  }


@mcp.tool()
def add_sitelink_assets(
    customer_id: str,
    sitelinks: list[dict],
    level: AssetLevel = "ACCOUNT",
    campaign_id: str | None = None,
    ad_group_id: str | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Creates Sitelink assets (Vínculos a Sitios) and links them.

  Each sitelink requires link_text and final_url, and optionally
  description1 and description2 (each ≤35 chars).

  Example sitelinks list:
  [
    {"link_text": "Contacto", "final_url": "https://example.com/contact",
     "description1": "Escríbenos", "description2": "Respuesta en 24h"},
    {"link_text": "Precios", "final_url": "https://example.com/pricing"}
  ]

  link_text max 25 chars. description lines max 35 chars each.

  For level=CAMPAIGN, provide campaign_id.
  For level=AD_GROUP, provide ad_group_id.

  Args:
      customer_id: The ID of the customer account (digits only).
      sitelinks: List of dicts, each with link_text, final_url, and
          optionally description1, description2.
      level: Where to attach: ACCOUNT, CAMPAIGN, or AD_GROUP. Defaults to ACCOUNT.
      campaign_id: Required when level=CAMPAIGN.
      ad_group_id: Required when level=AD_GROUP.
      login_customer_id: Optional MCC account ID.

  Returns:
      Asset resource names and link resource names.
  """
  if level == "CAMPAIGN" and not campaign_id:
    raise ToolError("campaign_id is required when level=CAMPAIGN.")
  if level == "AD_GROUP" and not ad_group_id:
    raise ToolError("ad_group_id is required when level=AD_GROUP.")

  for i, sl in enumerate(sitelinks):
    if "link_text" not in sl or "final_url" not in sl:
      raise ToolError(f"Sitelink {i}: link_text and final_url are required.")
    if len(sl["link_text"]) > 25:
      raise ToolError(
          f"Sitelink {i} link_text '{sl['link_text']}' exceeds 25 characters."
      )
    for field in ("description1", "description2"):
      if field in sl and len(sl[field]) > 35:
        raise ToolError(
            f"Sitelink {i} {field} '{sl[field]}' exceeds 35 characters."
        )

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  asset_ops = []
  for sl in sitelinks:
    asset = ads_client.get_type("Asset")
    asset.sitelink_asset.link_text = sl["link_text"]
    asset.sitelink_asset.final_urls.append(sl["final_url"])
    if sl.get("description1"):
      asset.sitelink_asset.description1 = sl["description1"]
    if sl.get("description2"):
      asset.sitelink_asset.description2 = sl["description2"]
    op = ads_client.get_type("AssetOperation")
    op.create = asset
    asset_ops.append(op)

  try:
    asset_response = ads_client.get_service("AssetService").mutate_assets(
        customer_id=customer_id, operations=asset_ops
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  asset_resource_names = [r.resource_name for r in asset_response.results]

  field_type = ads_client.enums.AssetFieldTypeEnum.SITELINK
  entity_id = campaign_id if level == "CAMPAIGN" else ad_group_id

  try:
    link_resource_names = _link_assets(
        ads_client, customer_id, asset_resource_names, field_type, level, entity_id
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "assets_created": len(asset_resource_names),
      "asset_resource_names": asset_resource_names,
      "link_resource_names": link_resource_names,
      "level": level,
  }


@mcp.tool()
def remove_assets(
    customer_id: str,
    link_resource_names: list[str],
    level: AssetLevel,
    login_customer_id: str | None = None,
) -> dict:
  """Removes asset links from an account, campaign, or ad group.

  Use execute_gaql to find link resource names:
  - Account level: SELECT customer_asset.resource_name FROM customer_asset
  - Campaign level: SELECT campaign_asset.resource_name FROM campaign_asset
  - Ad group level: SELECT ad_group_asset.resource_name FROM ad_group_asset

  Removing the link detaches the asset; the asset itself is not deleted.

  Args:
      customer_id: The ID of the customer account (digits only).
      link_resource_names: List of asset link resource names to remove.
      level: ACCOUNT, CAMPAIGN, or AD_GROUP — must match the resource names.
      login_customer_id: Optional MCC account ID.

  Returns:
      Number of asset links removed.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  try:
    if level == "ACCOUNT":
      service = ads_client.get_service("CustomerAssetService")
      ops = []
      for rn in link_resource_names:
        op = ads_client.get_type("CustomerAssetOperation")
        op.remove = rn
        ops.append(op)
      response = service.mutate_customer_assets(
          customer_id=customer_id, operations=ops
      )
    elif level == "CAMPAIGN":
      service = ads_client.get_service("CampaignAssetService")
      ops = []
      for rn in link_resource_names:
        op = ads_client.get_type("CampaignAssetOperation")
        op.remove = rn
        ops.append(op)
      response = service.mutate_campaign_assets(
          customer_id=customer_id, operations=ops
      )
    elif level == "AD_GROUP":
      service = ads_client.get_service("AdGroupAssetService")
      ops = []
      for rn in link_resource_names:
        op = ads_client.get_type("AdGroupAssetOperation")
        op.remove = rn
        ops.append(op)
      response = service.mutate_ad_group_assets(
          customer_id=customer_id, operations=ops
      )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {"removed": len(response.results), "level": level}
