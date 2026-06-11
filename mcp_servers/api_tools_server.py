"""
MCP Server exposing REST API tools for QA testing.

APIs integrated:
  - JSONPlaceholder (https://jsonplaceholder.typicode.com) — No auth, CRUD demo
    Endpoints defined in: specs/jsonplaceholder_openapi.yaml
  - Generic REST caller                                    — Any endpoint

Run standalone:  python mcp_servers/api_tools_server.py
Transport:       stdio (consumed by Google ADK McpToolset)
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from mcp.server.fastmcp import FastMCP

# Add project root to path so specs module is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from specs import (
    get_base_url,
    validate_params,
    build_request_info,
    list_operations,
    build_url,
    build_query_params,
    build_request_body,
)

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


def _json_response(data, status_code: int = 200, operation_id: str = "") -> str:
    """Wrap an API response with metadata useful for QA."""
    result = {"status_code": status_code, "data": data}
    if operation_id:
        result["openapi_operation"] = operation_id
    return json.dumps(result, indent=2, default=str)


def _validate_and_log(operation_id: str, **params) -> list[str]:
    """Validate params against the OpenAPI spec and return any errors."""
    errors = validate_params(operation_id, **params)
    if errors:
        logger.warning(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "direction": "VALIDATION_ERROR",
            "operation": operation_id,
            "errors": errors,
            "params": params,
        }, default=str))
    return errors


# ---------------------------------------------------------------------------
# JSONPlaceholder — Users
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_users() -> str:
    """List all users from the JSONPlaceholder API.
    Returns id, name, username, email, phone, website, address, and company
    for every user.

    OpenAPI operationId: list_users
    Spec: specs/jsonplaceholder_openapi.yaml"""
    url = build_url("list_users")
    _log_request("list_users", "GET", url)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        _log_response("list_users", r.status_code, r.json())
        return _json_response(r.json(), r.status_code, operation_id="list_users")


@mcp.tool()
async def get_user(user_id: int) -> str:
    """Get a single user by ID (1-10) from JSONPlaceholder.

    OpenAPI operationId: get_user
    Spec: specs/jsonplaceholder_openapi.yaml"""
    errors = _validate_and_log("get_user", user_id=user_id)
    if errors:
        return _json_response({"validation_errors": errors}, 400, operation_id="get_user")
    url = build_url("get_user", user_id=user_id)
    _log_request("get_user", "GET", url, params={"user_id": user_id})
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        _log_response("get_user", r.status_code, r.json())
        return _json_response(r.json(), r.status_code, operation_id="get_user")


# ---------------------------------------------------------------------------
# JSONPlaceholder — Posts
# ---------------------------------------------------------------------------


@mcp.tool()
async def list_posts(user_id: Optional[int] = None) -> str:
    """List posts from JSONPlaceholder.  Optionally filter by user_id.

    OpenAPI operationId: list_posts
    Spec: specs/jsonplaceholder_openapi.yaml"""
    url = build_url("list_posts")
    params = build_query_params("list_posts", userId=user_id)
    _log_request("list_posts", "GET", url, params=params)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        _log_response("list_posts", r.status_code, r.json())
        return _json_response(r.json(), r.status_code, operation_id="list_posts")


@mcp.tool()
async def get_post(post_id: int) -> str:
    """Get a single post by ID from JSONPlaceholder.

    OpenAPI operationId: get_post
    Spec: specs/jsonplaceholder_openapi.yaml"""
    errors = _validate_and_log("get_post", post_id=post_id)
    if errors:
        return _json_response({"validation_errors": errors}, 400, operation_id="get_post")
    url = build_url("get_post", post_id=post_id)
    _log_request("get_post", "GET", url, params={"post_id": post_id})
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        _log_response("get_post", r.status_code, r.json())
        return _json_response(r.json(), r.status_code, operation_id="get_post")


@mcp.tool()
async def create_post(title: str, body: str, user_id: int = 1) -> str:
    """Create a new post on JSONPlaceholder (simulated — returns the created object).

    OpenAPI operationId: create_post
    Spec: specs/jsonplaceholder_openapi.yaml"""
    errors = _validate_and_log("create_post", title=title, body=body, userId=user_id)
    if errors:
        return _json_response({"validation_errors": errors}, 400, operation_id="create_post")
    url = build_url("create_post")
    request_body = build_request_body("create_post", title=title, body=body, user_id=user_id)
    _log_request("create_post", "POST", url, body=request_body)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, json=request_body)
        _log_response("create_post", r.status_code, r.json())
        return _json_response(r.json(), r.status_code, operation_id="create_post")


@mcp.tool()
async def update_post(post_id: int, title: str, body: str) -> str:
    """Update an existing post by ID on JSONPlaceholder (simulated).

    OpenAPI operationId: update_post
    Spec: specs/jsonplaceholder_openapi.yaml"""
    errors = _validate_and_log("update_post", post_id=post_id, title=title, body=body)
    if errors:
        return _json_response({"validation_errors": errors}, 400, operation_id="update_post")
    url = build_url("update_post", post_id=post_id)
    request_body = build_request_body("update_post", title=title, body=body)
    _log_request("update_post", "PUT", url, body=request_body)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.put(url, json=request_body)
        _log_response("update_post", r.status_code, r.json())
        return _json_response(r.json(), r.status_code, operation_id="update_post")


@mcp.tool()
async def delete_post(post_id: int) -> str:
    """Delete a post by ID on JSONPlaceholder (simulated).

    OpenAPI operationId: delete_post
    Spec: specs/jsonplaceholder_openapi.yaml"""
    errors = _validate_and_log("delete_post", post_id=post_id)
    if errors:
        return _json_response({"validation_errors": errors}, 400, operation_id="delete_post")
    url = build_url("delete_post", post_id=post_id)
    _log_request("delete_post", "DELETE", url, params={"post_id": post_id})
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.delete(url)
        _log_response("delete_post", r.status_code, {"deleted": True, "post_id": post_id})
        return _json_response({"deleted": True, "post_id": post_id}, r.status_code, operation_id="delete_post")


# ---------------------------------------------------------------------------
# JSONPlaceholder — Comments & Todos
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_comments(post_id: int) -> str:
    """Get all comments for a post from JSONPlaceholder.

    OpenAPI operationId: get_comments
    Spec: specs/jsonplaceholder_openapi.yaml"""
    errors = _validate_and_log("get_comments", post_id=post_id)
    if errors:
        return _json_response({"validation_errors": errors}, 400, operation_id="get_comments")
    url = build_url("get_comments", post_id=post_id)
    _log_request("get_comments", "GET", url, params={"post_id": post_id})
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url)
        _log_response("get_comments", r.status_code, r.json())
        return _json_response(r.json(), r.status_code, operation_id="get_comments")


@mcp.tool()
async def list_todos(user_id: Optional[int] = None) -> str:
    """List todos from JSONPlaceholder. Optionally filter by user_id.

    OpenAPI operationId: list_todos
    Spec: specs/jsonplaceholder_openapi.yaml"""
    url = build_url("list_todos")
    params = build_query_params("list_todos", userId=user_id)
    _log_request("list_todos", "GET", url, params=params)
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(url, params=params)
        _log_response("list_todos", r.status_code, r.json())
        return _json_response(r.json(), r.status_code, operation_id="list_todos")



# ---------------------------------------------------------------------------
# OpenAPI Spec Lookup Tool
# ---------------------------------------------------------------------------


@mcp.tool()
async def get_api_spec(operation_id: str = "") -> str:
    """Look up the OpenAPI spec for JSONPlaceholder endpoints.

    If operation_id is provided, returns the full spec for that operation
    (method, URL, required/optional params, request body schema, response schema).
    If empty, returns a summary of all available operations.

    Args:
        operation_id: The operationId to look up (e.g. 'get_user', 'create_post').
                      Leave empty to list all operations.
    """
    if operation_id:
        info = build_request_info(operation_id)
        if not info:
            return _json_response({"error": f"Unknown operationId: {operation_id}"}, 404)
        return json.dumps(info, indent=2, default=str)
    else:
        ops = list_operations()
        return json.dumps({"operations": ops, "base_url": get_base_url()}, indent=2)


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
