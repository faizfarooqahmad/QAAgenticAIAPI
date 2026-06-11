"""OpenAPI spec loader and request validator.

Loads the JSONPlaceholder OpenAPI spec and provides helpers to:
  - Look up endpoint definitions by operationId
  - Validate request parameters against the spec
  - Build request metadata (method, url, expected schema) from the spec
"""

import yaml
from pathlib import Path
from typing import Optional

SPECS_DIR = Path(__file__).resolve().parent
OPENAPI_FILE = SPECS_DIR / "jsonplaceholder_openapi.yaml"

_spec_cache: Optional[dict] = None


def load_spec() -> dict:
    """Load and cache the OpenAPI spec."""
    global _spec_cache
    if _spec_cache is None:
        with open(OPENAPI_FILE, "r", encoding="utf-8") as f:
            _spec_cache = yaml.safe_load(f)
    return _spec_cache


def get_base_url() -> str:
    """Get the base URL from the spec's servers list."""
    spec = load_spec()
    servers = spec.get("servers", [])
    return servers[0]["url"] if servers else ""


def get_operation(operation_id: str) -> Optional[dict]:
    """Look up an operation by its operationId.

    Returns a dict with: method, path, parameters, requestBody, responses,
    summary, description — or None if not found.
    """
    spec = load_spec()
    for path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            if isinstance(op, dict) and op.get("operationId") == operation_id:
                return {
                    "operationId": operation_id,
                    "method": method.upper(),
                    "path": path,
                    "summary": op.get("summary", ""),
                    "description": op.get("description", ""),
                    "parameters": op.get("parameters", []),
                    "requestBody": op.get("requestBody"),
                    "responses": op.get("responses", {}),
                }
    return None


def resolve_ref(ref: str) -> dict:
    """Resolve a $ref pointer like '#/components/schemas/User'."""
    spec = load_spec()
    parts = ref.lstrip("#/").split("/")
    node = spec
    for part in parts:
        node = node.get(part, {})
    return node


def resolve_parameter(param: dict) -> dict:
    """Resolve a parameter that may be a $ref."""
    if "$ref" in param:
        return resolve_ref(param["$ref"])
    return param


def get_request_schema(operation_id: str) -> Optional[dict]:
    """Get the request body JSON schema for an operation (if any)."""
    op = get_operation(operation_id)
    if not op or not op.get("requestBody"):
        return None
    content = op["requestBody"].get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})
    if "$ref" in schema:
        return resolve_ref(schema["$ref"])
    return schema


def get_response_schema(operation_id: str, status: str = "200") -> Optional[dict]:
    """Get the response JSON schema for an operation and status code."""
    op = get_operation(operation_id)
    if not op:
        return None
    resp = op.get("responses", {}).get(status)
    if not resp:
        return None
    content = resp.get("content", {})
    json_content = content.get("application/json", {})
    schema = json_content.get("schema", {})
    if "$ref" in schema:
        return resolve_ref(schema["$ref"])
    # Resolve items ref for arrays
    if schema.get("type") == "array" and "$ref" in schema.get("items", {}):
        schema = dict(schema)
        schema["items"] = resolve_ref(schema["items"]["$ref"])
    return schema


def validate_params(operation_id: str, **kwargs) -> list[str]:
    """Validate parameters against the spec. Returns a list of errors (empty = valid)."""
    op = get_operation(operation_id)
    if not op:
        return [f"Unknown operation: {operation_id}"]

    errors = []

    # Check required path/query parameters
    for param_def in op.get("parameters", []):
        param = resolve_parameter(param_def)
        name = param.get("name", "")
        required = param.get("required", False)
        if required and name not in kwargs:
            errors.append(f"Missing required parameter: {name}")

    # Check required request body fields
    req_schema = get_request_schema(operation_id)
    if req_schema:
        required_fields = req_schema.get("required", [])
        for field in required_fields:
            if field not in kwargs:
                errors.append(f"Missing required body field: {field}")

    return errors


