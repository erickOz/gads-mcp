# Changelog

All notable changes to this project are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- **Skill playbooks as MCP prompts** — `skill_registry.py` registers each
  `ads_mcp/skills/*/SKILL.md` as a prompt (discovery by description, body as the
  playbook). Playbooks: `start-here`, `account-audit`, `wasted-spend-audit`,
  `campaign-launch`, `quality-score-optimization`, `experiment-workflow`,
  `offline-conversions`, `account-performance-diagnostics`.
- **Guidance layer** — server `instructions` (capability map + routing to
  `start-here` + safety rules) so the model orients the user instead of waiting.
- **Configurable tools** — `tools_config.yaml` + `config.py` to enable/disable
  tool namespaces (e.g. a read-only reporting profile). `api`/`docs` are core.
- **Input validation** — `ads_mcp/tools/validation.py`
  (`validate_numeric_id`, `validate_id_list`, `validate_enum`,
  `validate_resource_name`, `validate_date`).
- **Tests** — suites for every write module plus config, validation,
  skill_registry, and an integration smoke test. Coverage ~20% → ~52%,
  CI `--cov-fail-under` ratchet.
- **Live smoke tests** (`tests/live/`) — read-only queries against a real
  account, skipped unless credentials + a test customer ID are set. The only
  tests that can catch invalid GAQL fields / API-version drift (unit tests mock
  `execute_gaql`). These found the three GAQL field bugs fixed below.

### Changed
- Bumped `google-ads` to `>=31.0.0` (Google Ads API v24). Verified live.
- Reporting `date_range` validation now delegates to `validation.validate_enum`
  (single source of truth from the `DateRange` Literal).

### Security
- Closed ~23 GAQL injection points across reporting, targeting, assets,
  experiments, change_history, and customer_match. Caller-supplied IDs, enums,
  resource names, and dates are validated before being interpolated into GAQL
  (the `Literal` type hints only guard the MCP boundary, not direct calls).

### Fixed
- **Invalid GAQL fields in v24** (all caught by the live smoke tests):
  - `get_keyword_performance` / `get_quality_score_report` used
    `quality_info.ad_relevance` / `quality_info.landing_page_experience`
    → `creative_quality_score` / `post_click_quality_score`.
  - `get_ad_performance` used `ad_group_ad.ad.type_` (a Python attribute name)
    → `ad_group_ad.ad.type`.
  - `get_auction_insights` queried competitor-level fields the API doesn't expose
    (`segments.auction_insight.domain`, `metrics.search_overlap_rate`,
    `search_position_above_rate`, `search_outranking_share`). Reworked to return
    the available impression-share metrics (IS, top/abs-top IS, and share lost to
    rank vs budget).
- Stale tests that assumed a nested `execute_gaql` result shape (the real
  contract is flat, dotted keys).
- Wrapped the unhandled `create_offline_user_data_job` call so Google Ads API
  errors surface as a clean `ToolError`.
