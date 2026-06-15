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


@mcp.tool()
def upload_click_conversions(
    customer_id: str,
    conversions: list[dict],
    partial_failure: bool = True,
    login_customer_id: str | None = None,
) -> dict:
  """Uploads click conversions from CRM/offline data to Google Ads.

  Use this to attribute offline sales back to ad clicks using the Google Click ID
  (gclid) recorded when the user clicked your ad. Ideal for businesses that close
  deals offline (calls, in-store, delayed checkout).

  Each conversion dict must contain:
    - gclid: Google Click ID recorded at click time
    - conversion_action_id: ID of the conversion action to credit
    - conversion_date_time: "yyyy-MM-dd HH:mm:ss+ZZ:ZZ" (e.g. "2024-01-15 14:30:00+00:00")
    - conversion_value: monetary value of the conversion (float)
    - currency_code: (optional) ISO 4217 code e.g. "USD". Defaults to account currency.

  Args:
      customer_id: The ID of the customer account (digits only).
      conversions: List of conversion dicts.
      partial_failure: If True, valid conversions upload even if some fail. Defaults to True.
      login_customer_id: Optional MCC account ID.

  Returns:
      successful_count, failed_count, and partial_failure_errors if any.
  """
  if not conversions:
    raise ToolError("conversions list cannot be empty.")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  service = ads_client.get_service("ConversionUploadService")
  operations = []
  for conv in conversions:
    click_conv = ads_client.get_type("ClickConversion")
    click_conv.gclid = conv["gclid"]
    click_conv.conversion_action = (
        f"customers/{customer_id}/conversionActions/{conv['conversion_action_id']}"
    )
    click_conv.conversion_date_time = conv["conversion_date_time"]
    click_conv.conversion_value = float(conv.get("conversion_value", 0))
    if "currency_code" in conv:
      click_conv.currency_code = conv["currency_code"]
    operations.append(click_conv)

  try:
    response = service.upload_click_conversions(
        customer_id=customer_id,
        conversions=operations,
        partial_failure=partial_failure,
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  errors = []
  if partial_failure and response.partial_failure_error.code != 0:
    from google.ads.googleads.errors import GoogleAdsFailure  # noqa: PLC0415
    failure = GoogleAdsFailure.deserialize(
        response.partial_failure_error.details[0].value
    )
    errors = [str(err) for err in failure.errors]

  successful = len([r for r in response.results if r.gclid])
  return {
      "successful_count": successful,
      "failed_count": len(operations) - successful,
      "partial_failure_errors": errors,
  }


@mcp.tool()
def upload_call_conversions(
    customer_id: str,
    conversions: list[dict],
    partial_failure: bool = True,
    login_customer_id: str | None = None,
) -> dict:
  """Uploads call conversions from CRM/offline data to Google Ads.

  Use this to attribute phone call outcomes (sales, appointments) to ad-driven calls.
  Requires call extension or call-only ads with call reporting enabled.

  Each conversion dict must contain:
    - caller_id: E.164 phone number of the caller (e.g. "+14155551234")
    - call_start_date_time: "yyyy-MM-dd HH:mm:ss+ZZ:ZZ"
    - conversion_action_id: ID of the conversion action to credit
    - conversion_date_time: "yyyy-MM-dd HH:mm:ss+ZZ:ZZ"
    - conversion_value: monetary value of the conversion (float)

  Args:
      customer_id: The ID of the customer account (digits only).
      conversions: List of conversion dicts.
      partial_failure: If True, valid conversions upload even if some fail. Defaults to True.
      login_customer_id: Optional MCC account ID.

  Returns:
      successful_count, failed_count, and partial_failure_errors if any.
  """
  if not conversions:
    raise ToolError("conversions list cannot be empty.")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  service = ads_client.get_service("ConversionUploadService")
  operations = []
  for conv in conversions:
    call_conv = ads_client.get_type("CallConversion")
    call_conv.caller_id = conv["caller_id"]
    call_conv.call_start_date_time = conv["call_start_date_time"]
    call_conv.conversion_action = (
        f"customers/{customer_id}/conversionActions/{conv['conversion_action_id']}"
    )
    call_conv.conversion_date_time = conv["conversion_date_time"]
    call_conv.conversion_value = float(conv.get("conversion_value", 0))
    operations.append(call_conv)

  try:
    response = service.upload_call_conversions(
        customer_id=customer_id,
        conversions=operations,
        partial_failure=partial_failure,
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  errors = []
  if partial_failure and response.partial_failure_error.code != 0:
    from google.ads.googleads.errors import GoogleAdsFailure  # noqa: PLC0415
    failure = GoogleAdsFailure.deserialize(
        response.partial_failure_error.details[0].value
    )
    errors = [str(err) for err in failure.errors]

  successful = len([r for r in response.results if r.caller_id])
  return {
      "successful_count": successful,
      "failed_count": len(operations) - successful,
      "partial_failure_errors": errors,
  }
