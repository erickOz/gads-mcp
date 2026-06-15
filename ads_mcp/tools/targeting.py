"""Geographic and demographic targeting tools for the Google Ads API."""

from typing import Any, Literal

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import execute_gaql, get_ads_client


AgeRange = Literal[
    "AGE_RANGE_18_24",
    "AGE_RANGE_25_34",
    "AGE_RANGE_35_44",
    "AGE_RANGE_45_54",
    "AGE_RANGE_55_64",
    "AGE_RANGE_65_UP",
    "AGE_RANGE_UNDETERMINED",
]

Gender = Literal["MALE", "FEMALE", "UNDETERMINED"]

Device = Literal["MOBILE", "TABLET", "DESKTOP", "CONNECTED_TV"]


# ── Geographic targeting ────────────────────────────────────────────────────


@mcp.tool()
def search_geo_targets(
    search_term: str,
    locale: str = "en",
    country_code: str | None = None,
) -> list[dict[str, Any]]:
  """Searches for geo target constants (countries, regions, cities, etc.).

  Use the returned geo_target_id with add_location_targets to apply
  locations to a campaign.

  Args:
      search_term: Location name to search for (e.g. "Lima", "Peru", "Mexico").
      locale: Language code for returned names (e.g. "en", "es"). Defaults to "en".
      country_code: Optional 2-letter ISO country code to narrow results
          (e.g. "PE", "MX", "US").

  Returns:
      List of matching locations with id, name, target_type, country_code,
      and canonical_name (full path, e.g. "Lima, Lima Region, Peru").
  """
  ads_client = get_ads_client()
  geo_service = ads_client.get_service("GeoTargetConstantService")

  request = ads_client.get_type("SuggestGeoTargetConstantsRequest")
  request.locale = locale
  if country_code:
    request.country_code = country_code
  request.location_names.names.append(search_term)

  try:
    response = geo_service.suggest_geo_target_constants(request=request)
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  results = []
  for suggestion in response.geo_target_constant_suggestions:
    gtc = suggestion.geo_target_constant
    results.append({
        "geo_target_id": str(gtc.id),
        "name": gtc.name,
        "target_type": gtc.target_type,
        "country_code": gtc.country_code,
        "canonical_name": gtc.canonical_name,
    })
  return results


