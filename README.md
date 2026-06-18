# Google Ads MCP Server

An implementation of the [Model Context Protocol (MCP)](https://modelcontextprotocol.io) that connects AI assistants directly to the Google Ads API. Ask Claude, Gemini, or any MCP-compatible LLM to manage, analyze, and optimize your campaigns in natural language — no GAQL required.

**This is not an officially supported Google product.**

---

## What you can do

Talk to your Google Ads account like you would to a colleague:

```
"Which campaigns had the worst cost-per-conversion last month?"
"Pause all keywords with Quality Score below 5 and more than 1000 impressions"
"Create a new ad group for branded keywords in campaign 123456"
"Show me competitor auction insights for my top campaign"
"Apply Google's budget recommendations automatically"
```

**78 tools** covering the full Google Ads API lifecycle:

| Category | Tools |
|----------|-------|
| Reporting | Campaign metrics, keyword performance, search terms, Quality Score, auction insights, ad performance |
| Campaign management | Create, update status/budget/bidding, Performance Max |
| Ad groups & ads | Create/update groups, responsive search ads, ad status |
| Keywords | Add, update bids, pause, negatives (ad group & campaign level) |
| Assets & extensions | Sitelinks, callouts, call, promotion, price, lead form, images |
| Audiences | Create rule-based lists, apply to ad groups with bid modifiers |
| Customer Match | Create CRM audiences from hashed emails, phones, and addresses |
| Recommendations | List and auto-apply Google's optimization suggestions |
| Conversions | Create conversion actions, upload offline click/call conversions from CRM |
| Labels | Create, apply, list labels across campaigns and ad groups |
| Geographic targeting | Search geo targets, add/list/remove location targets per campaign |
| Demographic targeting | Age range, gender, and device bid modifiers |
| Ad scheduling | Time-of-day and day-of-week bid modifiers per campaign |
| Keyword Planner | Keyword ideas with search volume + traffic forecasts at a given budget |
| Shared budgets | Create portfolio budgets and assign campaigns to them |
| Portfolio bidding | Create and assign shared automated bidding strategies (Target CPA, ROAS) |
| A/B experiments | Create, schedule, promote, or end campaign experiments |
| Change history | Audit log of who changed what and when (last 30 days) |
| Raw queries | Execute any GAQL query with built-in schema reference |
| Account | List accessible accounts (MCC support) |

---

## Quick Start

### Requirements

- Python 3.12+
- [`uv`](https://github.com/astral-sh/uv) package manager
- A Google Ads API developer token and OAuth2 credentials

### 1. Get credentials

Create a `google-ads.yaml` file with your Google Ads API credentials:

```yaml
developer_token: YOUR_DEVELOPER_TOKEN
client_id: YOUR_CLIENT_ID
client_secret: YOUR_CLIENT_SECRET
refresh_token: YOUR_REFRESH_TOKEN
login_customer_id: YOUR_MCC_ID  # optional but recommended
```

To generate OAuth2 credentials, use the [authentication example](https://github.com/googleads/google-ads-python/blob/main/examples/authentication/generate_user_credentials.py) from `google-ads-python`.

### 2. Install

```bash
git clone https://github.com/erickoz/gads-mcp
cd gads-mcp
uv sync
```

### 3. Run

```bash
GOOGLE_ADS_CREDENTIALS=/path/to/google-ads.yaml uv run run-mcp-server
```

The server starts on `http://localhost:8000/mcp`.

---

## Connect your AI assistant

### Claude Desktop (local)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/gads-mcp", "-m", "ads_mcp.stdio"],
      "env": { "GOOGLE_ADS_CREDENTIALS": "/path/to/google-ads.yaml" }
    }
  }
}
```

### Claude.ai Web & Claude Mobile (remote)

Deploy to Cloud Run (see [deployment guide](deploy/cloud-run.sh)) to get a public HTTPS URL,
then go to **Settings → Integrations → Add MCP Server** and enter:

```
https://your-service.run.app/mcp
```

Works identically on browser and mobile. See [CLAUDE.md](CLAUDE.md) for the full setup guide.

### Gemini CLI

```json5
{
  "mcpServers": {
    "GoogleAds": {
      "command": "pipx",
      "args": ["run", "--spec", "git+https://github.com/erickoz/gads-mcp.git", "run-mcp-server"],
      "env": { "GOOGLE_ADS_CREDENTIALS": "PATH_TO_YAML" },
      "timeout": 30000,
      "trust": false
    }
  }
}
```

### Other compatible clients

Cursor, Windsurf, Cline (VS Code), Continue.dev — any client that supports MCP HTTP transport
can connect to the deployed server URL.

---

## Deploy publicly

```bash
# Docker (local)
cp .env.example .env   # fill in your values
docker compose up

# Google Cloud Run (public HTTPS endpoint)
./deploy/cloud-run.sh
```

See [`.env.example`](.env.example) for all configuration options including OAuth2 setup
for restricting access to specific Google accounts.

---

## Disclaimer

Copyright Google LLC. Supported by Google LLC and/or its affiliate(s). This solution, including any related sample code or data, is made available on an "as is," "as available," and "with all faults" basis, solely for illustrative purposes, and without warranty or representation of any kind. This solution is experimental, unsupported and provided solely for your convenience. Your use of it is subject to your agreements with Google, as applicable, and may constitute a beta feature as defined under those agreements. To the extent that you make any data available to Google in connection with your use of the solution, you represent and warrant that you have all necessary and appropriate rights, consents and permissions to permit Google to use and process that data. By using any portion of this solution, you acknowledge, assume and accept all risks, known and unknown, associated with its usage and any processing of data by Google, including with respect to your deployment of any portion of this solution in your systems, or usage in connection with your business, if at all. With respect to the entrustment of personal information to Google, you will verify that the established system is sufficient by checking Google's privacy policy and other public information, and you agree that no further information will be provided by Google.

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## License

Apache 2.0 — see [LICENSE](LICENSE).
