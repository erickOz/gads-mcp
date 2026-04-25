"""Tools for managing Google Ads audiences (User Lists)."""

from typing import Any

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import get_ads_client, execute_gaql


@mcp.tool()
def list_audiences(
    customer_id: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Lists all user lists (audiences) in the account.

  Args:
      customer_id: The ID of the customer account (digits only).
      login_customer_id: Optional MCC account ID.

  Returns:
      A list of audiences with id, name, type, status, and search size.
  """
  gaql_query = """
    SELECT
      user_list.resource_name,
      user_list.id,
      user_list.name,
      user_list.type,
      user_list.membership_status,
      user_list.size_for_search
    FROM user_list
    ORDER BY user_list.name
  """

  response = execute_gaql(
      query=gaql_query,
      customer_id=customer_id,
      login_customer_id=login_customer_id,
  )

  # execute_gaql returns flat keys: "user_list.id", "user_list.name", etc.
  processed_data = []
  for row in response["data"]:
    processed_data.append({
        "resource_name": row.get("user_list.resource_name"),
        "id": row.get("user_list.id"),
        "name": row.get("user_list.name"),
        "type": row.get("user_list.type"),
        "membership_status": row.get("user_list.membership_status"),
        "size_for_search": row.get("user_list.size_for_search"),
    })

  return {"audiences": processed_data}


@mcp.tool()
def create_audience(
    customer_id: str,
    name: str,
    description: str,
    url_contains_values: list[str],
    membership_lifespan_days: int = 30,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Creates a rule-based website visitor audience (user list).

  Creates an audience that includes users who visited pages whose URL
  contains any of the specified strings. Uses OR logic between values.

  Example: url_contains_values=["/products", "/shop"] will add users
  who visited any page containing "/products" OR "/shop".

  Args:
      customer_id: The ID of the customer account (digits only).
      name: Name for the user list.
      description: Description for the user list.
      url_contains_values: List of URL substrings to match
          (e.g. ["/products", "/checkout"]).
      membership_lifespan_days: Days a user stays in the list (default 30,
          max 540).
      login_customer_id: Optional MCC account ID.

  Returns:
      resource_name and id of the created user list.
  """
  if not url_contains_values:
    raise ToolError("At least one url_contains_values entry is required.")
  if membership_lifespan_days < 1 or membership_lifespan_days > 540:
    raise ToolError("membership_lifespan_days must be between 1 and 540.")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  user_list = ads_client.get_type("UserList")
  user_list.name = name
  user_list.description = description
  user_list.membership_status = (
      ads_client.enums.UserListMembershipStatusEnum.OPEN
  )
  user_list.membership_lifespan_days = membership_lifespan_days
  user_list.rule_based_user_list.prepopulation_status = (
      ads_client.enums.UserListPrepopulationStatusEnum.REQUESTED
  )

  # Build one rule item group per URL value (OR logic between groups)
  for url_value in url_contains_values:
    rule_item = ads_client.get_type("UserListRuleItem")
    rule_item.name = f"url_contains_{url_value}"
    rule_item.string_rule_item.key = (
        ads_client.enums.UserListStringRuleItemKeyEnum.URL
    )
    rule_item.string_rule_item.op = (
        ads_client.enums.UserListStringRuleItemOperatorEnum.CONTAINS
    )
    rule_item.string_rule_item.value = url_value

    rule_item_group = ads_client.get_type("UserListRuleItemGroup")
    rule_item_group.rule_items.append(rule_item)
    user_list.rule_based_user_list.expression_rule.rule.rule_item_groups.append(
        rule_item_group
    )

  operation = ads_client.get_type("UserListOperation")
  operation.create = user_list

  try:
    response = ads_client.get_service("UserListService").mutate_user_lists(
        customer_id=customer_id, operations=[operation]
    )
    resource_name = response.results[0].resource_name
    user_list_id = resource_name.split("/")[-1]
    return {"resource_name": resource_name, "id": user_list_id}
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e


@mcp.tool()
def apply_audience_to_ad_group(
    customer_id: str,
    ad_group_id: str,
    user_list_resource_name: str,
    bid_modifier: float | None = None,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Applies an audience (user list) to an ad group as a targeting criterion.

  Use list_audiences to get the user_list_resource_name.
  The audience is added in OBSERVATION mode by default (shows ads to everyone
  but allows bid adjustments for the audience). Provide bid_modifier to
  adjust bids, e.g. 1.2 = +20%, 0.8 = -20%.

  Args:
      customer_id: The ID of the customer account (digits only).
      ad_group_id: The ID of the ad group to apply the audience to.
      user_list_resource_name: Resource name of the user list
          (e.g. customers/123/userLists/456).
      bid_modifier: Optional bid multiplier (e.g. 1.2 for +20%).
      login_customer_id: Optional MCC account ID.

  Returns:
      Resource name of the created ad group criterion.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  criterion = ads_client.get_type("AdGroupCriterion")
  criterion.ad_group = f"customers/{customer_id}/adGroups/{ad_group_id}"
  criterion.user_list.user_list = user_list_resource_name

  if bid_modifier is not None:
    criterion.bid_modifier = bid_modifier

  operation = ads_client.get_type("AdGroupCriterionOperation")
  operation.create = criterion

  try:
    response = ads_client.get_service(
        "AdGroupCriterionService"
    ).mutate_ad_group_criteria(
        customer_id=customer_id, operations=[operation]
    )
    return {"resource_name": response.results[0].resource_name}
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e
