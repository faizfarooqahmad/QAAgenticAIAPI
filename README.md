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
│  JSONPlaceholder (No Auth, CRUD)               │
│  + Generic REST API Caller (Any Auth)          │
└────────────────────────────────────────────────┘
```

## Features

- **Natural language API testing** — Ask in plain English, the agent builds and executes the request
- **JSONPlaceholder CRUD** — Full Create, Read, Update, Delete operations on users, posts, comments, todos
- **Generic REST caller** — Test *any* REST endpoint via the `call_rest_api` tool
- **Authentication** — API Key, Bearer/OAuth Token, and Basic Auth support
- **Request/Response logging** — All API calls logged to `logs/api_calls.log`
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
# Edit .env and add your key:
#   GOOGLE_API_KEY — Required (Gemini API)
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

## Sample Prompts

### JSONPlaceholder API

#### list_users
```
List all users from JSONPlaceholder
```
```
Show me all the users available in the system
```

#### get_user
```
Get user with ID 3
```
```
Fetch details of user number 5 from JSONPlaceholder
```

#### list_posts
```
List all posts from JSONPlaceholder
```
```
Show me all posts written by user 2
```

#### get_post
```
Get post number 7
```
```
Fetch the post with ID 15 from JSONPlaceholder
```

#### create_post
```
Create a new post with title "Login Bug" and body "Login page returns 500 error on submit"
```
```
Create a post titled "Test Results" with body "All regression tests passed" for user 3
```

#### update_post
```
Update post 1 with new title "Updated Title" and body "This is the corrected content"
```
```
Change post 5 title to "Fixed Issue" and body to "The bug has been resolved"
```

#### delete_post
```
Delete post number 10
```
```
Remove post with ID 3 from JSONPlaceholder
```

#### get_comments
```
Get all comments on post 1
```
```
Show me the comments for post number 12
```

#### list_todos
```
List all todos from JSONPlaceholder
```
```
Show me todos for user 5
```

---

### Generic REST API Caller

#### GET request (no auth)
```
Call GET on https://httpbin.org/get
```
```
Make a GET request to https://jsonplaceholder.typicode.com/albums
```

#### GET request with query parameters
```
Call GET on https://httpbin.org/get with query params {"page": "1", "limit": "10"}
```

#### POST request with JSON body
```
Call POST on https://httpbin.org/post with body {"username": "testuser", "email": "test@example.com"}
```
```
Make a POST request to https://reqres.in/api/users with body {"name": "John", "job": "QA Engineer"}
```

#### PUT request
```
Call PUT on https://reqres.in/api/users/2 with body {"name": "Jane", "job": "Senior QA"}
```

#### PATCH request
```
Call PATCH on https://reqres.in/api/users/2 with body {"job": "Lead QA"}
```

#### DELETE request
```
Call DELETE on https://reqres.in/api/users/2
```

#### With Bearer Token (OAuth) authentication
```
Call GET on https://api.example.com/users with bearer token "eyJhbGciOiJIUzI1NiIsInR5..."
```
```
Make a POST to https://api.example.com/orders with bearer auth token "my-oauth-token" and body {"item": "widget", "qty": 5}
```

#### With API Key authentication
```
Call GET on https://api.example.com/data with API key "abc123xyz"
```

#### With Basic Auth
```
Call GET on https://httpbin.org/basic-auth/user/pass with basic auth "dXNlcjpwYXNz"
```

#### With custom headers
```
Call GET on https://httpbin.org/headers with headers {"X-Custom-Header": "QA-Test", "Accept": "application/json"}
```

---

### Response Analysis
```
Analyse the last response — are there any missing fields?
```
```
Compare the response of get user 1 and get user 2 — what are the differences?
```
```
Validate the response schema — does every user have an email and phone field?
```

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

### Generic REST API Caller
| Tool | Description |
|------|-------------|
| `call_rest_api` | Call any REST endpoint with custom method, headers, params, body, and auth |

## Authentication

The generic `call_rest_api` tool supports three authentication methods:

1. **API Key** (`auth_type='api_key'`) — Adds `?api_key=<value>` as query parameter
2. **Bearer / OAuth Token** (`auth_type='bearer'`) — Adds `Authorization: Bearer <value>` header
3. **Basic Auth** (`auth_type='basic'`) — Adds `Authorization: Basic <value>` header (Base64-encoded `user:password`)

## Logging

All API requests and responses are automatically logged to `logs/api_calls.log` in JSON format:

```json
{"timestamp": "2026-06-11T03:40:00+00:00", "direction": "REQUEST", "tool": "get_user", "method": "GET", "url": "https://jsonplaceholder.typicode.com/users/1", "query_params": {"user_id": 1}}
{"timestamp": "2026-06-11T03:40:01+00:00", "direction": "RESPONSE", "tool": "get_user", "status_code": 200, "body": {"id": 1, "name": "Leanne Graham", ...}}
```

## Tech Stack

- **Google ADK** — Agent orchestration framework
- **MCP** (Model Context Protocol) — Tool interface between agents and APIs
- **Gemini 2.0 Flash** — LLM powering the agents
- **FastAPI + WebSocket** — Web chat interface
- **httpx** — Async HTTP client for API calls
