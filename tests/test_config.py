"""Tests for the tools_config gating (ads_mcp.config)."""

import pytest

from ads_mcp.config import (
    ToolsConfig,
    ALL_NAMESPACES,
    NAMESPACE_MODULES,
    CORE_MODULES,
    register_enabled_tools,
)


def test_no_config_enables_all_namespaces():
    cfg = ToolsConfig()  # empty config -> everything on
    for ns in ALL_NAMESPACES:
        assert cfg.is_namespace_enabled(ns) is True


def test_empty_namespaces_block_enables_all():
    cfg = ToolsConfig({"namespaces": {}})
    assert cfg.is_namespace_enabled("reporting") is True


def test_explicit_namespace_toggles():
    cfg = ToolsConfig({"namespaces": {"reporting": True, "campaigns": False}})
    assert cfg.is_namespace_enabled("reporting") is True
    assert cfg.is_namespace_enabled("campaigns") is False


def test_omitted_namespace_is_disabled_when_block_present():
    # If a namespaces block is given, anything not listed is OFF.
    cfg = ToolsConfig({"namespaces": {"reporting": True}})
    assert cfg.is_namespace_enabled("mutate") is False


def test_dict_form_with_enabled_key():
    cfg = ToolsConfig({"namespaces": {"reporting": {"enabled": False}}})
    assert cfg.is_namespace_enabled("reporting") is False


def test_register_enabled_returns_enabled_list_and_adds_tools():
    # Registration is cumulative on the shared mcp_server singleton, so within
    # one interpreter we can only assert that enabled namespaces ARE present
    # (other tests may have imported other modules). True exclusion is proven
    # in the isolated subprocess test below.
    import asyncio
    from ads_mcp.coordinator import mcp_server

    cfg = ToolsConfig({"namespaces": {"reporting": True}})
    enabled = register_enabled_tools(cfg)

    assert enabled == ["reporting"]
    names = {t.name for t in asyncio.run(mcp_server.list_tools())}
    assert "execute_gaql" in names  # core
    assert "get_gaql_doc" in names  # docs core
    assert "get_campaign_performance" in names  # reporting


def test_reporting_only_profile_excludes_write_tools_in_fresh_process():
    # A fresh interpreter is the real deployment scenario: the server imports
    # only the enabled namespaces. This proves write tools never register.
    import subprocess
    import sys

    code = (
        "import asyncio;"
        "from ads_mcp.config import ToolsConfig, register_enabled_tools;"
        "from ads_mcp.coordinator import mcp_server;"
        "register_enabled_tools(ToolsConfig({'namespaces': {'reporting': True}}));"
        "names={t.name for t in asyncio.run(mcp_server.list_tools())};"
        "assert 'get_campaign_performance' in names;"
        "assert 'execute_gaql' in names;"
        "assert 'create_campaign' not in names, 'write tool leaked';"
        "assert 'add_keywords' not in names, 'write tool leaked';"
        "print('OK', len(names))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("OK")


def test_namespace_modules_cover_all_namespaces():
    assert set(NAMESPACE_MODULES) == set(ALL_NAMESPACES)
    # api/docs are core, never namespaced.
    assert "api" not in NAMESPACE_MODULES
    assert "api" in CORE_MODULES
    assert "docs" in CORE_MODULES
