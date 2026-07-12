import pytest
from unittest.mock import MagicMock

from ads_mcp.tools.customer_match import (
    _sha256,
    create_customer_match_list,
    get_customer_match_job_status,
    upload_customer_match_members,
)


def test_sha256_is_stable_and_lowercase_hex():
    # Customer Match requires SHA-256 hashed, normalized identifiers.
    assert _sha256("test@example.com") == _sha256("test@example.com")
    assert len(_sha256("a")) == 64


def test_create_customer_match_list_returns_id(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.customer_match.get_ads_client", return_value=mock_client
    )
    service = mock_client.get_service.return_value
    result = MagicMock()
    result.resource_name = "customers/123/userLists/999"
    service.mutate_user_lists.return_value.results = [result]

    out = create_customer_match_list("123", "CRM Leads")

    service.mutate_user_lists.assert_called_once()
    assert out["user_list_id"] == "999"
    assert out["name"] == "CRM Leads"


def test_get_job_status_reads_flat_key(mocker):
    mock_execute = mocker.patch("ads_mcp.tools.customer_match.execute_gaql")
    mock_execute.return_value = {
        "data": [
            {
                "offline_user_data_job.status": "RUNNING",
                "offline_user_data_job.failure_reason": None,
            }
        ]
    }

    out = get_customer_match_job_status(
        "123", "customers/123/offlineUserDataJobs/55"
    )

    assert out["status"] == "RUNNING"


def test_upload_customer_match_members_queues_and_runs(mocker):
    mock_client = MagicMock()
    mocker.patch(
        "ads_mcp.tools.customer_match.get_ads_client", return_value=mock_client
    )
    service = mock_client.get_service.return_value
    service.create_offline_user_data_job.return_value.resource_name = (
        "customers/123/offlineUserDataJobs/55"
    )

    out = upload_customer_match_members(
        "123",
        "999",
        [{"email": "a@b.com"}, {"phone": "+14155551234"}],
    )

    service.create_offline_user_data_job.assert_called_once()
    service.add_offline_user_data_job_operations.assert_called_once()
    service.run_offline_user_data_job.assert_called_once()
    assert out["job_resource_name"] == "customers/123/offlineUserDataJobs/55"
    assert out["members_queued"] == 2
    assert out["status"] == "RUNNING"


def test_upload_customer_match_members_rejects_empty(mocker):
    mocker.patch("ads_mcp.tools.customer_match.get_ads_client")
    with pytest.raises(Exception, match="cannot be empty"):
        upload_customer_match_members("123", "999", [])


def test_get_job_status_rejects_injection(mocker):
    # job_resource_name is interpolated into a GAQL string literal.
    mocker.patch("ads_mcp.tools.customer_match.execute_gaql")
    with pytest.raises(Exception, match="unexpected characters"):
        get_customer_match_job_status("123", "x' OR '1'='1")


def test_get_job_status_raises_when_not_found(mocker):
    mock_execute = mocker.patch("ads_mcp.tools.customer_match.execute_gaql")
    mock_execute.return_value = {"data": []}

    with pytest.raises(Exception, match="Job not found"):
        get_customer_match_job_status("123", "customers/123/offlineUserDataJobs/55")
