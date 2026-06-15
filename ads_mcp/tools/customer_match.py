"""Customer Match tools — upload hashed CRM data as Google Ads audiences."""

import hashlib
from typing import Any

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import execute_gaql, get_ads_client


def _sha256(value: str) -> str:
  return hashlib.sha256(value.encode("utf-8")).hexdigest()


@mcp.tool()
def create_customer_match_list(
    customer_id: str,
    name: str,
    description: str = "",
    membership_lifespan_days: int = 30,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Creates an empty Customer Match user list for CRM-based audience targeting.

  After creation, call upload_customer_match_members with the returned
  user_list_id to populate it with hashed emails, phones, or addresses.
  The list becomes available for targeting once it has at least 1,000 members.

  Args:
      customer_id: The ID of the customer account (digits only).
      name: Display name for the audience list.
      description: Optional description.
      membership_lifespan_days: Days a member stays in the list (1–540,
          or 10000 for no expiry). Defaults to 30.
      login_customer_id: Optional MCC account ID.

  Returns:
      user_list_id and resource_name of the created list.
  """
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
  user_list.crm_based_user_list.upload_key_type = (
      ads_client.enums.CustomerMatchUploadKeyTypeEnum.CONTACT_INFO
  )

  operation = ads_client.get_type("UserListOperation")
  operation.create = user_list

  try:
    response = ads_client.get_service("UserListService").mutate_user_lists(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  resource_name = response.results[0].resource_name
  return {
      "user_list_id": resource_name.split("/")[-1],
      "resource_name": resource_name,
      "name": name,
  }


@mcp.tool()
def upload_customer_match_members(
    customer_id: str,
    user_list_id: str,
    members: list[dict[str, str]],
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Uploads hashed contact data to a Customer Match audience list.

  Each member dict can contain any combination of:
    - email: raw email (normalized + SHA-256 hashed automatically)
    - phone: E.164 format e.g. "+14155551234" (SHA-256 hashed automatically)
    - first_name, last_name, zip, country: all four required together for
      address matching (lowercased + hashed automatically)

  The upload job runs asynchronously. Use get_customer_match_job_status
  with the returned job_resource_name to track completion.
  Lists need ~1,000 members before they're usable for targeting.

  Args:
      customer_id: The ID of the customer account (digits only).
      user_list_id: ID from create_customer_match_list.
      members: List of member dicts with raw (unhashed) contact data.
      login_customer_id: Optional MCC account ID.

  Returns:
      job_resource_name to poll, and count of members queued.
  """
  if not members:
    raise ToolError("members list cannot be empty.")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  offline_service = ads_client.get_service("OfflineUserDataJobService")
  user_list_resource = f"customers/{customer_id}/userLists/{user_list_id}"

  job = ads_client.get_type("OfflineUserDataJob")
  job.type_ = (
      ads_client.enums.OfflineUserDataJobTypeEnum.CUSTOMER_MATCH_USER_LIST
  )
  job.customer_match_user_list_metadata.user_list = user_list_resource

  job_response = offline_service.create_offline_user_data_job(
      customer_id=customer_id, job=job
  )
  job_resource_name = job_response.resource_name

  operations = []
  for member in members:
    user_data = ads_client.get_type("UserData")

    if "email" in member:
      uid = ads_client.get_type("UserIdentifier")
      uid.hashed_email = _sha256(member["email"].strip().lower())
      user_data.user_identifiers.append(uid)

    if "phone" in member:
      uid = ads_client.get_type("UserIdentifier")
      uid.hashed_phone_number = _sha256(
          member["phone"].strip().replace(" ", "")
      )
      user_data.user_identifiers.append(uid)

    if all(k in member for k in ("first_name", "last_name", "zip", "country")):
      uid = ads_client.get_type("UserIdentifier")
      uid.address_info.hashed_first_name = _sha256(
          member["first_name"].strip().lower()
      )
      uid.address_info.hashed_last_name = _sha256(
          member["last_name"].strip().lower()
      )
      uid.address_info.zip_code = member["zip"].strip()
      uid.address_info.country_code = member["country"].strip().upper()
      user_data.user_identifiers.append(uid)

    if not user_data.user_identifiers:
      continue

    op = ads_client.get_type("OfflineUserDataJobOperation")
    op.create = user_data
    operations.append(op)

  if not operations:
    raise ToolError(
        "No members had usable fields (email, phone, or full address)."
    )

  batch_size = 10_000
  try:
    for i in range(0, len(operations), batch_size):
      offline_service.add_offline_user_data_job_operations(
          resource_name=job_resource_name,
          operations=operations[i : i + batch_size],
      )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  try:
    offline_service.run_offline_user_data_job(
        resource_name=job_resource_name
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "job_resource_name": job_resource_name,
      "members_queued": len(operations),
      "status": "RUNNING",
  }


@mcp.tool()
def get_customer_match_job_status(
    customer_id: str,
    job_resource_name: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Checks the status of a Customer Match upload job.

  Args:
      customer_id: The ID of the customer account (digits only).
      job_resource_name: Value returned by upload_customer_match_members.
      login_customer_id: Optional MCC account ID.

  Returns:
      status (PENDING, RUNNING, SUCCESS, FAILED), and failure_reason if any.
  """
  query = f"""
    SELECT
      offline_user_data_job.resource_name,
      offline_user_data_job.id,
      offline_user_data_job.status,
      offline_user_data_job.type,
      offline_user_data_job.failure_reason
    FROM offline_user_data_job
    WHERE offline_user_data_job.resource_name = '{job_resource_name}'
  """
  result = execute_gaql(
      query=query,
      customer_id=customer_id,
      login_customer_id=login_customer_id,
  )
  if not result["data"]:
    raise ToolError(f"Job not found: {job_resource_name}")

  row = result["data"][0]
  return {
      "status": row.get("offline_user_data_job.status"),
      "failure_reason": row.get("offline_user_data_job.failure_reason"),
      "job_resource_name": job_resource_name,
  }
