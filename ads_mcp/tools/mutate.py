"""This module contains mutate tools for the Google Ads API."""

from typing import Literal

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import get_ads_client


MatchType = Literal["EXACT", "PHRASE", "BROAD"]
AdGroupStatus = Literal["ENABLED", "PAUSED"]


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
    keywords: list[str],
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
    keywords: list[str],
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
