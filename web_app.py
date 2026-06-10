"""
FastAPI web chat interface for the QA Agentic AI API.

Provides a browser-based chat UI so the QA team can interact with the
orchestrator agent from any device.

Usage:
    python web_app.py               # Starts on http://localhost:8000
    uvicorn web_app:app --reload    # With auto-reload for development
"""

import asyncio
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

app = FastAPI(title="QA Agentic AI API", version="1.0.0")

# ---------------------------------------------------------------------------
# Agent bootstrap (lazy — imported once on first request)
# ---------------------------------------------------------------------------

_runner = None
_session_service = None


def _get_runner():
    global _runner, _session_service
    if _runner is None:
        from qa_agent.agent import root_agent

        _session_service = InMemorySessionService()
        _runner = Runner(
            agent=root_agent,
            app_name=root_agent.name,
            session_service=_session_service,
        )
    return _runner, _session_service


# ---------------------------------------------------------------------------
# HTML Chat UI
# ---------------------------------------------------------------------------

CHAT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>QA Agentic AI — API Tester</title>
<script src="https://cdn.tailwindcss.com"></script>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
<style>
  body { font-family: 'Inter', sans-serif; }
  .msg-user  { @apply bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-2 max-w-[75%] ml-auto; }
  .msg-agent { @apply bg-gray-100 text-gray-800 rounded-2xl rounded-bl-md px-4 py-2 max-w-[75%]; }
  .msg-agent pre { @apply bg-gray-200 rounded p-2 overflow-x-auto text-sm my-1; }
  .msg-agent code { @apply text-sm; }
  #chat::-webkit-scrollbar { width: 6px; }
  #chat::-webkit-scrollbar-thumb { @apply bg-gray-300 rounded-full; }
  .typing-dot { animation: blink 1.4s infinite both; }
  .typing-dot:nth-child(2) { animation-delay: 0.2s; }
  .typing-dot:nth-child(3) { animation-delay: 0.4s; }
  @keyframes blink { 0%,80%,100%{opacity:0} 40%{opacity:1} }
</style>
</head>
<body class="bg-gray-50 h-screen flex flex-col">

  <!-- Header -->
  <header class="bg-white border-b px-6 py-4 flex items-center gap-3 shadow-sm">
    <div class="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-lg">Q</div>
    <div>
      <h1 class="text-lg font-semibold text-gray-800">QA API Testing Agent</h1>
      <p class="text-xs text-gray-500">Powered by Google ADK + MCP</p>
    </div>
    <span id="status-badge" class="ml-auto text-xs font-medium px-2.5 py-0.5 rounded-full bg-green-100 text-green-700">Online</span>
  </header>

  <!-- Chat area -->
  <main id="chat" class="flex-1 overflow-y-auto px-6 py-4 space-y-3">
    <div class="msg-agent">
      <p><strong>Welcome!</strong> I'm your QA API Testing Assistant.</p>
      <p class="mt-1 text-sm">I can help you:</p>
      <ul class="list-disc ml-5 text-sm mt-1 space-y-0.5">
        <li>Call REST APIs (JSONPlaceholder, GitHub, Weather, or any URL)</li>
        <li>Test CRUD operations (GET, POST, PUT, DELETE)</li>
        <li>Authenticate with API keys or OAuth tokens</li>
        <li>Analyse and validate API responses</li>
      </ul>
      <p class="mt-2 text-sm text-gray-500">Try: <em>"List all users from JSONPlaceholder"</em></p>
    </div>
  </main>

  <!-- Input bar -->
  <form id="form" class="bg-white border-t px-4 py-3 flex gap-2">
    <input id="input" type="text" placeholder="Ask me to test an API…"
           class="flex-1 border rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
           autocomplete="off" />
    <button type="submit"
            class="bg-blue-600 hover:bg-blue-700 text-white rounded-xl px-5 py-2.5 text-sm font-medium transition">
      Send
    </button>
  </form>

