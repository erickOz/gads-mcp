"""Campaign experiment tools — A/B testing for Google Ads campaigns."""

from typing import Any, Literal

from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools.api import execute_gaql, get_ads_client


ExperimentType = Literal[
    "SEARCH_CUSTOM",
    "DISPLAY_CUSTOM",
    "SEARCH_AUTOMATED_BIDDING_STRATEGY",
    "DISPLAY_AUTOMATED_BIDDING_STRATEGY",
    "SHOPPING_AUTOMATED_BIDDING_STRATEGY",
]


@mcp.tool()
def create_experiment(
    customer_id: str,
    name: str,
    campaign_id: str,
    traffic_split_percent: int = 50,
    experiment_type: ExperimentType = "SEARCH_CUSTOM",
    description: str = "",
    suffix: str = " (experiment)",
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Creates a campaign experiment for A/B testing.

  An experiment splits traffic between your existing campaign (control) and
  a copy (treatment) that you can modify. Google measures which performs
  better on your key metrics. After the experiment, promote the winner.

  The experiment starts in SETUP status. After creation:
  1. Modify the treatment campaign (bidding, ads, keywords, etc.)
  2. Call schedule_experiment to begin the test
  3. Monitor with list_experiments
  4. Call promote_experiment to make the winner permanent, or end it

  Args:
      customer_id: The ID of the customer account (digits only).
      name: Display name for the experiment.
      campaign_id: The base campaign to test against (becomes control arm).
      traffic_split_percent: Percent of traffic for the treatment arm (1–99).
          Control gets the remainder. Defaults to 50 (50/50 split).
      experiment_type: Type of experiment. SEARCH_CUSTOM for Search campaigns,
          DISPLAY_CUSTOM for Display, etc. Defaults to SEARCH_CUSTOM.
      description: Optional description.
      suffix: Suffix appended to the treatment campaign name. Defaults to
          " (experiment)".
      login_customer_id: Optional MCC account ID.

  Returns:
      experiment_id, resource_name, and treatment_campaign_id.
  """
  if traffic_split_percent < 1 or traffic_split_percent > 99:
    raise ToolError("traffic_split_percent must be between 1 and 99.")

  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  experiment_service = ads_client.get_service("ExperimentService")
  arm_service = ads_client.get_service("ExperimentArmService")

  # Step 1: Create the experiment
  experiment = ads_client.get_type("Experiment")
  experiment.name = name
  experiment.description = description
  experiment.suffix = suffix
  experiment.type_ = getattr(
      ads_client.enums.ExperimentTypeEnum, experiment_type
  )
  experiment.status = ads_client.enums.ExperimentStatusEnum.SETUP

  exp_op = ads_client.get_type("ExperimentOperation")
  exp_op.create = experiment

  try:
    exp_response = experiment_service.mutate_experiments(
        customer_id=customer_id, operations=[exp_op]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  experiment_resource = exp_response.results[0].resource_name

  # Step 2: Create control and treatment arms
  campaign_resource = f"customers/{customer_id}/campaigns/{campaign_id}"

  control_arm = ads_client.get_type("ExperimentArm")
  control_arm.experiment = experiment_resource
  control_arm.name = "Control"
  control_arm.control = True
  control_arm.traffic_split = 100 - traffic_split_percent
  control_arm.campaigns.append(campaign_resource)

  treatment_arm = ads_client.get_type("ExperimentArm")
  treatment_arm.experiment = experiment_resource
  treatment_arm.name = "Treatment"
  treatment_arm.control = False
  treatment_arm.traffic_split = traffic_split_percent

  control_op = ads_client.get_type("ExperimentArmOperation")
  control_op.create = control_arm
  treatment_op = ads_client.get_type("ExperimentArmOperation")
  treatment_op.create = treatment_arm

  try:
    arm_response = arm_service.mutate_experiment_arms(
        customer_id=customer_id, operations=[control_op, treatment_op]
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  experiment_id = experiment_resource.split("/")[-1]

  return {
      "experiment_id": experiment_id,
      "resource_name": experiment_resource,
      "name": name,
      "status": "SETUP",
      "control_arm": arm_response.results[0].resource_name,
      "treatment_arm": arm_response.results[1].resource_name,
      "traffic_split": f"{100 - traffic_split_percent}/{traffic_split_percent}",
  }


@mcp.tool()
def list_experiments(
    customer_id: str,
    status_filter: str | None = None,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Lists all campaign experiments with their status and performance.

  Args:
      customer_id: The ID of the customer account (digits only).
      status_filter: Optional filter by status: SETUP, INITIATED, ENABLED,
          HALTED, PROMOTED, GRADUATED, REMOVED. If omitted, returns all.
      login_customer_id: Optional MCC account ID.

  Returns:
      List of experiments with id, name, type, status, start/end dates.
  """
  query = """
    SELECT
      experiment.id,
      experiment.name,
      experiment.description,
      experiment.type,
      experiment.status,
      experiment.start_date,
      experiment.end_date,
      experiment.resource_name
    FROM experiment
  """
  if status_filter:
    query += f"\n    WHERE experiment.status = '{status_filter}'"
  query += "\n    ORDER BY experiment.name"

  result = execute_gaql(
      query=query,
      customer_id=customer_id,
      login_customer_id=login_customer_id,
  )

  experiments = [
      {
          "experiment_id": row.get("experiment.id"),
          "name": row.get("experiment.name"),
          "description": row.get("experiment.description"),
          "type": row.get("experiment.type"),
          "status": row.get("experiment.status"),
          "start_date": row.get("experiment.start_date"),
          "end_date": row.get("experiment.end_date"),
          "resource_name": row.get("experiment.resource_name"),
      }
      for row in result["data"]
  ]

  return {"experiments": experiments, "total": len(experiments)}


@mcp.tool()
def schedule_experiment(
    customer_id: str,
    experiment_id: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Schedules a SETUP experiment to start running (moves to INITIATED).

  Only call this after creating the experiment and making all desired changes
  to the treatment campaign. Once scheduled, the experiment goes live and
  starts splitting traffic according to the configured arms.

  Args:
      customer_id: The ID of the customer account (digits only).
      experiment_id: ID of the experiment (from create_experiment).
      login_customer_id: Optional MCC account ID.

  Returns:
      Confirmation that the experiment was scheduled.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  experiment_resource = (
      f"customers/{customer_id}/experiments/{experiment_id}"
  )

  try:
    ads_client.get_service("ExperimentService").schedule_experiment(
        resource_name=experiment_resource
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "experiment_id": experiment_id,
      "status": "INITIATED",
      "message": "Experiment scheduled. Traffic splitting will begin shortly.",
  }


@mcp.tool()
def promote_experiment(
    customer_id: str,
    experiment_id: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Promotes the treatment arm of an experiment, making it the new campaign.

  This applies the treatment campaign's settings (bids, ads, keywords, etc.)
  to the original campaign and ends the experiment. This action cannot be
  undone.

  Args:
      customer_id: The ID of the customer account (digits only).
      experiment_id: ID of the experiment to promote.
      login_customer_id: Optional MCC account ID.

  Returns:
      Confirmation that the experiment was promoted.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  experiment_resource = (
      f"customers/{customer_id}/experiments/{experiment_id}"
  )

  try:
    ads_client.get_service("ExperimentService").promote_experiment(
        resource_name=experiment_resource
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "experiment_id": experiment_id,
      "status": "PROMOTED",
      "message": "Treatment campaign promoted. Original campaign updated.",
  }


@mcp.tool()
def end_experiment(
    customer_id: str,
    experiment_id: str,
    login_customer_id: str | None = None,
) -> dict[str, Any]:
  """Ends an experiment without promoting either arm.

  Traffic returns 100% to the original campaign. The experiment data
  remains available for reporting.

  Args:
      customer_id: The ID of the customer account (digits only).
      experiment_id: ID of the experiment to end.
      login_customer_id: Optional MCC account ID.

  Returns:
      Confirmation that the experiment was ended.
  """
  ads_client = get_ads_client()
  if login_customer_id:
    ads_client.login_customer_id = login_customer_id

  experiment_resource = (
      f"customers/{customer_id}/experiments/{experiment_id}"
  )

  try:
    ads_client.get_service("ExperimentService").end_experiment(
        resource_name=experiment_resource
    )
  except GoogleAdsException as e:
    raise ToolError("\n".join(str(i) for i in e.failure.errors)) from e

  return {
      "experiment_id": experiment_id,
      "status": "ENDED",
      "message": "Experiment ended. All traffic returned to original campaign.",
  }
