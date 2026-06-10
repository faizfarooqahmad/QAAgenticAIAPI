# QA Agentic AI API

An **Agentic AI** project built with **Google ADK** (Agent Development Kit) and **MCP** (Model Context Protocol) that enables QA teams to test REST APIs through natural language chat.

## Architecture

```
┌────────────────────────────────────────────────┐
│              QA Team (Chat UI)                 │
│         Web UI  /  CLI  /  ADK Web             │
└──────────────────┬─────────────────────────────┘
                   │
┌──────────────────▼─────────────────────────────┐
│          qa_orchestrator (Root Agent)           │
│          Google ADK · Gemini 2.0 Flash         │
│                                                │
│  ┌──────────────┐    ┌──────────────────────┐  │
│  │  api_tester  │    │  response_analyzer   │  │
│  │  (Sub-Agent) │    │    (Sub-Agent)       │  │
│  └──────┬───────┘    └──────────────────────┘  │
│         │                                      │
└─────────┼──────────────────────────────────────┘
          │  MCP (stdio)
┌─────────▼──────────────────────────────────────┐
│          MCP Server (api_tools_server)          │
│                                                │
│  JSONPlaceholder  │  OpenWeatherMap  │  GitHub  │
│  (No Auth)        │  (API Key)       │ (OAuth)  │
│                                                │
│         + Generic REST API Caller              │
└────────────────────────────────────────────────┘
```

## Features

- **Natural language API testing** — Ask in plain English, the agent builds and executes the request
- **Multi-API support** — JSONPlaceholder (CRUD), OpenWeatherMap (weather), GitHub (repos/issues)
- **Authentication** — API Key, Bearer/OAuth Token, and Basic Auth support
- **Generic REST caller** — Test *any* REST endpoint via the `call_rest_api` tool
- **Response analysis** — Validate schemas, compare responses, get QA summaries
- **Multiple interfaces** — CLI, Web Chat UI, ADK Web, or REST API

## Quick Start

### 1. Install dependencies

```bash
cd QAAgenticAIAPI
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your keys:
#   GOOGLE_API_KEY          — Required (Gemini API)
#   OPENWEATHERMAP_API_KEY  — Optional (weather tools)
#   GITHUB_TOKEN            — Optional (higher GitHub rate limits)
```

Get your **Google API Key** at: https://aistudio.google.com/apikey

### 3. Run

**Option A — Web Chat UI** (recommended for QA teams):
```bash
python web_app.py
# Open http://localhost:8000
```

**Option B — CLI Chat**:
```bash
python main.py
```

**Option C — ADK Built-in Web UI**:
```bash
adk web qa_agent
```

**Option D — Single Prompt**:
```bash
python main.py --once "List all users from JSONPlaceholder"
```

## Example Prompts

| Prompt | What Happens |
|--------|-------------|
| *"List all users from JSONPlaceholder"* | Calls `list_users` → returns 10 users |
| *"Get posts by user 3"* | Calls `list_posts(user_id=3)` |
| *"Create a post titled 'Bug Report' with body 'Login fails'"* | Calls `create_post(...)` |
| *"What's the weather in London?"* | Calls `get_weather(city='London')` with API key auth |
| *"Search GitHub for Python testing frameworks"* | Calls `search_github_repos(...)` with token auth |
| *"GET https://api.example.com/health with Bearer token xyz"* | Calls `call_rest_api(...)` with bearer auth |
| *"Analyse the last response — are there any missing fields?"* | Routes to `response_analyzer` agent |

## Project Structure

```
QAAgenticAIAPI/
├── README.md
├── requirements.txt
├── .env.example
├── .env                          # Your API keys (git-ignored)
├── mcp_servers/
│   ├── __init__.py
│   └── api_tools_server.py       # MCP server — all API tools
├── qa_agent/
│   ├── __init__.py
│   └── agent.py                  # ADK agents (orchestrator + sub-agents)
├── main.py                       # CLI runner
└── web_app.py                    # FastAPI web chat UI
```

## MCP Tools Reference

### JSONPlaceholder (No Auth)
| Tool | Description |
|------|-------------|
| `list_users` | GET all users |
| `get_user` | GET user by ID |
| `list_posts` | GET posts (optionally by user) |
| `get_post` | GET post by ID |
| `create_post` | POST new post |
| `update_post` | PUT update post |
| `delete_post` | DELETE post |
| `get_comments` | GET comments for a post |
| `list_todos` | GET todos (optionally by user) |

### OpenWeatherMap (API Key Auth)
| Tool | Description |
|------|-------------|
| `get_weather` | Current weather for a city |
| `get_weather_forecast` | 5-day forecast for a city |

### GitHub (Bearer Token Auth)
| Tool | Description |
|------|-------------|
| `search_github_repos` | Search repositories |
| `get_github_repo` | Get repo details |
| `list_github_issues` | List issues for a repo |

### Generic
| Tool | Description |
|------|-------------|
| `call_rest_api` | Call any REST endpoint with custom method, headers, params, body, and auth |

## Authentication

The agent supports three authentication methods:

1. **API Key** — Passed as query parameter (e.g., OpenWeatherMap)
2. **Bearer / OAuth Token** — Passed in `Authorization: Bearer <token>` header (e.g., GitHub)
3. **Basic Auth** — Base64-encoded `user:password` in `Authorization: Basic <value>` header

For the generic `call_rest_api` tool, set `auth_type` and `auth_value` accordingly.

## Tech Stack

- **Google ADK** — Agent orchestration framework
- **MCP** (Model Context Protocol) — Tool interface between agents and APIs
- **Gemini 2.0 Flash** — LLM powering the agents
- **FastAPI + WebSocket** — Web chat interface
- **httpx** — Async HTTP client for API calls
