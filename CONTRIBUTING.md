# How to contribute

We'd love to accept your patches and contributions to this project.

## Before you begin

### Sign our Contributor License Agreement

Contributions to this project must be accompanied by a
[Contributor License Agreement](https://cla.developers.google.com/about) (CLA).
You (or your employer) retain the copyright to your contribution; this simply
gives us permission to use and redistribute your contributions as part of the
project.

If you or your current employer have already signed the Google CLA (even if it
was for a different project), you probably don't need to do it again.

Visit <https://cla.developers.google.com/> to see your current agreements or to
sign a new one.

### Review our community guidelines

This project follows
[Google's Open Source Community Guidelines](https://opensource.google/conduct/).

## Contribution process

### Code reviews

All submissions, including submissions by project members, require review. We
use GitHub pull requests for this purpose. Consult
[GitHub Help](https://help.github.com/articles/about-pull-requests/) for more
information on using pull requests.

## Architecture notes

Conventions to follow when extending the server:

- **`execute_gaql` returns flat, dotted keys.** A result row is
  `{"campaign.id": "1", "metrics.cost_micros": 100}` — not nested. Read fields
  with `row.get("campaign.id")`. Tests must mock this flat shape.
- **Validate every value interpolated into GAQL or a resource name.** Use the
  helpers in `ads_mcp/tools/validation.py` (`validate_numeric_id`,
  `validate_id_list`, `validate_enum`, `validate_resource_name`,
  `validate_date`). The `Literal` type hints only guard the MCP boundary, not
  direct/programmatic calls.
- **Adding a tool:** put it in a domain module under `ads_mcp/tools/`, decorate
  with `@mcp.tool()`, and get the client/query helpers from `ads_mcp.tools.api`.
  Wrap Google Ads mutations in `try/except GoogleAdsException` → `ToolError`.
- **Adding a namespace:** register it in `ads_mcp/config.py`
  (`NAMESPACE_MODULES`) and `tools_config.yaml` so it can be toggled.
- **Adding a skill:** drop a `SKILL.md` (with `name` + `description`
  frontmatter) in `ads_mcp/skills/<name>/`; `skill_registry.py` exposes it as an
  MCP prompt automatically.
- **Tests:** add a module test mocking `get_ads_client` / `execute_gaql`, then
  raise the `--cov-fail-under` floor in `.github/workflows/ci.yml`.
