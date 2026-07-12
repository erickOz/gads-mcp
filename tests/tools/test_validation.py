import pytest

from ads_mcp.tools.validation import (
    validate_numeric_id,
    validate_id_list,
    validate_enum,
    validate_resource_name,
    validate_date,
)


def test_validate_numeric_id_ok():
    assert validate_numeric_id("123") == "123"
    assert validate_numeric_id(456) == "456"  # ints are coerced to str


@pytest.mark.parametrize("bad", ["12'3", "abc", "1 OR 1=1", "", "12; DROP", "1.5"])
def test_validate_numeric_id_rejects_non_digits(bad):
    with pytest.raises(Exception, match="must contain digits only"):
        validate_numeric_id(bad, "campaign_id")


def test_validate_id_list_returns_validated_strings():
    assert validate_id_list(["1", "22", 333]) == ["1", "22", "333"]


def test_validate_id_list_rejects_injection_attempt():
    # A quote in an ID would break out of a GAQL IN (...) clause.
    with pytest.raises(Exception, match="must contain digits only"):
        validate_id_list(["1", "2') OR (1=1"], "campaign_id")


def test_validate_resource_name_ok():
    rn = "customers/123/offlineUserDataJobs/55"
    assert validate_resource_name(rn) == rn
    # composite ids use a tilde
    assert validate_resource_name("customers/1/adGroupCriteria/2~3")


@pytest.mark.parametrize("bad", ["x' OR '1'='1", "a; DROP", "with space", "quote'd"])
def test_validate_resource_name_rejects_unsafe(bad):
    with pytest.raises(Exception, match="unexpected characters"):
        validate_resource_name(bad, "job_resource_name")


def test_validate_date_ok():
    assert validate_date("2026-07-11") == "2026-07-11"


@pytest.mark.parametrize("bad", ["2026-7-1", "2026/07/11", "2026-07-11' OR '1'='1", "today", ""])
def test_validate_date_rejects_bad_format(bad):
    with pytest.raises(Exception, match="YYYY-MM-DD"):
        validate_date(bad, "start_date")


def test_validate_enum_ok():
    assert validate_enum("ENABLED", {"ENABLED", "PAUSED"}, "status") == "ENABLED"


def test_validate_enum_rejects_unknown():
    with pytest.raises(Exception, match="Must be one of"):
        validate_enum("BOGUS", {"ENABLED", "PAUSED"}, "status")
