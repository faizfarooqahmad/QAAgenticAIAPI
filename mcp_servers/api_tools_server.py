"""
MCP Server exposing REST API tools for QA testing.

APIs integrated:
  - JSONPlaceholder (https://jsonplaceholder.typicode.com) — No auth, CRUD demo
  - Generic REST caller                                    — Any endpoint

Run standalone:  python mcp_servers/api_tools_server.py
Transport:       stdio (consumed by Google ADK McpToolset)
"""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Logging setup — logs all API requests and responses to logs/api_calls.log
# ---------------------------------------------------------------------------

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "api_calls.log"

logger = logging.getLogger("api_calls")
logger.setLevel(logging.INFO)

_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_file_handler.setFormatter(
    logging.Formatter("%(message)s")
)
logger.addHandler(_file_handler)

# Also log to stderr for real-time visibility
_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(
    logging.Formatter("[%(levelname)s] %(message)s")
)
logger.addHandler(_stream_handler)


def _log_request(tool_name: str, method: str, url: str, **kwargs) -> None:
    """Log an outgoing API request."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "direction": "REQUEST",
        "tool": tool_name,
        "method": method,
        "url": url,
    }
    if kwargs.get("params"):
        entry["query_params"] = kwargs["params"]
    if kwargs.get("body"):
        entry["body"] = kwargs["body"]
    if kwargs.get("headers"):
        entry["headers"] = kwargs["headers"]
    logger.info(json.dumps(entry, default=str))


def _log_response(tool_name: str, status_code: int, body) -> None:
    """Log an incoming API response."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "direction": "RESPONSE",
        "tool": tool_name,
        "status_code": status_code,
        "body": body,
    }
    logger.info(json.dumps(entry, default=str))


mcp = FastMCP("qa-api-tools")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

JSONPLACEHOLDER = "https://jsonplaceholder.typicode.com"


def _json_response(data, status_code: int = 200) -> str:
    """Wrap an API response with metadata useful for QA."""
    return json.dumps(
        {"status_code": status_code, "data": data},
        indent=2,
        default=str,
    )


# ---------------------------------------------------------------------------
# JSONPlaceholder — Users
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_users() -> str:
    """List all users from the JSONPlaceholder API.
    Returns id, name, username, email, phone, website, address, and company
    for every user."""
    url = f"{JSONPLACEHOLDER}/users"
    _log_request("list_users", "GET", url)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        _log_response("list_users", r.status_code, r.json())
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def get_user(user_id: int) -> str:
    """Get a single user by ID (1-10) from JSONPlaceholder."""
    url = f"{JSONPLACEHOLDER}/users/{user_id}"
    _log_request("get_user", "GET", url, params={"user_id": user_id})
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        _log_response("get_user", r.status_code, r.json())
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
    _log_request("list_posts", "GET", url, params=params)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        _log_response("list_posts", r.status_code, r.json())
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def get_post(post_id: int) -> str:
    """Get a single post by ID from JSONPlaceholder."""
    url = f"{JSONPLACEHOLDER}/posts/{post_id}"
    _log_request("get_post", "GET", url, params={"post_id": post_id})
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        _log_response("get_post", r.status_code, r.json())
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def create_post(title: str, body: str, user_id: int = 1) -> str:
    """Create a new post on JSONPlaceholder (simulated — returns the created object)."""
    url = f"{JSONPLACEHOLDER}/posts"
    request_body = {"title": title, "body": body, "userId": user_id}
    _log_request("create_post", "POST", url, body=request_body)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json=request_body)
        _log_response("create_post", r.status_code, r.json())
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def update_post(post_id: int, title: str, body: str) -> str:
    """Update an existing post by ID on JSONPlaceholder (simulated)."""
    url = f"{JSONPLACEHOLDER}/posts/{post_id}"
    request_body = {"title": title, "body": body}
    _log_request("update_post", "PUT", url, body=request_body)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.put(url, json=request_body)
        _log_response("update_post", r.status_code, r.json())
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def delete_post(post_id: int) -> str:
    """Delete a post by ID on JSONPlaceholder (simulated)."""
    url = f"{JSONPLACEHOLDER}/posts/{post_id}"
    _log_request("delete_post", "DELETE", url, params={"post_id": post_id})
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.delete(url)
        _log_response("delete_post", r.status_code, {"deleted": True, "post_id": post_id})
        return _json_response({"deleted": True, "post_id": post_id}, r.status_code)


# ---------------------------------------------------------------------------
# JSONPlaceholder — Comments & Todos
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_comments(post_id: int) -> str:
    """Get all comments for a post from JSONPlaceholder."""
    url = f"{JSONPLACEHOLDER}/posts/{post_id}/comments"
    _log_request("get_comments", "GET", url, params={"post_id": post_id})
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        _log_response("get_comments", r.status_code, r.json())
        return _json_response(r.json(), r.status_code)


@mcp.tool()
async def list_todos(user_id: Optional[int] = None) -> str:
    """List todos from JSONPlaceholder. Optionally filter by user_id."""
    url = f"{JSONPLACEHOLDER}/todos"
    params = {}
    if user_id is not None:
        params["userId"] = user_id
    _log_request("list_todos", "GET", url, params=params)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        _log_response("list_todos", r.status_code, r.json())
        return _json_response(r.json(), r.status_code)



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

    _log_request("call_rest_api", method, url, headers=headers, params=params, body=body if method in ("POST", "PUT", "PATCH") else None)

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

            _log_response("call_rest_api", r.status_code, resp_data)
            return _json_response(resp_data, r.status_code)
        except httpx.RequestError as e:
            _log_response("call_rest_api", 500, {"error": str(e)})
            return _json_response({"error": str(e)}, 500)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
