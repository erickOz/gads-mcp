"""Label management tools for the Google Ads API.

Labels let you tag campaigns, ad groups, ads, and keywords to organize
experiments, A/B tests, client segments, or optimization phases.
"""

from typing import Literal

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import get_ads_client, execute_gaql


LabelEntityType = Literal["CAMPAIGN", "AD_GROUP", "AD", "KEYWORD"]


@mcp.tool()
def create_label(
    customer_id: str,
    name: str,
    description: str | None = None,
    background_color: str | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Creates a label for organizing campaigns, ad groups, ads, or keywords.

  Labels are useful for tagging entities by experiment variant, optimization
  phase, client segment, or any custom classification.

  Args:
      customer_id: The ID of the customer account (digits only).
      name: Label name (must be unique within the account).
      description: Optional short description for the label.
      background_color: Optional hex color code (e.g. "#FF0000" for red).
          Used in the Google Ads UI to visually distinguish labels.
      login_customer_id: Optional MCC account ID.

  Returns:
      label_id and resource_name of the created label.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  label = ads_client.get_type("Label")
  label.name = name
  label.status = ads_client.enums.LabelStatusEnum.ENABLED

  if description:
    label.text_label.description = description
  if background_color:
    label.text_label.background_color = background_color

  operation = ads_client.get_type("LabelOperation")
  operation.create = label

  try:
    response = ads_client.get_service("LabelService").mutate_labels(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  resource_name = response.results[0].resource_name
  label_id = resource_name.split("/")[-1]

  return {
      "label_id": label_id,
      "resource_name": resource_name,
      "name": name,
  }


@mcp.tool()
def list_labels(
    customer_id: str,
    login_customer_id: str | None = None,
) -> dict:
  """Lists all labels defined in the account.

  Use this to get label IDs before applying labels to entities.

  Args:
      customer_id: The ID of the customer account (digits only).
      login_customer_id: Optional MCC account ID.

  Returns:
      List of labels with id, name, description, background_color, and status.
  """
  gaql = """
    SELECT
      label.id,
      label.name,
      label.status,
      label.text_label.description,
      label.text_label.background_color
    FROM label
    WHERE label.status = 'ENABLED'
    ORDER BY label.name ASC
  """

  response = execute_gaql(query=gaql, customer_id=customer_id, login_customer_id=login_customer_id)

  rows = []
  for row in response["data"]:
    rows.append({
        "label_id": row.get("label.id"),
        "name": row.get("label.name"),
        "status": row.get("label.status"),
        "description": row.get("label.text_label.description"),
        "background_color": row.get("label.text_label.background_color"),
    })

  return {"labels": rows, "total": len(rows)}


@mcp.tool()
def apply_labels(
    customer_id: str,
    label_id: str,
    entity_type: LabelEntityType,
    entity_ids: list[str],
    ad_group_id: str | None = None,
    login_customer_id: str | None = None,
) -> dict:
  """Applies a label to one or more campaigns, ad groups, ads, or keywords.

  Use list_labels to get the label_id.
  Use execute_gaql to find entity IDs before applying.

  For entity_type=AD: provide the ad IDs and the containing ad_group_id.
  For entity_type=KEYWORD: provide the criterion IDs and the containing ad_group_id.
  For entity_type=CAMPAIGN or AD_GROUP: just provide entity_ids.

  Args:
      customer_id: The ID of the customer account (digits only).
      label_id: The ID of the label to apply (from list_labels).
      entity_type: CAMPAIGN, AD_GROUP, AD, or KEYWORD.
      entity_ids: List of entity IDs to apply the label to.
      ad_group_id: Required for entity_type=AD or KEYWORD.
      login_customer_id: Optional MCC account ID.

  Returns:
      Number of labels applied and the entity type.
  """
  if entity_type in ("AD", "KEYWORD") and not ad_group_id:
    raise ToolError(f"ad_group_id is required when entity_type={entity_type}.")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  label_resource = f"customers/{customer_id}/labels/{label_id}"

  try:
    if entity_type == "CAMPAIGN":
      service = ads_client.get_service("CampaignLabelService")
      ops = []
      for eid in entity_ids:
        link = ads_client.get_type("CampaignLabel")
        link.campaign = f"customers/{customer_id}/campaigns/{eid}"
        link.label = label_resource
        op = ads_client.get_type("CampaignLabelOperation")
        op.create = link
        ops.append(op)
      response = service.mutate_campaign_labels(customer_id=customer_id, operations=ops)

    elif entity_type == "AD_GROUP":
      service = ads_client.get_service("AdGroupLabelService")
      ops = []
      for eid in entity_ids:
        link = ads_client.get_type("AdGroupLabel")
        link.ad_group = f"customers/{customer_id}/adGroups/{eid}"
        link.label = label_resource
        op = ads_client.get_type("AdGroupLabelOperation")
        op.create = link
        ops.append(op)
      response = service.mutate_ad_group_labels(customer_id=customer_id, operations=ops)

    elif entity_type == "AD":
      service = ads_client.get_service("AdGroupAdLabelService")
      ops = []
      for eid in entity_ids:
        link = ads_client.get_type("AdGroupAdLabel")
        link.ad_group_ad = f"customers/{customer_id}/adGroupAds/{ad_group_id}~{eid}"
        link.label = label_resource
        op = ads_client.get_type("AdGroupAdLabelOperation")
        op.create = link
        ops.append(op)
      response = service.mutate_ad_group_ad_labels(customer_id=customer_id, operations=ops)

    elif entity_type == "KEYWORD":
      service = ads_client.get_service("AdGroupCriterionLabelService")
      ops = []
      for eid in entity_ids:
        link = ads_client.get_type("AdGroupCriterionLabel")
        link.ad_group_criterion = (
            f"customers/{customer_id}/adGroupCriteria/{ad_group_id}~{eid}"
        )
        link.label = label_resource
        op = ads_client.get_type("AdGroupCriterionLabelOperation")
        op.create = link
        ops.append(op)
      response = service.mutate_ad_group_criterion_labels(
          customer_id=customer_id, operations=ops
      )

  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "applied": len(response.results),
      "entity_type": entity_type,
      "label_id": label_id,
  }
