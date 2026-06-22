# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tool-registration configuration for the Google Ads MCP server.

Adapted from the upstream `googleads/google-ads-mcp` `config.py` to our
architecture, where each tool module maps 1:1 to a namespace. Tools register
themselves via `@mcp.tool()` decorators at import time, so we gate which
namespaces get imported based on `tools_config.yaml`.
"""

import importlib
import importlib.resources
import logging
import os

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_FILE = "tools_config.yaml"

# Environment variable to point the server at an explicit config file.
CONFIG_PATH_ENV_VAR = "GOOGLE_ADS_MCP_TOOLS_CONFIG"

# Modules always loaded regardless of config: core GAQL/account tools and docs.
# Every other tool module imports helpers from `api`, so it must stay enabled.
CORE_MODULES = ("api", "docs")

# Namespace -> tool module under `ads_mcp.tools`. Each is toggleable in the YAML.
NAMESPACE_MODULES = {
    "reporting": "reporting",
    "campaigns": "campaigns",
    "mutate": "mutate",  # ad groups, ads, keywords, negatives
    "assets": "assets",
    "audiences": "audiences",
    "bidding_strategies": "bidding_strategies",
    "budgets": "budgets",
    "change_history": "change_history",
    "conversions": "conversions",
    "customer_match": "customer_match",
    "experiments": "experiments",
    "keyword_planner": "keyword_planner",
    "labels": "labels",
    "pmax": "pmax",
    "recommendations": "recommendations",
    "targeting": "targeting",
}

ALL_NAMESPACES = list(NAMESPACE_MODULES)


class ToolsConfig:
  """Manages tool registration configuration parsed from YAML."""

  def __init__(self, config_dict=None):
    self._config = config_dict or {}

  @classmethod
  def _resolve_config_path(cls, filepath=None):
    """Resolves which config file to load.

    Resolution order:
      1. An explicit ``filepath`` argument, if provided.
      2. The ``GOOGLE_ADS_MCP_TOOLS_CONFIG`` environment variable.
      3. ``tools_config.yaml`` in the current working directory.
      4. The default ``tools_config.yaml`` bundled with the package.

    Returns the resolved path, or ``None`` if no config file can be found.
    """
    explicit = filepath or os.environ.get(CONFIG_PATH_ENV_VAR)
    if explicit:
      if not os.path.exists(explicit):
        raise FileNotFoundError(
            f"Tools configuration file '{explicit}' not found."
        )
      return explicit

    if os.path.exists(DEFAULT_CONFIG_FILE):
      return DEFAULT_CONFIG_FILE

    bundled = importlib.resources.files("ads_mcp").joinpath(DEFAULT_CONFIG_FILE)
    if bundled.is_file():
      return str(bundled)

    return None

  @classmethod
  def load(cls, filepath=None):
    """Loads configuration from a YAML file.

    Falls back to enabling all namespaces if no config file is found.
    """
    resolved = cls._resolve_config_path(filepath)
    if resolved is None:
      logger.warning(
          "No tools configuration found; enabling all namespaces."
      )
      return cls()

    try:
      with open(resolved, "r") as file:
        data = yaml.safe_load(file)
        if data is None:
          return cls()
        if not isinstance(data, dict):
          raise ValueError("Configuration root must be a YAML mapping")
        return cls(data)
    except Exception as e:
      raise ValueError(
          f"Failed to parse configuration file '{resolved}': {e}"
      ) from e

  def is_namespace_enabled(self, namespace):
    """Determines if a tool namespace is enabled.

    With no `namespaces` block configured, every known namespace is enabled
    (preserving the default behaviour of registering all tools).
    """
    namespaces = self._config.get("namespaces")
    if not namespaces:
      return namespace in ALL_NAMESPACES

    value = namespaces.get(namespace)
    if value is None:
      return False
    if isinstance(value, bool):
      return value
    if isinstance(value, dict):
      return bool(value.get("enabled", True))
    return bool(value)


def register_enabled_tools(config=None):
  """Imports tool modules so their `@mcp.tool()` decorators register them.

  Core modules are always imported; namespaced modules are imported only when
  enabled in the config. Returns the list of namespaces that were enabled.
  """
  config = config or ToolsConfig.load()

  for module in CORE_MODULES:
    importlib.import_module(f"ads_mcp.tools.{module}")

  enabled = []
  for namespace, module in NAMESPACE_MODULES.items():
    if config.is_namespace_enabled(namespace):
      importlib.import_module(f"ads_mcp.tools.{module}")
      enabled.append(namespace)

  logger.info("Registered tool namespaces: %s", ", ".join(enabled))
  return enabled
