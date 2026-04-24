"""This module contains mutate tools for the Google Ads API."""

import json
from typing import Annotated, Literal

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException
from pydantic import BeforeValidator

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import get_ads_client


def _coerce_list(v):
  """Parses a JSON string into a list if needed (MCP serialization workaround)."""
  if isinstance(v, str):
    try:
      return json.loads(v)
    except json.JSONDecodeError:
      return [v]
  return v


StringList = Annotated[list[str], BeforeValidator(_coerce_list)]


def _query_rsa(ads_client, customer_id, ad_group_id, ad_id, login_customer_id):
  """Fetches current RSA content via GAQL. Returns a dict with all ad fields."""
  gaql = f"""
    SELECT
      ad_group_ad.ad.id,
      ad_group_ad.ad.final_urls,
      ad_group_ad.ad.responsive_search_ad.headlines,
      ad_group_ad.ad.responsive_search_ad.descriptions,
      ad_group_ad.ad.responsive_search_ad.path1,
      ad_group_ad.ad.responsive_search_ad.path2
    FROM ad_group_ad
    WHERE ad_group_ad.ad.id = {ad_id}
      AND ad_group.id = {ad_group_id}
    PARAMETERS omit_unselected_resource_names=true
  """
  service = ads_client.get_service("GoogleAdsService")
  response = service.search_stream(query=gaql, customer_id=customer_id)

  for batch in response:
    for row in batch.results:
      rsa = row.ad_group_ad.ad.responsive_search_ad
      headlines = [a.text for a in rsa.headlines]
      descriptions = [a.text for a in rsa.descriptions]
      final_urls = list(row.ad_group_ad.ad.final_urls)
      path1 = rsa.path1 or None
      path2 = rsa.path2 or None
      return {
          "headlines": headlines,
          "descriptions": descriptions,
          "final_url": final_urls[0] if final_urls else None,
          "path1": path1,
          "path2": path2,
      }

  raise ToolError(
      f"Ad {ad_id} not found in ad group {ad_group_id}. "
      "Verify the IDs with: SELECT ad_group_ad.ad.id FROM ad_group_ad"
  )


MatchType = Literal["EXACT", "PHRASE", "BROAD"]
AdGroupStatus = Literal["ENABLED", "PAUSED"]
AdStatus = Literal["ENABLED", "PAUSED", "REMOVED"]


def _build_keyword_operation(ads_client, customer_id, ad_group_id, keyword_text, match_type, negative):
  """Builds a CREATE AdGroupCriterionOperation for a keyword."""
  criterion = ads_client.get_type("AdGroupCriterion")
  criterion.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"
  criterion.status = ads_client.enums.AdGroupCriterionStatusEnum.ENABLED
  criterion.negative = negative
  criterion.keyword.text = keyword_text
  criterion.keyword.match_type = getattr(ads_client.enums.KeywordMatchTypeEnum, match_type)
  operation = ads_client.get_type("AdGroupCriterionOperation")
  operation.create = criterion
  return operation


@mcp.tool()
def add_keywords(
    customer_id: str,
    ad_group_id: str,
    keywords: StringList,
    match_type: MatchType = "PHRASE",
    login_customer_id: str | None = None,
) -> dict:
  """Adds positive keywords to an ad group.

  Args:
      customer_id: The ID of the customer account (digits only).
      ad_group_id: The ID of the ad group.
      keywords: List of keyword texts to add.
      match_type: EXACT, PHRASE, or BROAD. Defaults to PHRASE.
      login_customer_id: Optional MCC account ID.

  Returns:
      Number of keywords added and their resource names.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  criterion_service = ads_client.get_service("AdGroupCriterionService")
  operations = [
      _build_keyword_operation(ads_client, customer_id, ad_group_id, kw, match_type, negative=False)
      for kw in keywords
  ]

  try:
    response = criterion_service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=operations
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "added": len(response.results),
      "resource_names": [r.resource_name for r in response.results],
  }


@mcp.tool()
def add_negative_keywords(
    customer_id: str,
    ad_group_id: str,
    keywords: StringList,
    match_type: MatchType = "PHRASE",
    login_customer_id: str | None = None,
) -> dict:
  """Adds negative keywords to an ad group.

  Args:
      customer_id: The ID of the customer account (digits only).
      ad_group_id: The ID of the ad group.
      keywords: List of keyword texts to add as negatives.
      match_type: EXACT or PHRASE. Defaults to PHRASE.
      login_customer_id: Optional MCC account ID.

  Returns:
      Number of negative keywords added and their resource names.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  criterion_service = ads_client.get_service("AdGroupCriterionService")
  operations = [
      _build_keyword_operation(ads_client, customer_id, ad_group_id, kw, match_type, negative=True)
      for kw in keywords
  ]

  try:
    response = criterion_service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=operations
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "added": len(response.results),
      "resource_names": [r.resource_name for r in response.results],
  }


