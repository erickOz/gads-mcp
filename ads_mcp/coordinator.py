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

"""The coordinator for the Google Ads API MCP."""

from fastmcp import FastMCP

# Sent to the model when a client connects. Turns 78 tools + skill playbooks into
# a guided experience: the model knows what this server does, when to orient the
# user, and the safety rules — instead of waiting to be told exactly what to do.
SERVER_INSTRUCTIONS = """\
This server manages Google Ads accounts through natural language: reporting,
campaign/ad/keyword management, bidding, budgets, conversions, audiences,
geo/demographic targeting, experiments, and the Keyword Planner (78 tools).

GUIDANCE — orient the user, don't wait:
When the goal is unclear or the user asks something open-ended ("what can you
do?", "help me with my account", "where do I start?"), do NOT guess or dump a
tool list. Invoke the `start-here` prompt to interview them and route to the
right workflow. For a proactive review, use `account-audit`.

SKILL PLAYBOOKS (exposed as prompts) — prefer these for multi-step goals:
- start-here: orient a user who isn't sure what they need
- account-audit: full account review -> prioritized action plan
- wasted-spend-audit: find and cut non-converting spend
- campaign-launch: build a new Search campaign end to end
- quality-score-optimization: raise low Quality Score keywords
- experiment-workflow: run a safe A/B test
- offline-conversions: import CRM conversions for Smart Bidding
- account-performance-diagnostics: diagnose a performance drop

SAFETY:
- Always confirm before any write/mutate operation and summarize what will
  change. New campaigns are created PAUSED.
- Never invent IDs — look them up with reporting tools or execute_gaql first.
- IDs are digits only. Monetary values are in micros (1,000,000 = 1 unit).
"""

# Initialize FastMCP server
mcp_server = FastMCP(
    name="Google Ads API",
    instructions=SERVER_INSTRUCTIONS,
    mask_error_details=True,
    client_log_level="error",
)
