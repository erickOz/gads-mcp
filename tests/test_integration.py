"""Integration smoke test: the server wires up tools, prompts, and instructions.

Imports the stdio entrypoint (which runs register_enabled_tools + register_skills
at module load) and asserts the full surface is exposed, catching wiring
regressions that per-module unit tests can't.
"""

import asyncio

import ads_mcp.stdio  # noqa: F401  (module import registers tools + skills)
from ads_mcp.coordinator import mcp_server


def test_server_exposes_full_tool_surface():
    tools = asyncio.run(mcp_server.list_tools())
    names = {t.name for t in tools}
    assert len(tools) == 78
    # Core, read, and write tools all present.
    assert {"execute_gaql", "list_accessible_accounts"} <= names  # core
    assert "get_campaign_performance" in names  # reporting
    assert "create_campaign" in names  # write


def test_server_exposes_all_skills_as_prompts():
    prompts = {p.name for p in asyncio.run(mcp_server.list_prompts())}
    expected = {
        "start-here",
        "account-audit",
        "wasted-spend-audit",
        "campaign-launch",
        "quality-score-optimization",
        "experiment-workflow",
        "offline-conversions",
        "account-performance-diagnostics",
    }
    assert expected <= prompts


def test_server_has_guidance_instructions():
    instructions = mcp_server.instructions or ""
    assert "start-here" in instructions
    assert "GUIDANCE" in instructions
