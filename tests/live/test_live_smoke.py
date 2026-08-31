"""Live smoke tests against the real Google Ads API.

Unit tests mock ``execute_gaql``, so they CANNOT catch invalid GAQL field names
or API-version drift — that's exactly how the v24 ``quality_info.ad_relevance``
bug slipped through. These tests issue a few READ-ONLY queries against a real
account and assert the reporting tools return successfully, turning a wrong GAQL
field into a red test.

They are SKIPPED unless a real test account is configured, so normal CI stays
green without secrets. To run them:

    # credentials (either a yaml file or the GOOGLE_ADS_* env vars)
    export GOOGLE_ADS_CREDENTIALS=/path/to/google-ads.yaml
    # the account to query, and (optional) the MCC to log in through
    export GOOGLE_ADS_MCP_TEST_CUSTOMER_ID=1234567890
    export GOOGLE_ADS_MCP_TEST_LOGIN_CUSTOMER_ID=0987654321

    uv run pytest tests/live -v

Read-only by design: these never call a mutate/write tool.
"""

import os

import pytest

CUSTOMER_ID = os.environ.get("GOOGLE_ADS_MCP_TEST_CUSTOMER_ID")
LOGIN = os.environ.get("GOOGLE_ADS_MCP_TEST_LOGIN_CUSTOMER_ID")
DATE_RANGE = "LAST_30_DAYS"

pytestmark = pytest.mark.skipif(
    not CUSTOMER_ID,
    reason=(
        "set GOOGLE_ADS_MCP_TEST_CUSTOMER_ID (and credentials) to run the live "
        "smoke tests"
    ),
)


@pytest.fixture(scope="module", autouse=True)
def _require_credentials():
  """Skips the module cleanly if Google Ads credentials aren't loadable."""
  from ads_mcp.tools.api import get_ads_client

  try:
    get_ads_client()
  except Exception as exc:  # noqa: BLE001 - any credential/config failure -> skip
    pytest.skip(f"Google Ads credentials not available: {exc}")


def test_campaign_performance_live():
  from ads_mcp.tools.reporting import get_campaign_performance

  result = get_campaign_performance(
      CUSTOMER_ID, DATE_RANGE, login_customer_id=LOGIN
  )
  assert "campaign_performance" in result


def test_keyword_performance_live():
  # Regression guard for the v24 quality_info.* field bug.
  from ads_mcp.tools.reporting import get_keyword_performance

  result = get_keyword_performance(
      CUSTOMER_ID, DATE_RANGE, login_customer_id=LOGIN, limit=5
  )
  assert "keywords" in result


def test_quality_score_report_live():
  # Regression guard for the v24 quality_info.* field bug.
  from ads_mcp.tools.reporting import get_quality_score_report

  result = get_quality_score_report(
      CUSTOMER_ID, login_customer_id=LOGIN, limit=5
  )
  assert "keywords" in result


def test_search_terms_report_live():
  from ads_mcp.tools.reporting import get_search_terms_report

  result = get_search_terms_report(
      CUSTOMER_ID, DATE_RANGE, login_customer_id=LOGIN, limit=5
  )
  assert "search_terms" in result


def test_ad_performance_live():
  from ads_mcp.tools.reporting import get_ad_performance

  result = get_ad_performance(
      CUSTOMER_ID, DATE_RANGE, login_customer_id=LOGIN, limit=5
  )
  assert "ads" in result


def test_auction_insights_live():
  from ads_mcp.tools.reporting import get_auction_insights

  result = get_auction_insights(
      CUSTOMER_ID, DATE_RANGE, login_customer_id=LOGIN
  )
  assert "auction_insights" in result


# ── B-12 regression guards ──────────────────────────────────────────────────
# These three tools shipped broken: their GAQL referenced fields v24 rejects,
# and the mocked unit tests passed anyway because they never reach the API.


@pytest.fixture(scope="module")
def campaign_id():
  """An enabled campaign in the test account, or skip."""
  from ads_mcp.tools.api import execute_gaql

  result = execute_gaql(
      query=("SELECT campaign.id FROM campaign "
             "WHERE campaign.status = 'ENABLED' LIMIT 1"),
      customer_id=CUSTOMER_ID,
      login_customer_id=LOGIN,
  )
  rows = result["data"]
  if not rows:
    pytest.skip("no enabled campaign in the test account")
  return str(rows[0]["campaign.id"])


def test_list_experiments_live():
  # Guards `experiment.experiment_id`; `experiment.id` is UNRECOGNIZED_FIELD.
  from ads_mcp.tools.experiments import list_experiments

  result = list_experiments(CUSTOMER_ID, login_customer_id=LOGIN)
  assert "experiments" in result


def test_list_campaign_locations_live(campaign_id):
  # Guards the two-step geo lookup: selecting geo_target_constant.* from
  # campaign_criterion raises PROHIBITED_RESOURCE_TYPE_IN_SELECT_CLAUSE.
  from ads_mcp.tools.targeting import list_campaign_locations

  result = list_campaign_locations(
      CUSTOMER_ID, campaign_id, login_customer_id=LOGIN
  )
  assert "locations" in result


def test_list_ad_group_demographics_live(campaign_id):
  # Guards `WHERE campaign.id`; `ad_group.campaign.id` is UNRECOGNIZED_FIELD.
  from ads_mcp.tools.targeting import list_ad_group_demographics

  result = list_ad_group_demographics(
      CUSTOMER_ID, campaign_id, login_customer_id=LOGIN
  )
  assert "age_gender" in result
  assert "devices" in result
