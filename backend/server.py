import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from mysimpleagent.agent.agent import Agent
from mysimpleagent.conversation.conversation import Conversation
from mysimpleagent.llm.llm import LLM
from mysimpleagent.tools.tool_repository import ToolRepository


agent = Agent(LLM(), ToolRepository())


class ChatHandler(BaseHTTPRequestHandler):
    def _send_json(self, status, body):
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self):
        self._send_json(204, {})

    def do_POST(self):
        if self.path != "/api/chat":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length))
            message = request["message"]
            session_id = request.get("session_id", "default")
            conversation = Conversation(agent, session_id=session_id)
            response = conversation.send(message)
            content = response.choices[0].message.content
            self._send_json(200, {"content": content, "session_id": conversation.session_id})
        except Exception as error:
            self._send_json(500, {"error": str(error)})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    print("Backend listening at http://localhost:8000")
    HTTPServer(("localhost", 8000), ChatHandler).serve_forever()