@mcp.tool()
def remove_ad_group_criteria(
    customer_id: str,
    ad_group_id: str,
    criterion_ids: list[str],
    login_customer_id: str | None = None,
) -> dict:
  """Removes keywords or criteria from an ad group by criterion ID.

  Use execute_gaql to find criterion IDs via ad_group_criterion.criterion_id.
  Useful for removing and recreating keywords with a different match type.

  Args:
      customer_id: The ID of the customer account (digits only).
      ad_group_id: The ID of the ad group.
      criterion_ids: List of criterion IDs to remove.
      login_customer_id: Optional MCC account ID.

  Returns:
      Number of criteria removed.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  criterion_service = ads_client.get_service("AdGroupCriterionService")
  operations = []
  for criterion_id in criterion_ids:
    operation = ads_client.get_type("AdGroupCriterionOperation")
    operation.remove = f"customers/{customer_id}/adGroups/{ad_group_id}/criteria/{criterion_id}"
    operations.append(operation)

  try:
    response = criterion_service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=operations
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {"removed": len(response.results)}


@mcp.tool()
def create_ad_group(
    customer_id: str,
    campaign_id: str,
    name: str,
    cpc_bid_micros: int,
    login_customer_id: str | None = None,
) -> dict:
  """Creates a new Search Standard ad group inside a campaign.

  Args:
      customer_id: The ID of the customer account (digits only).
      campaign_id: The ID of the campaign.
      name: Name for the new ad group.
      cpc_bid_micros: Max CPC bid in micros (e.g. 1000000 = $1.00 USD).
      login_customer_id: Optional MCC account ID.

  Returns:
      Resource name of the created ad group.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  ad_group_service = ads_client.get_service("AdGroupService")
  ad_group = ads_client.get_type("AdGroup")
  ad_group.name = name
  ad_group.status = ads_client.enums.AdGroupStatusEnum.ENABLED
  ad_group.type_ = ads_client.enums.AdGroupTypeEnum.SEARCH_STANDARD
  ad_group.cpc_bid_micros = cpc_bid_micros
  ad_group.campaign = f"customers/{customer_id}/campaigns/{campaign_id}"

  operation = ads_client.get_type("AdGroupOperation")
  operation.create = ad_group

  try:
    response = ad_group_service.mutate_ad_groups(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  resource_name = response.results[0].resource_name
  ad_group_id = resource_name.split("/")[-1]
  return {"resource_name": resource_name, "ad_group_id": ad_group_id}


@mcp.tool()
def create_responsive_search_ad(
    customer_id: str,
    ad_group_id: str,
    final_url: str,
    headlines: list[str],
    descriptions: list[str],
    path1: str | None = None,
    path2: str | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Creates a Responsive Search Ad (RSA) in an ad group.

  Requires at least 3 headlines and 2 descriptions.
  Google recommends 8-10 headlines and 3-4 descriptions for best performance.
  Maximum: 15 headlines and 4 descriptions.
  Each headline must be 30 characters or less.
  Each description must be 90 characters or less.
  path1 and path2 are optional display URL paths (e.g. path1="erp", path2="farmacias"
  results in uniflex.com.pe/erp/farmacias as display URL).

  Args:
      customer_id: The ID of the customer account (digits only).
      ad_group_id: The ID of the ad group.
      final_url: The landing page URL for the ad.
      headlines: List of headline texts (min 3, max 15, each ≤30 chars).
      descriptions: List of description texts (min 2, max 4, each ≤90 chars).
      path1: Optional first display URL path (≤15 chars).
      path2: Optional second display URL path (≤15 chars). Requires path1.
      login_customer_id: Optional MCC account ID.

  Returns:
      Resource name of the created ad.
  """
  if len(headlines) < 3:
    raise ToolError("At least 3 headlines are required for a Responsive Search Ad.")
  if len(descriptions) < 2:
    raise ToolError("At least 2 descriptions are required for a Responsive Search Ad.")
  if len(headlines) > 15:
    raise ToolError("Maximum 15 headlines allowed.")
  if len(descriptions) > 4:
    raise ToolError("Maximum 4 descriptions allowed.")
  if path2 and not path1:
    raise ToolError("path1 is required when path2 is provided.")

  headline_errors = [f'"{h}" ({len(h)} chars)' for h in headlines if len(h) > 30]
  if headline_errors:
    raise ToolError(f"Headlines exceed 30 characters: {', '.join(headline_errors)}")

  description_errors = [f'"{d}" ({len(d)} chars)' for d in descriptions if len(d) > 90]
  if description_errors:
    raise ToolError(f"Descriptions exceed 90 characters: {', '.join(description_errors)}")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  ad = ads_client.get_type("Ad")
  ad.final_urls.append(final_url)

  for text in headlines:
    asset = ads_client.get_type("AdTextAsset")
    asset.text = text
    ad.responsive_search_ad.headlines.append(asset)

  for text in descriptions:
    asset = ads_client.get_type("AdTextAsset")
    asset.text = text
    ad.responsive_search_ad.descriptions.append(asset)

  if path1:
    ad.responsive_search_ad.path1 = path1
  if path2:
    ad.responsive_search_ad.path2 = path2

  ad_group_ad = ads_client.get_type("AdGroupAd")
  ad_group_ad.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"
  ad_group_ad.status = ads_client.enums.AdGroupAdStatusEnum.ENABLED
  ad_group_ad.ad = ad

  operation = ads_client.get_type("AdGroupAdOperation")
  operation.create = ad_group_ad

  try:
    response = ads_client.get_service("AdGroupAdService").mutate_ad_group_ads(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {"resource_name": response.results[0].resource_name}


@mcp.tool()
def update_ad_group(
    customer_id: str,
    ad_group_id: str,
    status: AdGroupStatus | None = None,
    cpc_bid_micros: int | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Updates an ad group's status or CPC bid.

  Args:
      customer_id: The ID of the customer account (digits only).
      ad_group_id: The ID of the ad group to update.
      status: New status: ENABLED or PAUSED.
      cpc_bid_micros: New max CPC bid in micros (e.g. 1500000 = $1.50 USD).
      login_customer_id: Optional MCC account ID.

  Returns:
      Resource name of the updated ad group.
  """
  if status is None and cpc_bid_micros is None:
    raise ToolError("Provide at least one of: status or cpc_bid_micros.")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  ad_group_service = ads_client.get_service("AdGroupService")
  ad_group = ads_client.get_type("AdGroup")
  ad_group.resource_name = f"customers/{customer_id}/adGroups/{ad_group_id}"

  field_mask_paths = []
  if status is not None:
    ad_group.status = getattr(ads_client.enums.AdGroupStatusEnum, status)
    field_mask_paths.append("status")
  if cpc_bid_micros is not None:
    ad_group.cpc_bid_micros = cpc_bid_micros
    field_mask_paths.append("cpc_bid_micros")

  operation = ads_client.get_type("AdGroupOperation")
  operation.update = ad_group
  operation.update_mask.paths.extend(field_mask_paths)

  try:
    response = ad_group_service.mutate_ad_groups(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {"resource_name": response.results[0].resource_name}


@mcp.tool()
def replace_responsive_search_ad(
    customer_id: str,
    ad_group_id: str,
    ad_id: str,
    headlines: list[str] | None = None,
    descriptions: list[str] | None = None,
    final_url: str | None = None,
    path1: str | None = None,
    path2: str | None = None,
    pause_old_ad: bool = True,
    login_customer_id: str | None = None,
) -> dict:
  """Replaces a Responsive Search Ad by pausing the old one and creating a new one.

  The Google Ads API does not allow modifying the content (headlines,
  descriptions, final_url, paths) of an existing ad — Ad objects are shared
  and immutable after creation (CANNOT_MODIFY_AD policy).

  This tool reads the current ad content, applies your changes, pauses the
  old ad, and creates a new RSA with the merged result — which is the
  Google-recommended pattern for updating ad content.

  Only the fields you provide are changed; everything else is preserved from
  the original ad.

  Use execute_gaql to get ad_id:
    SELECT ad_group_ad.ad.id FROM ad_group_ad WHERE ad_group.id = <ad_group_id>

  Args:
      customer_id: The ID of the customer account (digits only).
      ad_group_id: The ID of the ad group containing the ad.
      ad_id: The ID of the ad to replace.
      headlines: New full list of headlines (min 3, max 15, each ≤30 chars).
          If omitted, the current headlines are preserved.
      descriptions: New full list of descriptions (min 2, max 4, each ≤90 chars).
          If omitted, the current descriptions are preserved.
      final_url: New landing page URL. If omitted, current URL is preserved.
      path1: New first display URL path (≤15 chars).
      path2: New second display URL path (≤15 chars).
      pause_old_ad: Whether to pause the original ad. Defaults to True.
      login_customer_id: Optional MCC account ID.

  Returns:
      new_resource_name, old_resource_name, and the final content applied.
  """
  if all(v is None for v in [headlines, descriptions, final_url, path1, path2]):
    raise ToolError("Provide at least one field to change.")

  if headlines is not None:
    if len(headlines) < 3:
      raise ToolError("At least 3 headlines are required.")
    if len(headlines) > 15:
      raise ToolError("Maximum 15 headlines allowed.")
    errors = [f'"{h}" ({len(h)} chars)' for h in headlines if len(h) > 30]
    if errors:
      raise ToolError(f"Headlines exceed 30 characters: {', '.join(errors)}")

  if descriptions is not None:
    if len(descriptions) < 2:
      raise ToolError("At least 2 descriptions are required.")
    if len(descriptions) > 4:
      raise ToolError("Maximum 4 descriptions allowed.")
    errors = [f'"{d}" ({len(d)} chars)' for d in descriptions if len(d) > 90]
    if errors:
      raise ToolError(f"Descriptions exceed 90 characters: {', '.join(errors)}")

  if path2 and not path1:
    raise ToolError("path1 is required when path2 is provided.")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  # Read current ad content
  try:
    current = _query_rsa(ads_client, customer_id, ad_group_id, ad_id, login_customer_id)
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  # Merge: use provided values or fall back to current
  final_headlines = headlines if headlines is not None else current["headlines"]
  final_descriptions = descriptions if descriptions is not None else current["descriptions"]
  final_final_url = final_url if final_url is not None else current["final_url"]
  final_path1 = path1 if path1 is not None else current["path1"]
  final_path2 = path2 if path2 is not None else current["path2"]

  if not final_final_url:
    raise ToolError("No final_url found on the current ad and none was provided.")

  # Pause old ad
  old_resource_name = (
      f"customers/{customer_id}/adGroupAds/{ad_group_id}~{ad_id}"
  )
  if pause_old_ad:
    ad_group_ad = ads_client.get_type("AdGroupAd")
    ad_group_ad.resource_name = old_resource_name
    ad_group_ad.status = ads_client.enums.AdGroupAdStatusEnum.PAUSED
    pause_op = ads_client.get_type("AdGroupAdOperation")
    pause_op.update = ad_group_ad
    pause_op.update_mask.paths.append("status")
    try:
      ads_client.get_service("AdGroupAdService").mutate_ad_group_ads(
          customer_id=customer_id, operations=[pause_op]
      )
    except GoogleAdsException as e:
      raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  # Create new RSA
  ad = ads_client.get_type("Ad")
  ad.final_urls.append(final_final_url)

  for text in final_headlines:
    asset = ads_client.get_type("AdTextAsset")
    asset.text = text
    ad.responsive_search_ad.headlines.append(asset)

  for text in final_descriptions:
    asset = ads_client.get_type("AdTextAsset")
    asset.text = text
    ad.responsive_search_ad.descriptions.append(asset)

  if final_path1:
    ad.responsive_search_ad.path1 = final_path1
  if final_path2:
    ad.responsive_search_ad.path2 = final_path2

  ad_group_ad_new = ads_client.get_type("AdGroupAd")
  ad_group_ad_new.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"
  ad_group_ad_new.status = ads_client.enums.AdGroupAdStatusEnum.ENABLED
  ad_group_ad_new.ad = ad

  create_op = ads_client.get_type("AdGroupAdOperation")
  create_op.create = ad_group_ad_new

  try:
    response = ads_client.get_service("AdGroupAdService").mutate_ad_group_ads(
        customer_id=customer_id, operations=[create_op]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  new_resource_name = response.results[0].resource_name

  return {
      "new_resource_name": new_resource_name,
      "old_resource_name": old_resource_name,
      "old_ad_paused": pause_old_ad,
      "applied": {
          "headlines": final_headlines,
          "descriptions": final_descriptions,
          "final_url": final_final_url,
          "path1": final_path1,
          "path2": final_path2,
      },
  }


@mcp.tool()
def update_ad_status(
    customer_id: str,
    ad_group_id: str,
    ad_id: str,
    status: AdStatus,
    login_customer_id: str | None = None,
) -> dict:
  """Updates the status of an ad (enable, pause, or remove).

  Use execute_gaql to get ad_id: SELECT ad_group_ad.ad.id FROM ad_group_ad.

  Args:
      customer_id: The ID of the customer account (digits only).
      ad_group_id: The ID of the ad group containing the ad.
      ad_id: The ID of the ad to update.
      status: New status: ENABLED, PAUSED, or REMOVED.
      login_customer_id: Optional MCC account ID.

  Returns:
      Resource name of the updated ad.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  ad_group_ad = ads_client.get_type("AdGroupAd")
  ad_group_ad.resource_name = (
      f"customers/{customer_id}/adGroupAds/{ad_group_id}~{ad_id}"
  )
  ad_group_ad.status = getattr(ads_client.enums.AdGroupAdStatusEnum, status)

  operation = ads_client.get_type("AdGroupAdOperation")
  operation.update = ad_group_ad
  operation.update_mask.paths.append("status")

  try:
    response = ads_client.get_service("AdGroupAdService").mutate_ad_group_ads(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {"resource_name": response.results[0].resource_name}


@mcp.tool()
def remove_ad_group(
    customer_id: str,
    ad_group_id: str,
    login_customer_id: str | None = None,
) -> dict:
  """Removes an ad group and all its ads and keywords.

  Args:
      customer_id: The ID of the customer account (digits only).
      ad_group_id: The ID of the ad group to remove.
      login_customer_id: Optional MCC account ID.

  Returns:
      Resource name of the removed ad group.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  operation = ads_client.get_type("AdGroupOperation")
  operation.remove = f"customers/{customer_id}/adGroups/{ad_group_id}"

  try:
    response = ads_client.get_service("AdGroupService").mutate_ad_groups(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {"resource_name": response.results[0].resource_name}


@mcp.tool()
def add_campaign_negative_keywords(
    customer_id: str,
    campaign_id: str,
    keywords: list[str],
    match_type: MatchType = "PHRASE",
    login_customer_id: str | None = None,
) -> dict:
  """Adds negative keywords at the campaign level.

  Campaign-level negatives block all ad groups within the campaign.

  Args:
      customer_id: The ID of the customer account (digits only).
      campaign_id: The ID of the campaign.
      keywords: List of keyword texts to add as negatives.
      match_type: EXACT, PHRASE, or BROAD. Defaults to PHRASE.
      login_customer_id: Optional MCC account ID.

  Returns:
      Number of negative keywords added and their resource names.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  service = ads_client.get_service("CampaignCriterionService")
  operations = []
  for kw_text in keywords:
    criterion = ads_client.get_type("CampaignCriterion")
    criterion.campaign = f"customers/{customer_id}/campaigns/{campaign_id}"
    criterion.negative = True
    criterion.keyword.text = kw_text
    criterion.keyword.match_type = getattr(
        ads_client.enums.KeywordMatchTypeEnum, match_type
    )
    operation = ads_client.get_type("CampaignCriterionOperation")
    operation.create = criterion
    operations.append(operation)

  try:
    response = service.mutate_campaign_criteria(
        customer_id=customer_id, operations=operations
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "added": len(response.results),
      "resource_names": [r.resource_name for r in response.results],
  }
