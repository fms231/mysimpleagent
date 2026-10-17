import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from mysimpleagent.tools.base_tools import BaseTools


class BaseToolsTest(unittest.TestCase):
    def test_file_tools_use_output_directory(self):
        with TemporaryDirectory() as directory:
            tools = BaseTools(directory)
            tools.call("write_file", file_name="note.txt", content="hello")

            self.assertEqual(tools.call("read_file", file_name="note.txt"), "hello")
            self.assertTrue((Path(directory) / "note.txt").exists())

    def test_file_tools_reject_path_traversal(self):
        with TemporaryDirectory() as directory:
            tools = BaseTools(directory)
            with self.assertRaises(ValueError):
                tools.call("read_file", file_name="../secret.txt")

    def test_system_time_is_available(self):
        with TemporaryDirectory() as directory:
            self.assertTrue(BaseTools(directory).call("get_system_time"))


if __name__ == "__main__":
    unittest.main()
