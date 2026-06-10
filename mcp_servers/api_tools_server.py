"""
MCP Server exposing REST API tools for QA testing.

APIs integrated:
  - JSONPlaceholder (https://jsonplaceholder.typicode.com) — No auth, CRUD demo
  - OpenWeatherMap  (https://openweathermap.org/api)       — API-key auth
  - GitHub REST API (https://api.github.com)               — Bearer-token auth
  - Generic REST caller                                    — Any endpoint

Run standalone:  python mcp_servers/api_tools_server.py
Transport:       stdio (consumed by Google ADK McpToolset)
"""

import json
import os
from typing import Optional

import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("qa-api-tools")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

JSONPLACEHOLDER = "https://jsonplaceholder.typicode.com"
WEATHER_BASE = "https://api.openweathermap.org/data/2.5"
GITHUB_BASE = "https://api.github.com"


def _json_response(data, status_code: int = 200) -> str:
    """Wrap an API response with metadata useful for QA."""
    return json.dumps(
        {"status_code": status_code, "data": data},
        indent=2,
        default=str,
    )


def _github_headers() -> dict:
    """Build GitHub request headers, optionally authenticated."""
    headers = {"Accept": "application/vnd.github+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


# ---------------------------------------------------------------------------
# JSONPlaceholder — Users
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_users() -> str:
    """List all users from the JSONPlaceholder API.
    Returns id, name, username, email, phone, website, address, and company
    for every user."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{JSONPLACEHOLDER}/users")
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def get_user(user_id: int) -> str:
    """Get a single user by ID (1-10) from JSONPlaceholder."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{JSONPLACEHOLDER}/users/{user_id}")
        return _json_response(r.json(), r.status_code)


# ---------------------------------------------------------------------------
# JSONPlaceholder — Posts
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_posts(user_id: Optional[int] = None) -> str:
    """List posts from JSONPlaceholder.  Optionally filter by user_id."""
    url = f"{JSONPLACEHOLDER}/posts"
    params = {}
    if user_id is not None:
        params["userId"] = user_id
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def get_post(post_id: int) -> str:
    """Get a single post by ID from JSONPlaceholder."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{JSONPLACEHOLDER}/posts/{post_id}")
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def create_post(title: str, body: str, user_id: int = 1) -> str:
    """Create a new post on JSONPlaceholder (simulated — returns the created object)."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{JSONPLACEHOLDER}/posts",
            json={"title": title, "body": body, "userId": user_id},
        )
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def update_post(post_id: int, title: str, body: str) -> str:
    """Update an existing post by ID on JSONPlaceholder (simulated)."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.put(
            f"{JSONPLACEHOLDER}/posts/{post_id}",
            json={"title": title, "body": body},
        )
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def delete_post(post_id: int) -> str:
    """Delete a post by ID on JSONPlaceholder (simulated)."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.delete(f"{JSONPLACEHOLDER}/posts/{post_id}")
        return _json_response({"deleted": True, "post_id": post_id}, r.status_code)


