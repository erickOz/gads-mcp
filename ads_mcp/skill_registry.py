"""Exposes the SKILL.md playbooks under ``ads_mcp/skills/`` to MCP clients.

Each skill is registered as an MCP **prompt**: its ``name`` becomes the prompt
name, its ``description`` drives discovery, and invoking it returns the playbook
body for the model to follow. Without this wiring the SKILL.md files are just
inert markdown in the repo — registering them is what makes them reachable from
clients like Claude Desktop.
"""

import glob
import os
import re

from fastmcp.prompts.prompt import Prompt

from ads_mcp.coordinator import mcp_server

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "skills")

_FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def _parse_skill(path: str):
  """Returns (name, description, body) from a SKILL.md file."""
  with open(path, "r", encoding="utf-8") as f:
    text = f.read()

  match = _FRONTMATTER.match(text)
  if not match:
    raise ValueError(f"Skill '{path}' is missing YAML frontmatter.")

  frontmatter, body = match.group(1), match.group(2).strip()
  name_match = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
  desc_match = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)
  if not name_match or not desc_match:
    raise ValueError(f"Skill '{path}' must define both name and description.")

  return name_match.group(1).strip(), desc_match.group(1).strip(), body


def register_skills(directory: str = SKILLS_DIR) -> list[str]:
  """Registers each ``<directory>/<name>/SKILL.md`` as an MCP prompt.

  Idempotent: re-registering a skill of the same name overwrites the prior one.
  Returns the list of registered skill names.
  """
  registered = []
  for path in sorted(glob.glob(os.path.join(directory, "*", "SKILL.md"))):
    name, description, body = _parse_skill(path)

    def _make_handler(playbook: str):
      def skill() -> str:
        return playbook

      return skill

    prompt = Prompt.from_function(
        _make_handler(body), name=name, description=description
    )
    mcp_server.add_prompt(prompt)
    registered.append(name)

  return registered