@mcp.tool()
def add_location_targets(
    customer_id: str,
    campaign_id: str,
    geo_target_ids: list[str],
    negative: bool = False,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Adds geographic location targets (or exclusions) to a campaign.

  Use search_geo_targets first to find the geo_target_id for each location.

  Args:
      customer_id: The ID of the customer account (digits only).
      campaign_id: The campaign to add location targets to.
      geo_target_ids: List of geo target IDs from search_geo_targets.
          e.g. ["2604"] for Peru, ["1003840"] for Lima, Peru.
      negative: If True, adds as location exclusions instead of targets.
          Defaults to False (targeting, not exclusion).
      login_customer_id: Optional MCC account ID.

  Returns:
      List of resource_names for the created campaign criteria.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  service = ads_client.get_service("CampaignCriterionService")
  operations = []

  for geo_target_id in geo_target_ids:
    criterion = ads_client.get_type("CampaignCriterion")
    criterion.campaign = f"customers/{customer_id}/campaigns/{campaign_id}"
    criterion.negative = negative
    criterion.location.geo_target_constant = (
        f"geoTargetConstants/{geo_target_id}"
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
      "negative": negative,
      "resource_names": [r.resource_name for r in response.results],
  }


@mcp.tool()
def list_campaign_locations(
    customer_id: str,
    campaign_id: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Lists all geographic location targets and exclusions on a campaign.

  Args:
      customer_id: The ID of the customer account (digits only).
      campaign_id: The campaign to inspect.
      login_customer_id: Optional MCC account ID.

  Returns:
      List of locations with criterion_id, location name, country_code,
      target_type, and whether it is a negative (exclusion).
  """
  query = f"""
    SELECT
      campaign_criterion.criterion_id,
      campaign_criterion.negative,
      campaign_criterion.location.geo_target_constant,
      geo_target_constant.name,
      geo_target_constant.country_code,
      geo_target_constant.target_type,
      geo_target_constant.canonical_name
    FROM campaign_criterion
    WHERE campaign.id = {campaign_id}
      AND campaign_criterion.type = LOCATION
  """
  result = execute_gaql(
      query=query,
      customer_id=customer_id,
      login_customer_id=login_customer_id,
  )
  locations = []
  for row in result["data"]:
    rn = row.get("campaign_criterion.location.geo_target_constant", "")
    geo_target_id = rn.split("/")[-1] if rn else ""
    locations.append({
        "criterion_id": row.get("campaign_criterion.criterion_id"),
        "geo_target_id": geo_target_id,
        "name": row.get("geo_target_constant.name"),
        "canonical_name": row.get("geo_target_constant.canonical_name"),
        "country_code": row.get("geo_target_constant.country_code"),
        "target_type": row.get("geo_target_constant.target_type"),
        "negative": row.get("campaign_criterion.negative"),
    })
  return {"locations": locations, "count": len(locations)}


@mcp.tool()
def remove_campaign_criteria(
    customer_id: str,
    criterion_resource_names: list[str],
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Removes campaign-level criteria (location targets, device modifiers, etc.).

  Get criterion resource names from list_campaign_locations or execute_gaql.
  Format: customers/{customer_id}/campaignCriteria/{campaign_id}~{criterion_id}

  Args:
      customer_id: The ID of the customer account (digits only).
      criterion_resource_names: Resource names of the criteria to remove.
      login_customer_id: Optional MCC account ID.

  Returns:
      Count of removed criteria.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  service = ads_client.get_service("CampaignCriterionService")
  operations = []
  for resource_name in criterion_resource_names:
    operation = ads_client.get_type("CampaignCriterionOperation")
    operation.remove = resource_name
    operations.append(operation)

  try:
    service.mutate_campaign_criteria(
        customer_id=customer_id, operations=operations
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {"removed": len(criterion_resource_names)}


# ── Demographic targeting ───────────────────────────────────────────────────


@mcp.tool()
def set_age_range_bid_modifier(
    customer_id: str,
    ad_group_id: str,
    age_range: AgeRange,
    bid_modifier: float,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Sets a bid modifier for an age range on an ad group.

  A bid_modifier of 1.2 means +20%, 0.8 means -20%, 0.0 means exclude.
  Use list_ad_group_demographics to see current age range criteria.

  Args:
      customer_id: The ID of the customer account (digits only).
      ad_group_id: The ad group to target.
      age_range: One of AGE_RANGE_18_24, AGE_RANGE_25_34, AGE_RANGE_35_44,
          AGE_RANGE_45_54, AGE_RANGE_55_64, AGE_RANGE_65_UP,
          AGE_RANGE_UNDETERMINED.
      bid_modifier: Bid adjustment multiplier. 1.0 = no change, 1.5 = +50%,
          0.5 = -50%, 0.0 = exclude this age range.
      login_customer_id: Optional MCC account ID.

  Returns:
      resource_name of the created or updated criterion.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  service = ads_client.get_service("AdGroupCriterionService")

  # Check if criterion already exists to decide create vs update
  query = f"""
    SELECT
      ad_group_criterion.criterion_id,
      ad_group_criterion.age_range.type
    FROM ad_group_criterion
    WHERE ad_group.id = {ad_group_id}
      AND ad_group_criterion.type = AGE_RANGE
      AND ad_group_criterion.age_range.type = {age_range}
  """
  result = execute_gaql(query=query, customer_id=customer_id,
                        login_customer_id=login_customer_id)

  if result["data"]:
    # UPDATE existing criterion
    criterion_id = result["data"][0]["ad_group_criterion.criterion_id"]
    resource_name = (
        f"customers/{customer_id}/adGroupCriteria/{ad_group_id}~{criterion_id}"
    )
    criterion = ads_client.get_type("AdGroupCriterion")
    criterion.resource_name = resource_name
    criterion.bid_modifier = bid_modifier
    operation = ads_client.get_type("AdGroupCriterionOperation")
    operation.update = criterion
    operation.update_mask.paths.append("bid_modifier")
  else:
    # CREATE new criterion
    criterion = ads_client.get_type("AdGroupCriterion")
    criterion.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"
    criterion.status = ads_client.enums.AdGroupCriterionStatusEnum.ENABLED
    criterion.bid_modifier = bid_modifier
    criterion.age_range.type_ = getattr(
        ads_client.enums.AgeRangeTypeEnum, age_range
    )
    operation = ads_client.get_type("AdGroupCriterionOperation")
    operation.create = criterion

  try:
    response = service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "resource_name": response.results[0].resource_name,
      "age_range": age_range,
      "bid_modifier": bid_modifier,
  }


@mcp.tool()
def set_gender_bid_modifier(
    customer_id: str,
    ad_group_id: str,
    gender: Gender,
    bid_modifier: float,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Sets a bid modifier for a gender on an ad group.

  A bid_modifier of 1.2 means +20%, 0.8 means -20%, 0.0 means exclude.
  Use list_ad_group_demographics to see current gender criteria.

  Args:
      customer_id: The ID of the customer account (digits only).
      ad_group_id: The ad group to target.
      gender: MALE, FEMALE, or UNDETERMINED.
      bid_modifier: Bid adjustment multiplier (1.0 = no change, 0.0 = exclude).
      login_customer_id: Optional MCC account ID.

  Returns:
      resource_name of the created or updated criterion.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  service = ads_client.get_service("AdGroupCriterionService")

  query = f"""
    SELECT
      ad_group_criterion.criterion_id,
      ad_group_criterion.gender.type
    FROM ad_group_criterion
    WHERE ad_group.id = {ad_group_id}
      AND ad_group_criterion.type = GENDER
      AND ad_group_criterion.gender.type = {gender}
  """
  result = execute_gaql(query=query, customer_id=customer_id,
                        login_customer_id=login_customer_id)

  if result["data"]:
    criterion_id = result["data"][0]["ad_group_criterion.criterion_id"]
    resource_name = (
        f"customers/{customer_id}/adGroupCriteria/{ad_group_id}~{criterion_id}"
    )
    criterion = ads_client.get_type("AdGroupCriterion")
    criterion.resource_name = resource_name
    criterion.bid_modifier = bid_modifier
    operation = ads_client.get_type("AdGroupCriterionOperation")
    operation.update = criterion
    operation.update_mask.paths.append("bid_modifier")
  else:
    criterion = ads_client.get_type("AdGroupCriterion")
    criterion.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"
    criterion.status = ads_client.enums.AdGroupCriterionStatusEnum.ENABLED
    criterion.bid_modifier = bid_modifier
    criterion.gender.type_ = getattr(
        ads_client.enums.GenderTypeEnum, gender
    )
    operation = ads_client.get_type("AdGroupCriterionOperation")
    operation.create = criterion

  try:
    response = service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "resource_name": response.results[0].resource_name,
      "gender": gender,
      "bid_modifier": bid_modifier,
  }


@mcp.tool()
def set_device_bid_modifier(
    customer_id: str,
    campaign_id: str,
    device: Device,
    bid_modifier: float,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Sets a bid modifier for a device type at the campaign level.

  bid_modifier of 1.3 means +30% bids on that device; 0.5 means -50%.
  Set to 0.0 to effectively exclude TABLET or CONNECTED_TV (not allowed for MOBILE).

  Args:
      customer_id: The ID of the customer account (digits only).
      campaign_id: The campaign to modify.
      device: MOBILE, TABLET, DESKTOP, or CONNECTED_TV.
      bid_modifier: Multiplier (e.g. 1.2 = +20%, 0.5 = -50%).
          Cannot be 0.0 for MOBILE on Search campaigns.
      login_customer_id: Optional MCC account ID.

  Returns:
      resource_name of the created or updated criterion.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  service = ads_client.get_service("CampaignCriterionService")

  query = f"""
    SELECT
      campaign_criterion.criterion_id,
      campaign_criterion.device.type
    FROM campaign_criterion
    WHERE campaign.id = {campaign_id}
      AND campaign_criterion.type = DEVICE
      AND campaign_criterion.device.type = {device}
  """
  result = execute_gaql(query=query, customer_id=customer_id,
                        login_customer_id=login_customer_id)

  if result["data"]:
    criterion_id = result["data"][0]["campaign_criterion.criterion_id"]
    resource_name = (
        f"customers/{customer_id}/campaignCriteria/{campaign_id}~{criterion_id}"
    )
    criterion = ads_client.get_type("CampaignCriterion")
    criterion.resource_name = resource_name
    criterion.bid_modifier = bid_modifier
    operation = ads_client.get_type("CampaignCriterionOperation")
    operation.update = criterion
    operation.update_mask.paths.append("bid_modifier")
  else:
    criterion = ads_client.get_type("CampaignCriterion")
    criterion.campaign = f"customers/{customer_id}/campaigns/{campaign_id}"
    criterion.bid_modifier = bid_modifier
    criterion.device.type_ = getattr(ads_client.enums.DeviceEnum, device)
    operation = ads_client.get_type("CampaignCriterionOperation")
    operation.create = criterion

  try:
    response = service.mutate_campaign_criteria(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "resource_name": response.results[0].resource_name,
      "device": device,
      "bid_modifier": bid_modifier,
  }


@mcp.tool()
def list_ad_group_demographics(
    customer_id: str,
    campaign_id: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Lists current age range and gender targeting criteria on all ad groups in a campaign.

  Also returns device bid modifiers at the campaign level.

  Args:
      customer_id: The ID of the customer account (digits only).
      campaign_id: The campaign to inspect.
      login_customer_id: Optional MCC account ID.

  Returns:
      age_gender: per-ad-group age and gender criteria with bid modifiers.
      devices: campaign-level device bid modifiers.
  """
  age_gender_query = f"""
    SELECT
      ad_group.id,
      ad_group.name,
      ad_group_criterion.criterion_id,
      ad_group_criterion.type,
      ad_group_criterion.age_range.type,
      ad_group_criterion.gender.type,
      ad_group_criterion.bid_modifier,
      ad_group_criterion.negative,
      ad_group_criterion.status
    FROM ad_group_criterion
    WHERE ad_group.campaign.id = {campaign_id}
      AND ad_group_criterion.type IN (AGE_RANGE, GENDER)
  """
  device_query = f"""
    SELECT
      campaign_criterion.criterion_id,
      campaign_criterion.device.type,
      campaign_criterion.bid_modifier
    FROM campaign_criterion
    WHERE campaign.id = {campaign_id}
      AND campaign_criterion.type = DEVICE
  """
  ag_result = execute_gaql(query=age_gender_query, customer_id=customer_id,
                           login_customer_id=login_customer_id)
  dev_result = execute_gaql(query=device_query, customer_id=customer_id,
                            login_customer_id=login_customer_id)

  age_gender = [
      {
          "ad_group_id": row.get("ad_group.id"),
          "ad_group_name": row.get("ad_group.name"),
          "criterion_id": row.get("ad_group_criterion.criterion_id"),
          "type": row.get("ad_group_criterion.type"),
          "value": row.get("ad_group_criterion.age_range.type")
                   or row.get("ad_group_criterion.gender.type"),
          "bid_modifier": row.get("ad_group_criterion.bid_modifier"),
          "negative": row.get("ad_group_criterion.negative"),
          "status": row.get("ad_group_criterion.status"),
      }
      for row in ag_result["data"]
  ]

  devices = [
      {
          "criterion_id": row.get("campaign_criterion.criterion_id"),
          "device": row.get("campaign_criterion.device.type"),
          "bid_modifier": row.get("campaign_criterion.bid_modifier"),
      }
      for row in dev_result["data"]
  ]

  return {"age_gender": age_gender, "devices": devices}