<script>
  const chat  = document.getElementById('chat');
  const form  = document.getElementById('form');
  const input = document.getElementById('input');
  const badge = document.getElementById('status-badge');

  let ws;
  let sessionId = null;

  function connect() {
    ws = new WebSocket(`ws://${location.host}/ws/chat`);
    ws.onopen = () => { badge.textContent = 'Online'; badge.className = badge.className.replace(/bg-\\w+-100 text-\\w+-700/, 'bg-green-100 text-green-700'); };
    ws.onclose = () => { badge.textContent = 'Offline'; badge.className = badge.className.replace(/bg-\\w+-100 text-\\w+-700/, 'bg-red-100 text-red-700'); setTimeout(connect, 3000); };
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.session_id) sessionId = data.session_id;
      if (data.response) {
        removeTyping();
        appendMsg('agent', data.response);
      }
    };
  }
  connect();

  function appendMsg(role, text) {
    const div = document.createElement('div');
    div.className = role === 'user' ? 'msg-user' : 'msg-agent';
    // Basic markdown-ish rendering
    div.innerHTML = text
      .replace(/```([\\s\\S]*?)```/g, '<pre><code>$1</code></pre>')
      .replace(/`([^`]+)`/g, '<code class="bg-gray-200 px-1 rounded text-sm">$1</code>')
      .replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>')
      .replace(/\\n/g, '<br/>');
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  function showTyping() {
    const div = document.createElement('div');
    div.id = 'typing';
    div.className = 'msg-agent flex gap-1 items-center';
    div.innerHTML = '<span class="typing-dot w-2 h-2 bg-gray-400 rounded-full inline-block"></span><span class="typing-dot w-2 h-2 bg-gray-400 rounded-full inline-block"></span><span class="typing-dot w-2 h-2 bg-gray-400 rounded-full inline-block"></span>';
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }
  function removeTyping() { document.getElementById('typing')?.remove(); }

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text || ws.readyState !== WebSocket.OPEN) return;
    appendMsg('user', text);
    showTyping();
    ws.send(JSON.stringify({ prompt: text, session_id: sessionId }));
    input.value = '';
  });
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return CHAT_HTML


# ---------------------------------------------------------------------------
# WebSocket chat endpoint
# ---------------------------------------------------------------------------


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    runner, session_service = _get_runner()
    user_id = f"qa_web_{uuid.uuid4().hex[:8]}"

    session = await session_service.create_session(
        app_name=runner.app_name,
        user_id=user_id,
    )
    session_id = session.id

    await websocket.send_json({"session_id": session_id})

    try:
        while True:
            data = await websocket.receive_json()
            prompt = data.get("prompt", "").strip()
            if not prompt:
                continue

            content = types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt)],
            )

            final_text = ""
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                if event.is_final_response():
                    for part in event.content.parts:
                        if part.text:
                            final_text += part.text

            await websocket.send_json({"response": final_text or "(No response)"})

    except WebSocketDisconnect:
        pass


# ---------------------------------------------------------------------------
# REST endpoint (alternative to WebSocket)
# ---------------------------------------------------------------------------


@app.post("/api/chat")
async def api_chat(payload: dict):
    """Simple REST endpoint for chat. Body: {"prompt": "...", "session_id": "..."}"""
    runner, session_service = _get_runner()
    prompt = payload.get("prompt", "").strip()
    session_id = payload.get("session_id")

    if not prompt:
        return {"error": "prompt is required"}

    user_id = "qa_api_user"

    if not session_id:
        session = await session_service.create_session(
            app_name=runner.app_name,
            user_id=user_id,
        )
        session_id = session.id

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt)],
    )

    final_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response():
            for part in event.content.parts:
                if part.text:
                    final_text += part.text

    return {"response": final_text, "session_id": session_id}


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web_app:app", host="0.0.0.0", port=8000, reload=True)
