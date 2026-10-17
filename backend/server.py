import re
from threading import Lock
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from mysimpleagent.agent.agent import Agent
from mysimpleagent.conversation.conversation import Conversation
from mysimpleagent.llm.llm import LLM


app = FastAPI(title="MySimpleAgent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

agent = Agent(LLM())
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
SESSIONS_DIR = Path("sessions")
SESSION_LOCKS: dict[str, Lock] = {}
SESSION_LOCKS_GUARD = Lock()


def get_session_lock(session_id: str) -> Lock:
    with SESSION_LOCKS_GUARD:
        if session_id not in SESSION_LOCKS:
            SESSION_LOCKS[session_id] = Lock()
        return SESSION_LOCKS[session_id]


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    edit_message_id: int | None = None

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message must be a non-empty string")
        return value

    @field_validator("session_id")
    @classmethod
    def session_id_must_be_safe(cls, value: str) -> str:
        if not SESSION_ID_PATTERN.fullmatch(value):
            raise ValueError("invalid session_id")
        return value

    @field_validator("edit_message_id")
    @classmethod
    def edit_message_id_must_be_non_negative(cls, value: int | None) -> int | None:
        if value is not None and value < 0:
            raise ValueError("invalid edit_message_id")
        return value


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_, __):
    return JSONResponse(status_code=400, content={"error": "Invalid request"})


@app.get("/api/sessions")
def list_sessions():
    sessions = []
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    for file_path in SESSIONS_DIR.glob("*.jsonl"):
        if file_path.stat().st_size == 0:
            continue
        session_id = file_path.stem
        if SESSION_ID_PATTERN.fullmatch(session_id):
            sessions.append({
                "session_id": session_id,
                "updated_at": file_path.stat().st_mtime,
            })
    sessions.sort(key=lambda item: item["updated_at"], reverse=True)
    return {"sessions": sessions}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: str):
    if not SESSION_ID_PATTERN.fullmatch(session_id):
        raise HTTPException(status_code=400, detail="Invalid request")
    file_path = SESSIONS_DIR / f"{session_id}.jsonl"
    try:
        with get_session_lock(session_id):
            if not file_path.is_file() or file_path.stat().st_size == 0:
                raise HTTPException(status_code=404, detail="Session not found")
            conversation = Conversation(agent, session_id=session_id)
            return {"session_id": session_id, "messages": conversation.context.messages}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/chat")
def chat(request: ChatRequest):
    try:
        with get_session_lock(request.session_id):
            conversation = Conversation(agent, session_id=request.session_id)
            if request.edit_message_id is None:
                response = conversation.send(request.message)
            else:
                response = conversation.edit_and_send(request.edit_message_id, request.message)
            content = response.choices[0].message.content
            return {
                "content": content,
                "session_id": conversation.session_id,
                "messages": conversation.context.messages,
            }
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")
