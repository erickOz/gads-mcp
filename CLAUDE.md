# Google Ads MCP — Claude Setup Guide

This guide covers three ways to connect Claude to this Google Ads MCP server.

---

## Option 1: Claude Desktop (local, stdio)

Best for: development, single-user use on your machine.

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "google-ads": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/path/to/gads-mcp",
        "-m",
        "ads_mcp.stdio"
      ],
      "env": {
        "GOOGLE_ADS_CREDENTIALS": "/path/to/google-ads.yaml"
      }
    }
  }
}
```

Restart Claude Desktop. You should see "google-ads" listed under MCP servers.

---

## Option 2: Claude.ai Web & Claude Mobile (remote HTTP)

Best for: accessing your Google Ads account from any device, including mobile.

### Step 1 — Deploy the server

Deploy to Cloud Run (recommended) or any HTTPS host:

```bash
# Fill in your values
cp .env.example .env

export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-central1
export GOOGLE_ADS_DEVELOPER_TOKEN=...
export GOOGLE_ADS_CLIENT_ID=...
export GOOGLE_ADS_CLIENT_SECRET=...
export GOOGLE_ADS_REFRESH_TOKEN=...
export GOOGLE_ADS_LOGIN_CUSTOMER_ID=...
export FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID=...
export FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET=...

./deploy/cloud-run.sh
```

The script prints your server URL when done, e.g. `https://google-ads-mcp-xxxx.run.app`.

### Step 2 — Connect Claude.ai

1. Open **claude.ai** on any device (web or mobile)
2. Go to **Settings → Integrations**
3. Click **Add MCP Server**
4. Enter your server URL: `https://google-ads-mcp-xxxx.run.app/mcp`
5. Authenticate with Google when prompted

That's it — the same server URL works on desktop browser and Claude mobile.

---

## Option 3: Claude Desktop pointing at a remote server

If you have a remote deployment and want to use it from Claude Desktop:

```json
{
  "mcpServers": {
    "google-ads": {
      "type": "http",
      "url": "https://google-ads-mcp-xxxx.run.app/mcp"
    }
  }
}
```

---

## Available Tools (69 total)

### Reporting & Insights
| Tool | What it does |
|------|-------------|
| `get_campaign_performance` | Impressions, clicks, cost, conversions, CTR by campaign |
| `get_keyword_performance` | Quality Score, bids, impression share per keyword |
| `get_search_terms_report` | Actual user queries that triggered your ads |
| `get_quality_score_report` | Quality Score breakdown (ad relevance, CTR, landing page) |
| `get_auction_insights` | Competitor overlap rates, impression share, outranking share |
| `get_ad_performance` | Ad strength, approval status, metrics per creative |
| `execute_gaql` | Run any custom Google Ads Query Language query |

### Campaign Management
| Tool | What it does |
|------|-------------|
| `create_campaign` | Create a new campaign with budget and bidding strategy |
| `update_campaign_status` | Enable, pause, or remove a campaign |
| `update_campaign_budget` | Adjust daily budget |
| `update_campaign_bidding_strategy` | Switch between Manual CPC, Target CPA, Target ROAS |
| `create_performance_max_campaign` | Create a full Performance Max campaign with asset groups |

### Ad Groups & Ads
| Tool | What it does |
|------|-------------|
| `create_ad_group` | Create an ad group within a campaign |
| `update_ad_group` | Rename or change ad group default bid |
| `remove_ad_group` | Remove an ad group |
| `create_responsive_search_ad` | Create RSA with up to 15 headlines + 4 descriptions |
| `replace_responsive_search_ad` | Update headlines/descriptions on an existing RSA |
| `update_ad_status` | Enable or pause individual ads |

### Keywords
| Tool | What it does |
|------|-------------|
| `add_keywords` | Add keywords to an ad group (broad, phrase, exact) |
| `add_negative_keywords` | Add negative keywords at ad group level |
| `add_campaign_negative_keywords` | Add negative keywords at campaign level |
| `update_keyword_bid` | Change max CPC bid for a keyword |
| `update_keyword_status` | Enable or pause keywords |
| `remove_ad_group_criteria` | Remove keywords or other ad group criteria |
| `create_shared_negative_list` | Create a shared negative keyword list |

### Assets & Extensions
| Tool | What it does |
|------|-------------|
| `add_sitelink_assets` | Add sitelink extensions |
| `add_callout_assets` | Add callout extensions |
| `add_structured_snippet_assets` | Add structured snippet extensions |
| `add_call_assets` | Add call extensions |
| `add_promotion_assets` | Add promotion extensions |
| `add_price_assets` | Add price extensions |
| `add_lead_form_asset` | Add lead form extensions |
| `add_image_asset` | Upload image assets |
| `list_assets` | List all assets in the account |
| `remove_assets` | Remove assets |

