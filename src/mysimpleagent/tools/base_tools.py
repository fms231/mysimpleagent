from datetime import datetime
from pathlib import Path

from .tool_repository import ToolRepository
from .tool_schema import ToolSchema


class BaseTools(ToolRepository):
    """Built-in tools available to an Agent by default."""

    def __init__(self, output_dir: str = "output"):
        super().__init__()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.add_tool(self._tool("get_system_time", "Get the current system time.", self.get_system_time, {"type": "object", "properties": {}, "additionalProperties": False}))
        self.add_tool(self._tool("read_file", "Read a UTF-8 text file from the output directory.", self.read_file, {"type": "object", "properties": {"file_name": {"type": "string"}}, "required": ["file_name"], "additionalProperties": False}))
        self.add_tool(self._tool("write_file", "Write UTF-8 text to a file in the output directory.", self.write_file, {"type": "object", "properties": {"file_name": {"type": "string"}, "content": {"type": "string"}}, "required": ["file_name", "content"], "additionalProperties": False}))

    @staticmethod
    def _tool(name, description, func, parameters):
        tool = ToolSchema()
        tool.name = name
        tool.description = description
        tool.func = func
        tool.parameters = parameters
        return tool

    def get_system_time(self) -> str:
        return datetime.now().astimezone().isoformat()

    def _get_file_path(self, file_name: str) -> Path:
        root = self.output_dir.resolve()
        path = (root / file_name).resolve()
        if path != root and root not in path.parents:
            raise ValueError("File must be inside the output directory")
        return path

    def read_file(self, file_name: str) -> str:
        return self._get_file_path(file_name).read_text(encoding="utf-8")

    def write_file(self, file_name: str, content: str) -> str:
        path = self._get_file_path(file_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"File written: {file_name}"