# ---------------------------------------------------------------------------
# JSONPlaceholder — Comments & Todos
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_comments(post_id: int) -> str:
    """Get all comments for a post from JSONPlaceholder."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{JSONPLACEHOLDER}/posts/{post_id}/comments")
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def list_todos(user_id: Optional[int] = None) -> str:
    """List todos from JSONPlaceholder. Optionally filter by user_id."""
    url = f"{JSONPLACEHOLDER}/todos"
    params = {}
    if user_id is not None:
        params["userId"] = user_id
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        return _json_response(r.json(), r.status_code)


# ---------------------------------------------------------------------------
# OpenWeatherMap — API-Key authentication
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_weather(city: str, units: str = "metric") -> str:
    """Get current weather for a city using the OpenWeatherMap API.
    Authenticates via the OPENWEATHERMAP_API_KEY environment variable.
    Args:
        city:  City name (e.g. 'London', 'New York', 'Tokyo')
        units: 'metric' (°C), 'imperial' (°F), or 'standard' (K)
    """
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return _json_response(
            {"error": "OPENWEATHERMAP_API_KEY is not configured. "
             "Set it in the .env file to use weather lookups."},
            401,
        )
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{WEATHER_BASE}/weather",
            params={"q": city, "appid": api_key, "units": units},
        )
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def get_weather_forecast(city: str, units: str = "metric") -> str:
    """Get a 5-day / 3-hour weather forecast for a city.
    Authenticates via the OPENWEATHERMAP_API_KEY environment variable.
    """
    api_key = os.getenv("OPENWEATHERMAP_API_KEY")
    if not api_key:
        return _json_response(
            {"error": "OPENWEATHERMAP_API_KEY is not configured."},
            401,
        )
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{WEATHER_BASE}/forecast",
            params={"q": city, "appid": api_key, "units": units},
        )
        return _json_response(r.json(), r.status_code)


# ---------------------------------------------------------------------------
# GitHub REST API — Bearer-token (OAuth) authentication
# ---------------------------------------------------------------------------


@mcp.tool()
async def search_github_repos(query: str, sort: str = "stars", per_page: int = 5) -> str:
    """Search GitHub repositories.  Authenticated with GITHUB_TOKEN if set.
    Args:
        query:    Search keywords (e.g. 'language:python machine-learning')
        sort:     Sort by 'stars', 'forks', 'updated', or 'help-wanted-issues'
        per_page: Number of results (max 30)
    """
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{GITHUB_BASE}/search/repositories",
            headers=_github_headers(),
            params={"q": query, "sort": sort, "per_page": min(per_page, 30)},
        )
        data = r.json()
        # Slim down the response for readability
        items = []
        for repo in data.get("items", []):
            items.append({
                "full_name": repo.get("full_name"),
                "description": repo.get("description"),
                "stars": repo.get("stargazers_count"),
                "forks": repo.get("forks_count"),
                "language": repo.get("language"),
                "url": repo.get("html_url"),
                "open_issues": repo.get("open_issues_count"),
            })
        return _json_response(
            {"total_count": data.get("total_count"), "items": items},
            r.status_code,
        )


@mcp.tool()
async def get_github_repo(owner: str, repo: str) -> str:
    """Get detailed information about a GitHub repository.
    Authenticated with GITHUB_TOKEN if set.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{GITHUB_BASE}/repos/{owner}/{repo}",
            headers=_github_headers(),
        )
        data = r.json()
        summary = {
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "language": data.get("language"),
            "open_issues": data.get("open_issues_count"),
            "license": (data.get("license") or {}).get("name"),
            "default_branch": data.get("default_branch"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "topics": data.get("topics"),
            "url": data.get("html_url"),
        }
        return _json_response(summary, r.status_code)


@mcp.tool()
async def list_github_issues(owner: str, repo: str, state: str = "open", per_page: int = 10) -> str:
    """List issues for a GitHub repository.
    Args:
        owner:    Repository owner
        repo:     Repository name
        state:    'open', 'closed', or 'all'
        per_page: Number of results (max 30)
    """
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(
            f"{GITHUB_BASE}/repos/{owner}/{repo}/issues",
            headers=_github_headers(),
            params={"state": state, "per_page": min(per_page, 30)},
        )
        data = r.json()
        issues = []
        for issue in data if isinstance(data, list) else []:
            issues.append({
                "number": issue.get("number"),
                "title": issue.get("title"),
                "state": issue.get("state"),
                "user": (issue.get("user") or {}).get("login"),
                "labels": [l.get("name") for l in issue.get("labels", [])],
                "created_at": issue.get("created_at"),
                "url": issue.get("html_url"),
            })
        return _json_response(issues, r.status_code)


# ---------------------------------------------------------------------------
# Generic REST API Caller
# ---------------------------------------------------------------------------


@mcp.tool()
async def call_rest_api(
    method: str,
    url: str,
    headers_json: str = "{}",
    query_params_json: str = "{}",
    body_json: str = "{}",
    auth_type: str = "none",
    auth_value: str = "",
) -> str:
    """Call any REST API endpoint (generic tool).

    Args:
        method:           HTTP method — GET, POST, PUT, PATCH, DELETE
        url:              Full URL of the API endpoint
        headers_json:     JSON string of extra headers, e.g. '{"X-Custom": "val"}'
        query_params_json:JSON string of query parameters
        body_json:        JSON string of request body (ignored for GET/DELETE)
        auth_type:        'none', 'api_key', 'bearer', or 'basic'
        auth_value:       The key/token/base64 value for the chosen auth_type
    """
    method = method.upper()
    try:
        headers = json.loads(headers_json) if headers_json else {}
        params = json.loads(query_params_json) if query_params_json else {}
        body = json.loads(body_json) if body_json else {}
    except json.JSONDecodeError as e:
        return _json_response({"error": f"Invalid JSON input: {e}"}, 400)

    # Apply authentication
    if auth_type == "bearer" and auth_value:
        headers["Authorization"] = f"Bearer {auth_value}"
    elif auth_type == "api_key" and auth_value:
        params["api_key"] = auth_value
    elif auth_type == "basic" and auth_value:
        headers["Authorization"] = f"Basic {auth_value}"

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            kwargs = {"headers": headers, "params": params}
            if method in ("POST", "PUT", "PATCH"):
                kwargs["json"] = body

            r = await client.request(method, url, **kwargs)

            # Try to parse as JSON; fall back to raw text
            try:
                resp_data = r.json()
            except Exception:
                resp_data = r.text

            return _json_response(resp_data, r.status_code)
        except httpx.RequestError as e:
            return _json_response({"error": str(e)}, 500)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
