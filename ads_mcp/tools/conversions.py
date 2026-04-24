"""Conversion action management tools for the Google Ads API."""

from typing import Literal

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import get_ads_client


ConversionCategory = Literal[
    "PURCHASE",
    "LEAD",
    "SIGNUP",
    "PAGE_VIEW",
    "DOWNLOAD",
    "PHONE_CALL_LEAD",
    "IMPORTED_LEAD",
    "QUALIFIED_LEAD",
    "CONVERTED_LEAD",
    "OTHER",
]

CountingType = Literal["ONE_PER_CLICK", "MANY_PER_CLICK"]


@mcp.tool()
def create_conversion_action(
    customer_id: str,
    name: str,
    category: ConversionCategory = "LEAD",
    counting_type: CountingType = "ONE_PER_CLICK",
    default_value: float | None = None,
    value_currency_code: str = "USD",
    view_through_lookback_window_days: int = 1,
    click_through_lookback_window_days: int = 30,
    login_customer_id: str | None = None,
) -> dict:
  """Creates a website conversion action (tag-based).

  After creation, use the conversion_id to set up the Google Tag in the website.
  Retrieve the tag snippet via execute_gaql:
    SELECT conversion_action.tag_snippets FROM conversion_action
    WHERE conversion_action.id = <conversion_id>

  Common categories:
  - PURCHASE: e-commerce transactions
  - LEAD: form submissions, quote requests
  - SIGNUP: registrations, newsletter sign-ups
  - PAGE_VIEW: specific page visits
  - DOWNLOAD: file downloads

  Args:
      customer_id: The ID of the customer account (digits only).
      name: Name for the conversion action.
      category: Conversion category. Defaults to LEAD.
      counting_type: ONE_PER_CLICK counts one conversion per ad click.
          MANY_PER_CLICK counts all conversions per click. Defaults to ONE_PER_CLICK.
      default_value: Optional monetary value per conversion (e.g. 50.0 for $50).
      value_currency_code: Currency for default_value (e.g. "USD", "PEN", "MXN").
          Defaults to USD.
      view_through_lookback_window_days: Days to attribute view-through conversions.
          Defaults to 1.
      click_through_lookback_window_days: Days to attribute click-through conversions.
          Defaults to 30.
      login_customer_id: Optional MCC account ID.

  Returns:
      conversion_id and resource_name of the created conversion action.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  conversion_action = ads_client.get_type("ConversionAction")
  conversion_action.name = name
  conversion_action.status = ads_client.enums.ConversionActionStatusEnum.ENABLED
  conversion_action.type_ = (
      ads_client.enums.ConversionActionTypeEnum.WEBPAGE
  )
  conversion_action.category = getattr(
      ads_client.enums.ConversionActionCategoryEnum, category
  )
  conversion_action.counting_type = getattr(
      ads_client.enums.ConversionActionCountingTypeEnum, counting_type
  )
  conversion_action.view_through_lookback_window_days = (
      view_through_lookback_window_days
  )
  conversion_action.click_through_lookback_window_days = (
      click_through_lookback_window_days
  )

  if default_value is not None:
    conversion_action.value_settings.default_value = default_value
    conversion_action.value_settings.default_currency_code = value_currency_code
    conversion_action.value_settings.always_use_default_value = True

  operation = ads_client.get_type("ConversionActionOperation")
  operation.create = conversion_action

  try:
    response = ads_client.get_service(
        "ConversionActionService"
    ).mutate_conversion_actions(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  resource_name = response.results[0].resource_name
  conversion_id = resource_name.split("/")[-1]

  return {
      "conversion_id": conversion_id,
      "resource_name": resource_name,
      "name": name,
      "category": category,
  }