### Audiences
| Tool | What it does |
|------|-------------|
| `list_audiences` | List all user lists (audiences) in the account |
| `create_audience` | Create a rule-based website visitor audience |
| `apply_audience_to_ad_group` | Apply an audience to an ad group with a bid modifier |

### Labels
| Tool | What it does |
|------|-------------|
| `create_label` | Create a label for organizing campaigns/ad groups |
| `apply_labels` | Apply labels to campaigns, ad groups, or keywords |
| `list_labels` | List all labels in the account |

### Recommendations
| Tool | What it does |
|------|-------------|
| `list_recommendations` | Get Google's active optimization recommendations |
| `apply_recommendation` | Apply a specific recommendation |

### Conversions
| Tool | What it does |
|------|-------------|
| `create_conversion_action` | Create a new conversion tracking action |
| `list_conversion_actions` | List all conversion actions and their settings |
| `upload_click_conversions` | Upload offline click conversions from CRM using GCLIDs |
| `upload_call_conversions` | Upload offline call conversions from CRM using caller phone numbers |

### Customer Match
| Tool | What it does |
|------|-------------|
| `create_customer_match_list` | Create an empty Customer Match audience list for CRM-based targeting |
| `upload_customer_match_members` | Upload hashed emails/phones/addresses to a Customer Match list |
| `get_customer_match_job_status` | Check upload job status (PENDING/RUNNING/SUCCESS/FAILED) |

### Geographic Targeting
| Tool | What it does |
|------|-------------|
| `search_geo_targets` | Search for geographic targets by name (countries, cities, regions) |
| `add_location_targets` | Add location targeting (or exclusions) to a campaign |
| `list_campaign_locations` | List current location targets for a campaign |
| `remove_campaign_criteria` | Remove campaign-level targeting criteria by resource name |

### Demographic Targeting
| Tool | What it does |
|------|-------------|
| `set_age_range_bid_modifier` | Set bid modifier for an age range in an ad group |
| `set_gender_bid_modifier` | Set bid modifier for a gender in an ad group |
| `set_device_bid_modifier` | Set bid modifier for a device type at campaign level |
| `list_ad_group_demographics` | List current age/gender/device bid modifiers |

### Ad Scheduling
| Tool | What it does |
|------|-------------|
| `set_ad_schedule` | Set time-of-day/day-of-week bid modifiers for a campaign |
| `list_ad_schedules` | List current ad schedule bid adjustments for a campaign |

### Keyword Planner
| Tool | What it does |
|------|-------------|
| `generate_keyword_ideas` | Get keyword suggestions with search volume, competition, CPC estimates |
| `get_keyword_forecast` | Forecast clicks, impressions, and cost for a keyword set at a given budget |

### Shared Budgets
| Tool | What it does |
|------|-------------|
| `create_shared_budget` | Create a portfolio budget shared across multiple campaigns |
| `list_shared_budgets` | List all shared budgets and how many campaigns use each |
| `assign_campaign_budget` | Assign a shared budget to a campaign |

### Account
| Tool | What it does |
|------|-------------|
| `list_accessible_accounts` | List all Google Ads accounts accessible via your credentials |

### Documentation
| Tool | What it does |
|------|-------------|
| `get_gaql_doc` | Reference for Google Ads Query Language |
| `get_reporting_view_doc` | Schema for a specific GAQL reporting view |
| `get_reporting_fields_doc` | Available fields across all reporting views |

---

## Example Prompts

```
"List all my active campaigns and their monthly spend"

"Which keywords have a Quality Score below 5? What's the root cause?"

"Show me the search terms that are costing the most but not converting"

"Pause all keywords with more than 500 impressions and 0 conversions in the last 30 days"

"Create a new ad group called 'Brand' in campaign 123456 with exact match keywords [my brand] and [my brand reviews]"

"What does my competitor landscape look like? Who is beating me in the auction?"

"Apply all of Google's budget recommendations"

"Generate a Performance Max campaign for my e-commerce store with target ROAS of 400%"
```

---

## Credentials Reference

### Option A: YAML file (local development)

```yaml
# google-ads.yaml
developer_token: YOUR_DEVELOPER_TOKEN
client_id: YOUR_CLIENT_ID
client_secret: YOUR_CLIENT_SECRET
refresh_token: YOUR_REFRESH_TOKEN
login_customer_id: YOUR_MCC_ID  # optional but recommended
```

Set `GOOGLE_ADS_CREDENTIALS=/path/to/google-ads.yaml`.

### Option B: Environment variables (production / Cloud Run)

```bash
GOOGLE_ADS_DEVELOPER_TOKEN=...
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_LOGIN_CUSTOMER_ID=...  # optional
```

The server automatically detects which option to use.
To generate credentials: [google-ads-python authentication example](https://github.com/googleads/google-ads-python/blob/main/examples/authentication/generate_user_credentials.py)
