"""Skills loader — reads agent capabilities from a standard Markdown skill file.

The skill file (api_skills.md) follows the open-source skill configuration
convention using Markdown with YAML frontmatter:

  ---
  name: ...
  version: ...
  description: ...
  ---

  # Skills
  ## Skill: <Skill Name>
  ### Tool: <Tool Name>
  #### Parameters
  #### Examples

This module parses the markdown and builds structured capability text
that is injected into the agent's system instruction.
"""

import re
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent
SKILLS_FILE = SKILLS_DIR / "api_skills.md"


def load_skills_markdown() -> str:
    """Load the raw markdown content of the skills file."""
    with open(SKILLS_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).strip().splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip()
    return fm


def _extract_skills_section(content: str) -> str:
    """Extract the body after frontmatter (the skills content)."""
    match = re.match(r"^---\s*\n.*?\n---\s*\n", content, re.DOTALL)
    if match:
        return content[match.end():]
    return content


def _parse_tools_from_skill(skill_block: str) -> list[dict]:
    """Parse tool definitions from a skill section."""
    tools = []
    tool_blocks = re.split(r"^### Tool:\s*", skill_block, flags=re.MULTILINE)

    for block in tool_blocks[1:]:  # skip content before first tool
        lines = block.strip().splitlines()
        tool_name = lines[0].strip()

        # Extract metadata
        method = ""
        endpoint = ""
        description = ""
        for line in lines[1:]:
            if line.startswith("- **Method:**"):
                method = line.split(":**")[1].strip()
            elif line.startswith("- **Endpoint:**"):
                endpoint = line.split(":**")[1].strip()
            elif line.startswith("- **Description:**"):
                description = line.split(":**")[1].strip()

        # Extract parameters table
        params = []
        in_params_table = False
        for line in lines:
            if "| Name |" in line:
                in_params_table = True
                continue
            if in_params_table and line.startswith("|---"):
                continue
            if in_params_table and line.startswith("|"):
                cols = [c.strip() for c in line.strip("|").split("|")]
                if len(cols) >= 5 and cols[0] != "—":
                    params.append({
                        "name": cols[0],
                        "type": cols[1],
                        "required": cols[2].lower() == "yes",
                        "default": cols[3] if cols[3] != "—" else None,
                        "description": cols[4],
                    })
            elif in_params_table and not line.startswith("|"):
                in_params_table = False

        # Extract examples
        examples = re.findall(r"```prompt\s*\n(.*?)\n```", block, re.DOTALL)

        tools.append({
            "name": tool_name,
            "method": method,
            "endpoint": endpoint,
            "description": description,
            "params": params,
            "examples": [e.strip() for e in examples],
        })

    return tools


def _parse_skills(content: str) -> list[dict]:
    """Parse all skills from the markdown body."""
    body = _extract_skills_section(content)
    skill_blocks = re.split(r"^## Skill:\s*", body, flags=re.MULTILINE)

    skills = []
    for block in skill_blocks[1:]:  # skip content before first skill
        lines = block.strip().splitlines()
        skill_name = lines[0].strip()

        # Extract skill metadata (only from lines before first ### heading)
        base_url = ""
        auth_required = "No"
        description = ""
        for line in lines[1:]:
            if line.startswith("###"):
                break
            if line.startswith("- **Base URL:**"):
                base_url = line.split(":**")[1].strip()
            elif line.startswith("- **Auth Required:**"):
                auth_required = line.split(":**")[1].strip()
            elif line.startswith("- **Description:**"):
                description = line.split(":**")[1].strip()

        tools = _parse_tools_from_skill(block)

        # Extract capabilities list (for non-tool skills like Response Analysis)
        capabilities = []
        in_capabilities = False
        for line in lines:
            if "### Capabilities" in line:
                in_capabilities = True
                continue
            if in_capabilities and line.startswith("- "):
                capabilities.append(line[2:].strip())
            elif in_capabilities and line.startswith("#"):
                break

        # Extract standalone examples (for skills without tools)
        standalone_examples = []
        if not tools:
            standalone_examples = re.findall(
                r"```prompt\s*\n(.*?)\n```", block, re.DOTALL
            )
            standalone_examples = [e.strip() for e in standalone_examples]

        skills.append({
            "name": skill_name,
            "base_url": base_url,
            "auth_required": auth_required,
            "description": description,
            "tools": tools,
            "capabilities": capabilities,
            "examples": standalone_examples,
        })

    return skills


def build_capabilities_text() -> str:
    """Build a formatted markdown capabilities string from the skills .md file.
    This is injected into the agent's system instruction so it can
    describe its full capabilities to users."""
    content = load_skills_markdown()
    skills = _parse_skills(content)

    lines = []
    lines.append("## What I Can Do\n")

    for idx, skill in enumerate(skills, 1):
        # Skill header
        url_part = f" ({skill['base_url']})" if skill["base_url"] and skill["base_url"] != "N/A" else ""
        lines.append(f"### {idx}. {skill['name']}{url_part}")
        if skill["description"]:
            lines.append(f"{skill['description']}")
        lines.append(f"**Authentication required:** {skill['auth_required']}\n")

        if skill["tools"]:
            # Build tools table
            lines.append("| Tool | Method | Required Params | Optional Params | Description |")
            lines.append("|------|--------|----------------|-----------------|-------------|")
            for tool in skill["tools"]:
                required = ", ".join(
                    f"`{p['name']}` ({p['type']})"
                    for p in tool["params"] if p["required"]
                ) or "—"
                optional = ", ".join(
                    f"`{p['name']}` ({p['type']})"
                    for p in tool["params"] if not p["required"]
                ) or "—"
                lines.append(
                    f"| `{tool['name']}` | {tool['method']} | {required} | {optional} | {tool['description']} |"
                )
            lines.append("")

            # Auth types table if present in the skill block
            if "Authentication Types" in content and skill["name"] == "Generic REST API Caller":
                lines.append("**Authentication types supported:**")
                lines.append("- **`none`** — No authentication (default)")
                lines.append("- **`api_key`** — Adds `?api_key=<value>` as query parameter")
                lines.append("- **`bearer`** — Adds `Authorization: Bearer <value>` header (OAuth tokens)")
                lines.append("- **`basic`** — Adds `Authorization: Basic <value>` header (Base64 user:pass)")
                lines.append("")

        elif skill["capabilities"]:
            lines.append("**Capabilities:**")
            for cap in skill["capabilities"]:
                lines.append(f"- {cap}")
            lines.append("")

    return "\n".join(lines)


def build_sample_prompts_text() -> str:
    """Build a formatted list of all sample prompts from the skills .md file."""
    content = load_skills_markdown()
    skills = _parse_skills(content)

    lines = []
    for skill in skills:
        lines.append(f"### {skill['name']} — Sample Prompts\n")

        if skill["tools"]:
            for tool in skill["tools"]:
                if tool["examples"]:
                    lines.append(f"**{tool['name']}**")
                    for ex in tool["examples"]:
                        lines.append(f"- `{ex}`")
                    lines.append("")

        if skill["examples"]:
            for ex in skill["examples"]:
                lines.append(f"- `{ex}`")
            lines.append("")

    return "\n".join(lines)
