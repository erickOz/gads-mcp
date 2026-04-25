"""Asset (ad extension) tools for the Google Ads API.

Covers Callout, Structured Snippet, and Sitelink assets
at account (customer), campaign, and ad group level.
"""

from typing import Literal

import httpx
from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import get_ads_client, execute_gaql


AssetLevel = Literal["ACCOUNT", "CAMPAIGN", "AD_GROUP"]

LeadFormCTA = Literal[
    "GET_QUOTE", "APPLY_NOW", "SIGN_UP", "CONTACT_US", "SUBSCRIBE",
    "DOWNLOAD", "BOOK_NOW", "GET_OFFER", "REGISTER", "GET_INFO",
    "REQUEST_DEMO", "JOIN_NOW", "GET_STARTED",
]

LeadFormFieldType = Literal[
    "FULL_NAME", "EMAIL", "PHONE_NUMBER", "POSTAL_CODE", "CITY",
    "REGION", "COUNTRY", "WORK_EMAIL", "COMPANY_NAME", "WORK_PHONE",
    "JOB_TITLE", "FIRST_NAME", "LAST_NAME",
]

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


@mcp.tool()
def list_assets(
    customer_id: str,
    level: AssetLevel = "ACCOUNT",
    campaign_id: str | None = None,
    ad_group_id: str | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Lists assets (ad extensions) linked to an account, campaign, or ad group.

  Returns link_resource_name (needed for remove_assets), field_type, asset
  details, and type-specific content (callout text, sitelink URL, etc.).

  For level=CAMPAIGN, provide campaign_id.
  For level=AD_GROUP, provide ad_group_id.

  Args:
      customer_id: The ID of the customer account (digits only).
      level: ACCOUNT, CAMPAIGN, or AD_GROUP. Defaults to ACCOUNT.
      campaign_id: Required when level=CAMPAIGN.
      ad_group_id: Required when level=AD_GROUP.
      login_customer_id: Optional MCC account ID.

  Returns:
      List of asset entries with link_resource_name, field_type, and content.
  """
  if level == "CAMPAIGN" and not campaign_id:
    raise ToolError("campaign_id is required when level=CAMPAIGN.")
  if level == "AD_GROUP" and not ad_group_id:
    raise ToolError("ad_group_id is required when level=AD_GROUP.")

  if level == "ACCOUNT":
    link_rn_key = "customer_asset.resource_name"
    field_type_key = "customer_asset.field_type"
    from_clause = "customer_asset"
    where_clause = ""
  elif level == "CAMPAIGN":
    link_rn_key = "campaign_asset.resource_name"
    field_type_key = "campaign_asset.field_type"
    from_clause = "campaign_asset"
    where_clause = f"WHERE campaign.id = {campaign_id}"
  else:
    link_rn_key = "ad_group_asset.resource_name"
    field_type_key = "ad_group_asset.field_type"
    from_clause = "ad_group_asset"
    where_clause = f"WHERE ad_group.id = {ad_group_id}"

  gaql_query = f"""
    SELECT
      {link_rn_key},
      {field_type_key},
      asset.id,
      asset.resource_name,
      asset.type,
      asset.callout_asset.callout_text,
      asset.sitelink_asset.link_text,
      asset.sitelink_asset.description1,
      asset.sitelink_asset.description2,
      asset.structured_snippet_asset.header,
      asset.structured_snippet_asset.values,
      asset.call_asset.phone_number,
      asset.call_asset.country_code,
      asset.lead_form_asset.headline,
      asset.lead_form_asset.description
    FROM {from_clause}
    {where_clause}
  """

  response = execute_gaql(
      query=gaql_query,
      customer_id=customer_id,
      login_customer_id=login_customer_id,
  )

  processed_data = []
  for row in response["data"]:
    entry = {
        "link_resource_name": row.get(link_rn_key),
        "field_type": row.get(field_type_key),
        "asset_id": row.get("asset.id"),
        "asset_resource_name": row.get("asset.resource_name"),
        "asset_type": row.get("asset.type"),
    }
    if row.get("asset.callout_asset.callout_text"):
      entry["callout_text"] = row["asset.callout_asset.callout_text"]
    if row.get("asset.sitelink_asset.link_text"):
      entry["link_text"] = row["asset.sitelink_asset.link_text"]
      entry["description1"] = row.get("asset.sitelink_asset.description1")
      entry["description2"] = row.get("asset.sitelink_asset.description2")
    if row.get("asset.structured_snippet_asset.header"):
      entry["header"] = row["asset.structured_snippet_asset.header"]
      entry["values"] = row.get("asset.structured_snippet_asset.values", [])
    if row.get("asset.call_asset.phone_number"):
      entry["phone_number"] = row["asset.call_asset.phone_number"]
      entry["country_code"] = row.get("asset.call_asset.country_code")
    if row.get("asset.lead_form_asset.headline"):
      entry["lead_form_headline"] = row["asset.lead_form_asset.headline"]
      entry["lead_form_description"] = row.get("asset.lead_form_asset.description")
    processed_data.append(entry)

  return {"assets": processed_data, "level": level, "count": len(processed_data)}


@mcp.tool()
def add_call_assets(
    customer_id: str,
    phone_number: str,
    country_code: str,
    level: AssetLevel = "ACCOUNT",
    campaign_id: str | None = None,
    ad_group_id: str | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Creates a Call asset (extensión de llamada) and links it to an account, campaign, or ad group.

  Displays a phone number below the ad, allowing users to call directly
  from the search results page.

  Args:
      customer_id: The ID of the customer account (digits only).
      phone_number: Phone number in local format (e.g. "01 234 5678").
      country_code: ISO 3166-1 alpha-2 country code (e.g. "PE", "US", "MX").
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

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  asset = ads_client.get_type("Asset")
  asset.call_asset.phone_number = phone_number
  asset.call_asset.country_code = country_code

  op = ads_client.get_type("AssetOperation")
  op.create = asset

  try:
    asset_response = ads_client.get_service("AssetService").mutate_assets(
        customer_id=customer_id, operations=[op]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  asset_resource_name = asset_response.results[0].resource_name

  field_type = ads_client.enums.AssetFieldTypeEnum.CALL
  entity_id = campaign_id if level == "CAMPAIGN" else ad_group_id

  try:
    link_resource_names = _link_assets(
        ads_client, customer_id, [asset_resource_name], field_type, level, entity_id
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "asset_resource_name": asset_resource_name,
      "link_resource_names": link_resource_names,
      "level": level,
      "phone_number": phone_number,
      "country_code": country_code,
  }


@mcp.tool()
def add_lead_form_asset(
    customer_id: str,
    headline: str,
    description: str,
    privacy_policy_url: str,
    call_to_action_type: LeadFormCTA = "CONTACT_US",
    fields: list[LeadFormFieldType] | None = None,
    post_submit_headline: str | None = None,
    post_submit_description: str | None = None,
    webhook_url: str | None = None,
    webhook_secret: str | None = None,
    level: Literal["ACCOUNT", "CAMPAIGN"] = "CAMPAIGN",
    campaign_id: str | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Creates a Lead Form asset (formulario de contacto) and links it to a campaign or account.

  Lead forms let users submit their contact info directly from the ad,
  without leaving Google Search. Leads are stored in Google Ads or sent
  to a webhook URL.

  Common fields: FULL_NAME, EMAIL, PHONE_NUMBER, COMPANY_NAME, JOB_TITLE,
  WORK_EMAIL, WORK_PHONE, CITY, REGION.

  Call to action options: GET_QUOTE, APPLY_NOW, SIGN_UP, CONTACT_US,
  SUBSCRIBE, DOWNLOAD, BOOK_NOW, GET_OFFER, REGISTER, GET_INFO,
  REQUEST_DEMO, JOIN_NOW, GET_STARTED.

  Args:
      customer_id: The ID of the customer account (digits only).
      headline: Form headline shown in the ad (max 30 chars).
      description: Form description (max 200 chars).
      privacy_policy_url: URL to the privacy policy page (required by Google).
      call_to_action_type: CTA button text shown on the ad. Defaults to CONTACT_US.
      fields: List of input fields to include. Defaults to
          [FULL_NAME, EMAIL, PHONE_NUMBER, COMPANY_NAME].
      post_submit_headline: Headline shown after form submission (max 30 chars).
      post_submit_description: Description shown after form submission (max 200 chars).
      webhook_url: Optional URL to receive lead data via POST webhook.
      webhook_secret: Required if webhook_url is provided. Secret key for
          verifying Google's webhook calls.
      level: ACCOUNT or CAMPAIGN. Defaults to CAMPAIGN.
      campaign_id: Required when level=CAMPAIGN.
      login_customer_id: Optional MCC account ID.

  Returns:
      Asset resource name and link resource name.
  """
  if level == "CAMPAIGN" and not campaign_id:
    raise ToolError("campaign_id is required when level=CAMPAIGN.")
  if webhook_url and not webhook_secret:
    raise ToolError("webhook_secret is required when webhook_url is provided.")
  if len(headline) > 30:
    raise ToolError(f"headline exceeds 30 characters ({len(headline)} chars).")
  if len(description) > 200:
    raise ToolError(f"description exceeds 200 characters ({len(description)} chars).")

  if fields is None:
    fields = ["FULL_NAME", "EMAIL", "PHONE_NUMBER", "COMPANY_NAME"]

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  asset = ads_client.get_type("Asset")
  lf = asset.lead_form_asset

  lf.headline = headline
  lf.description = description
  lf.privacy_policy_url = privacy_policy_url
  lf.call_to_action_type = (
      ads_client.enums.LeadFormCallToActionTypeEnum[call_to_action_type]
  )

  if post_submit_headline:
    lf.post_submit_headline = post_submit_headline
  if post_submit_description:
    lf.post_submit_description = post_submit_description

  for field_name in fields:
    lf_field = ads_client.get_type("LeadFormField")
    lf_field.input_type = (
        ads_client.enums.LeadFormFieldUserInputTypeEnum[field_name]
    )
    lf.fields.append(lf_field)

  if webhook_url:
    delivery = ads_client.get_type("LeadFormDeliveryMethod")
    delivery.webhook.advertiser_webhook_url = webhook_url
    delivery.webhook.google_secret = webhook_secret
    lf.delivery_methods.append(delivery)

  op = ads_client.get_type("AssetOperation")
  op.create = asset

  try:
    asset_response = ads_client.get_service("AssetService").mutate_assets(
        customer_id=customer_id, operations=[op]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  asset_resource_name = asset_response.results[0].resource_name

  field_type_enum = ads_client.enums.AssetFieldTypeEnum.LEAD_FORM
  entity_id = campaign_id if level == "CAMPAIGN" else None

  try:
    link_resource_names = _link_assets(
        ads_client, customer_id, [asset_resource_name],
        field_type_enum, level, entity_id,
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "asset_resource_name": asset_resource_name,
      "link_resource_names": link_resource_names,
      "level": level,
      "headline": headline,
      "call_to_action_type": call_to_action_type,
      "fields": fields,
  }


@mcp.tool()
def add_image_asset(
    customer_id: str,
    image_url: str,
    level: AssetLevel = "ACCOUNT",
    campaign_id: str | None = None,
    ad_group_id: str | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Creates an Image asset (extensión de imagen) and links it to an account, campaign, or ad group.

  Downloads the image from the given URL and uploads it to Google Ads.
  Image extensions show alongside Search ads, increasing visual presence.

  Google Ads requirements:
    - Landscape (1.91:1): minimum 600x314 px, recommended 1200x628 px.
    - Square (1:1): minimum 300x300 px, recommended 1200x1200 px.
    - Accepted formats: JPEG, PNG.
    - Max file size: 5 MB.

  For level=CAMPAIGN, provide campaign_id.
  For level=AD_GROUP, provide ad_group_id.

  Args:
      customer_id: The ID of the customer account (digits only).
      image_url: Public URL of the image to upload (JPEG or PNG).
      level: Where to attach: ACCOUNT, CAMPAIGN, or AD_GROUP. Defaults to ACCOUNT.
      campaign_id: Required when level=CAMPAIGN.
      ad_group_id: Required when level=AD_GROUP.
      login_customer_id: Optional MCC account ID.

  Returns:
      Asset resource name, link resource name, and detected MIME type.
  """
  if level == "CAMPAIGN" and not campaign_id:
    raise ToolError("campaign_id is required when level=CAMPAIGN.")
  if level == "AD_GROUP" and not ad_group_id:
    raise ToolError("ad_group_id is required when level=AD_GROUP.")

  try:
    response = httpx.get(image_url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    image_data = response.content
    content_type = response.headers.get("content-type", "").lower()
  except httpx.HTTPError as e:
    raise ToolError(f"Failed to download image from URL: {e}") from e

  if len(image_data) > 5 * 1024 * 1024:
    raise ToolError(
        f"Image file size ({len(image_data) // 1024} KB) exceeds the 5 MB limit."
    )

  url_lower = image_url.lower()
  if "png" in content_type or url_lower.endswith(".png"):
    mime_type_name = "IMAGE_PNG"
  else:
    mime_type_name = "IMAGE_JPEG"

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  asset = ads_client.get_type("Asset")
  asset.image_asset.data = image_data
  asset.image_asset.mime_type = ads_client.enums.MimeTypeEnum[mime_type_name]

  op = ads_client.get_type("AssetOperation")
  op.create = asset

  try:
    asset_response = ads_client.get_service("AssetService").mutate_assets(
        customer_id=customer_id, operations=[op]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  asset_resource_name = asset_response.results[0].resource_name

  field_type = ads_client.enums.AssetFieldTypeEnum.IMAGE
  entity_id = campaign_id if level == "CAMPAIGN" else ad_group_id

  try:
    link_resource_names = _link_assets(
        ads_client, customer_id, [asset_resource_name], field_type, level, entity_id
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "asset_resource_name": asset_resource_name,
      "link_resource_names": link_resource_names,
      "level": level,
      "mime_type": mime_type_name,
      "file_size_kb": round(len(image_data) / 1024, 1),
  }