def build_request_info(operation_id: str) -> Optional[dict]:
    """Build a human-readable request info dict for an operation.

    Returns: {operationId, method, url_template, required_params,
              optional_params, request_body_schema, response_schema}
    """
    op = get_operation(operation_id)
    if not op:
        return None

    base_url = get_base_url()
    url_template = base_url + op["path"]

    required_params = []
    optional_params = []
    for param_def in op.get("parameters", []):
        param = resolve_parameter(param_def)
        info = {
            "name": param.get("name"),
            "in": param.get("in"),
            "type": param.get("schema", {}).get("type", "string"),
            "description": param.get("description", ""),
        }
        if param.get("required"):
            required_params.append(info)
        else:
            optional_params.append(info)

    req_schema = get_request_schema(operation_id)
    if req_schema:
        for field in req_schema.get("required", []):
            props = req_schema.get("properties", {}).get(field, {})
            required_params.append({
                "name": field,
                "in": "body",
                "type": props.get("type", "string"),
                "description": props.get("description", ""),
            })
        for field, props in req_schema.get("properties", {}).items():
            if field not in req_schema.get("required", []):
                optional_params.append({
                    "name": field,
                    "in": "body",
                    "type": props.get("type", "string"),
                    "description": props.get("description", ""),
                    "default": props.get("default"),
                })

    resp_schema = get_response_schema(
        operation_id,
        "201" if op["method"] == "POST" else "200",
    )

    return {
        "operationId": operation_id,
        "method": op["method"],
        "url_template": url_template,
        "summary": op["summary"],
        "description": op["description"],
        "required_params": required_params,
        "optional_params": optional_params,
        "request_body_schema": req_schema,
        "response_schema": resp_schema,
    }


def list_operations() -> list[dict]:
    """List all operations in the spec with basic info."""
    spec = load_spec()
    ops = []
    for path, methods in spec.get("paths", {}).items():
        for method, op in methods.items():
            if isinstance(op, dict) and "operationId" in op:
                ops.append({
                    "operationId": op["operationId"],
                    "method": method.upper(),
                    "path": path,
                    "summary": op.get("summary", ""),
                })
    return ops


def build_url(operation_id: str, **path_params) -> Optional[str]:
    """Build the full URL for an operation, substituting path parameters.

    Example:
        build_url("get_user", user_id=3)
        → "https://jsonplaceholder.typicode.com/users/3"
    """
    op = get_operation(operation_id)
    if not op:
        return None
    base = get_base_url()
    path = op["path"]
    for param_def in op.get("parameters", []):
        param = resolve_parameter(param_def)
        if param.get("in") == "path":
            name = param["name"]
            if name in path_params:
                path = path.replace(f"{{{name}}}", str(path_params[name]))
    return base + path


def build_query_params(operation_id: str, **kwargs) -> dict:
    """Build query parameters dict for an operation from kwargs.

    Only includes parameters that the spec defines as 'in: query'.
    """
    op = get_operation(operation_id)
    if not op:
        return {}
    query_params = {}
    for param_def in op.get("parameters", []):
        param = resolve_parameter(param_def)
        if param.get("in") == "query":
            name = param["name"]
            if name in kwargs and kwargs[name] is not None:
                query_params[name] = kwargs[name]
    return query_params


def build_request_body(operation_id: str, **kwargs) -> Optional[dict]:
    """Build a request body dict for an operation based on its OpenAPI schema.

    Reads the requestBody schema, picks matching fields from kwargs,
    applies defaults from the spec for missing optional fields, and
    returns the body dict. Returns None if the operation has no request body.

    Example:
        build_request_body("create_post", title="Hi", body="Hello", user_id=2)
        → {"title": "Hi", "body": "Hello", "userId": 2}
    """
    schema = get_request_schema(operation_id)
    if not schema:
        return None

    properties = schema.get("properties", {})
    required_fields = set(schema.get("required", []))
    body = {}

    for field_name, field_schema in properties.items():
        # Try exact match first, then snake_case variant
        snake_name = _to_snake_case(field_name)
        if field_name in kwargs:
            body[field_name] = kwargs[field_name]
        elif snake_name in kwargs:
            body[field_name] = kwargs[snake_name]
        elif "default" in field_schema:
            body[field_name] = field_schema["default"]
        # If required and still not set, leave it out — validation will catch it

    return body


def _to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case. e.g. userId → user_id"""
    import re as _re
    s1 = _re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    return _re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s1).lower()
