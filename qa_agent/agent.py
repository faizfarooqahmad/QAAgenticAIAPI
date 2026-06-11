"""
Google ADK Agent definition for the QA API Testing Assistant.

Architecture:
  root_agent (Orchestrator)
    ├── api_tester_agent   — Executes API calls via MCP tools
    └── analyzer_agent     — Analyses responses, compares, validates

The MCP server (mcp_servers/api_tools_server.py) is launched via stdio
and exposes tools for JSONPlaceholder and a generic REST caller.

Agent capabilities are loaded from: skills/api_skills.yaml

Export: root_agent  (consumed by `adk web` / `adk run`)
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StdioServerParameters

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MCP_SERVER_SCRIPT = str(PROJECT_ROOT / "mcp_servers" / "api_tools_server.py")

# Add project root to path so skills module is importable
sys.path.insert(0, str(PROJECT_ROOT))
from skills import build_capabilities_text

# ---------------------------------------------------------------------------
# Load capabilities from skills config
# ---------------------------------------------------------------------------

CAPABILITIES_TEXT = build_capabilities_text()

# ---------------------------------------------------------------------------
# MCP Toolset — connects to the API tools server over stdio
# ---------------------------------------------------------------------------

api_mcp_toolset = McpToolset(
    connection_params=StdioServerParameters(
        command=sys.executable,
        args=[MCP_SERVER_SCRIPT],
        env={**os.environ},
    )
)

# ---------------------------------------------------------------------------
# Sub-agent: API Tester
# ---------------------------------------------------------------------------

api_tester_agent = LlmAgent(
    name="api_tester",
    model="gemini-2.0-flash",
    description=(
        "Executes API requests via MCP tools. Use this agent when the user "
        "wants to call an API, fetch data, create/update/delete resources, "
        "or test an endpoint."
    ),
    instruction="""You are an expert API tester. Your job is to:

1. **Understand** the user's request and determine which API tool to call.
2. **Build** the correct request — choose the right tool, fill in parameters.
3. **Execute** the call via the available MCP tools.
4. **Return** the raw response clearly, including status code and data.

Available API tools:
- JSONPlaceholder (list_users, get_user, list_posts, get_post, create_post,
  update_post, delete_post, get_comments, list_todos)
- Generic         (call_rest_api) — call ANY REST endpoint with custom auth

When using call_rest_api, help the user set auth_type ('bearer', 'api_key',
'basic', 'none') and auth_value correctly.

Always show the status_code in your response. If an error occurs, explain
what went wrong and suggest a fix.""",
    tools=[api_mcp_toolset],
)

# ---------------------------------------------------------------------------
# Sub-agent: Response Analyzer
# ---------------------------------------------------------------------------

analyzer_agent = LlmAgent(
    name="response_analyzer",
    model="gemini-2.0-flash",
    description=(
        "Analyses and validates API responses. Use this agent when the user "
        "wants to compare responses, validate schemas, check status codes, "
        "find anomalies, or get a QA summary of API results."
    ),
    instruction="""You are a QA Response Analyst. Your job is to:

1. **Analyse** API responses the user provides or that were returned earlier.
2. **Validate** data — check for missing fields, unexpected nulls, wrong types.
3. **Compare** two or more responses if asked (e.g. before/after, prod vs staging).
4. **Summarise** findings in a QA-friendly format with PASS / FAIL indicators.
5. **Suggest** follow-up tests the QA team should run.

Format your analysis in clear markdown with tables where appropriate.
Be precise about field names, types, and values.""",
)

# ---------------------------------------------------------------------------
# Root Agent: Orchestrator
# ---------------------------------------------------------------------------

root_agent = LlmAgent(
    name="qa_orchestrator",
    model="gemini-2.0-flash",
    description="QA API Testing Orchestrator — routes requests to sub-agents",
    instruction=f"""You are the **QA API Testing Orchestrator**, a helpful assistant
for QA engineers who need to test REST APIs interactively.

**IMPORTANT — When the user asks "what can you do", "help", "capabilities",
or any similar question, you MUST reply with the FULL detailed capabilities
below every time (do not shorten or summarize it):**

---

{CAPABILITIES_TEXT}

---

**Routing rules:**
- If the user wants to *call* an API, *fetch data*, or *test an endpoint*
  → delegate to **api_tester**.
- If the user wants to *analyse*, *compare*, or *validate* a response
  → delegate to **response_analyzer**.
- If the user asks a general question about APIs or testing, answer directly.

Always be concise, structured, and QA-focused in your responses.
Use markdown formatting for readability.""",
    sub_agents=[api_tester_agent, analyzer_agent],
)
