import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

from mysimpleagent.agent.agent import Agent
from mysimpleagent.conversation.conversation import Conversation
from mysimpleagent.llm.llm import LLM
from mysimpleagent.tools.tool_repository import ToolRepository


agent = Agent(LLM(), ToolRepository())
SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class ChatHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, body=None):
        payload = b"" if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        if body is not None:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if payload:
            self.wfile.write(payload)

    def do_OPTIONS(self):
        self._send_json(204)

    def do_POST(self):
        if self.path != "/api/chat":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length))
            if not isinstance(request, dict):
                raise ValueError("request must be an object")
            message = request.get("message")
            session_id = request.get("session_id", "default")
            if not isinstance(message, str) or not message.strip():
                raise ValueError("message must be a non-empty string")
            if not isinstance(session_id, str) or not SESSION_ID_PATTERN.fullmatch(session_id):
                raise ValueError("invalid session_id")
            conversation = Conversation(agent, session_id=session_id)
            response = conversation.send(message)
            content = response.choices[0].message.content
            self._send_json(200, {"content": content, "session_id": conversation.session_id})
        except (ValueError, TypeError, json.JSONDecodeError):
            self._send_json(400, {"error": "Invalid request"})
        except Exception:
            self._send_json(500, {"error": "Internal server error"})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    print("Backend listening at http://localhost:8000")
    HTTPServer(("localhost", 8000), ChatHandler).serve_forever()
