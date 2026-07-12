"""Shared input validation helpers for the Google Ads API tools.

Several tools interpolate caller-supplied values directly into GAQL queries or
resource names. The MCP boundary enforces type hints (e.g. ``Literal``) but
direct/programmatic calls bypass that, so these helpers guard the interpolation
points against malformed input and GAQL injection.
"""

import re

from fastmcp.exceptions import ToolError

_NUMERIC_ID = re.compile(r"\d+")

# Google Ads resource names look like "customers/123/offlineUserDataJobs/55"
# or composite "customers/1/adGroupCriteria/2~3". Allow only those characters so
# a value cannot break out of a GAQL string literal.
_RESOURCE_NAME = re.compile(r"[A-Za-z0-9/_~.-]+")

_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")


def validate_numeric_id(value, field_name: str = "id") -> str:
  """Ensures ``value`` is a digits-only ID and returns it as a string.

  Raises ToolError otherwise. Use before interpolating an ID into GAQL or a
  resource name.
  """
  text = str(value)
  if not _NUMERIC_ID.fullmatch(text):
    raise ToolError(
        f"Invalid {field_name} '{value}': must contain digits only."
    )
  return text


def validate_id_list(values, field_name: str = "id") -> list[str]:
  """Validates every item in ``values`` as a numeric ID.

  Returns the list as validated strings so it can be used in place of the
  original iterable (e.g. inside a GAQL ``IN (...)`` clause).
  """
  return [validate_numeric_id(v, field_name) for v in values]


def validate_resource_name(value, field_name: str = "resource_name") -> str:
  """Ensures a Google Ads resource name is safe to interpolate into GAQL.

  Resource names are not numeric, so they can't use ``validate_numeric_id``;
  this guards against quotes/spaces that would break a GAQL string literal.
  """
  text = str(value)
  if not _RESOURCE_NAME.fullmatch(text):
    raise ToolError(
        f"Invalid {field_name} '{value}': contains unexpected characters."
    )
  return text


def validate_date(value, field_name: str = "date") -> str:
  """Ensures a date is 'YYYY-MM-DD' before interpolating it into GAQL.

  Guards against quotes/spaces in a value that lands inside a GAQL string
  literal. Calendar validity is left to the API.
  """
  text = str(value)
  if not _DATE.fullmatch(text):
    raise ToolError(
        f"Invalid {field_name} '{value}': expected format YYYY-MM-DD."
    )
  return text


def validate_enum(value, allowed, field_name: str = "value"):
  """Ensures ``value`` is one of ``allowed`` (any iterable). Returns it.

  Use before interpolating a string into a GAQL string literal where a
  ``Literal`` type hint is not already enforcing the allowed set.
  """
  if value not in allowed:
    allowed_str = ", ".join(sorted(str(a) for a in allowed))
    raise ToolError(
        f"Invalid {field_name} '{value}'. Must be one of: {allowed_str}."
    )
  return value
