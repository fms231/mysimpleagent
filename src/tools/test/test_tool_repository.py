import unittest

from src.tools.tool_repository import ToolRepository
from src.tools.tool_schema import ToolSchema


class ToolRepositoryTest(unittest.TestCase):
    def test_add_tool_and_call(self):
        def add(a: int, b: int) -> int:
            return a + b

        tool = ToolSchema()
        tool.name = "add"
        tool.description = "Add two numbers."
        tool.func = add
        tool.parameters = {
            "type": "object",
            "properties": {
                "a": {"type": "integer"},
                "b": {"type": "integer"},
            },
            "required": ["a", "b"],
        }

        repository = ToolRepository()
        repository.add_tool(tool)

        self.assertIs(repository.get_tool("add"), tool)
        self.assertEqual(repository.call("add", a=2, b=3), 5)


if __name__ == "__main__":
    unittest.main()
