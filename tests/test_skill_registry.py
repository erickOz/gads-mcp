"""Tests for skill -> MCP prompt registration (ads_mcp.skill_registry)."""

import asyncio

from ads_mcp.skill_registry import register_skills, _parse_skill, SKILLS_DIR
import glob
import os


def test_register_skills_returns_all_skill_names():
    names = register_skills()
    # Every SKILL.md on disk should be registered.
    on_disk = {
        os.path.basename(os.path.dirname(p))
        for p in glob.glob(os.path.join(SKILLS_DIR, "*", "SKILL.md"))
    }
    assert set(names) == on_disk
    assert "wasted-spend-audit" in names


def test_skills_are_exposed_as_prompts():
    register_skills()
    from ads_mcp.coordinator import mcp_server

    prompts = {p.name for p in asyncio.run(mcp_server.list_prompts())}
    assert "campaign-launch" in prompts
    assert "offline-conversions" in prompts


def test_every_skill_has_name_and_description():
    for path in glob.glob(os.path.join(SKILLS_DIR, "*", "SKILL.md")):
        name, description, body = _parse_skill(path)
        assert name and description and body


def test_register_skills_is_idempotent():
    first = register_skills()
    second = register_skills()  # must not raise on duplicate prompt names
    assert first == second
