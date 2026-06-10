"""
CLI runner for the QA Agentic AI API project.

Usage:
    python main.py                  # Interactive CLI chat
    python main.py --once "prompt"  # Single prompt, then exit

Alternatively, use the built-in ADK web UI:
    adk web qa_agent
"""

import argparse
import asyncio
import sys
import uuid

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

load_dotenv()


async def run_agent(prompt: str, runner: Runner, user_id: str, session_id: str):
    """Send a single prompt to the orchestrator and stream the response."""
    from google.genai import types

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)],
    )

    final_response = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response():
            for part in event.content.parts:
                if part.text:
                    final_response += part.text

    return final_response


async def interactive_loop():
    """Run an interactive chat loop in the terminal."""
    from qa_agent.agent import root_agent

    session_service = InMemorySessionService()
    user_id = f"qa_user_{uuid.uuid4().hex[:8]}"
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    session = await session_service.create_session(
        app_name=root_agent.name,
        user_id=user_id,
    )
    session_id = session.id

    runner = Runner(
        agent=root_agent,
        app_name=root_agent.name,
        session_service=session_service,
    )

    print("=" * 60)
    print("  QA Agentic AI API — Interactive Chat")
    print("  Type 'quit' or 'exit' to stop.")
    print("=" * 60)
    print()

    while True:
        try:
            prompt = input("You > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not prompt:
            continue
        if prompt.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        response = await run_agent(prompt, runner, user_id, session_id)
        print(f"\nAgent > {response}\n")


async def single_prompt(prompt: str):
    """Run a single prompt and print the response."""
    from qa_agent.agent import root_agent

    session_service = InMemorySessionService()
    user_id = "qa_user_cli"

    session = await session_service.create_session(
        app_name=root_agent.name,
        user_id=user_id,
    )

    runner = Runner(
        agent=root_agent,
        app_name=root_agent.name,
        session_service=session_service,
    )

    response = await run_agent(prompt, runner, user_id, session.id)
    print(response)


def main():
    parser = argparse.ArgumentParser(description="QA Agentic AI API — CLI")
    parser.add_argument("--once", type=str, help="Run a single prompt and exit")
    args = parser.parse_args()

    if args.once:
        asyncio.run(single_prompt(args.once))
    else:
        asyncio.run(interactive_loop())


if __name__ == "__main__":
    main()
