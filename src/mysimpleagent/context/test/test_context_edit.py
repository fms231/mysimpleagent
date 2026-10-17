import unittest

from mysimpleagent.context.context import Context


class ContextEditTest(unittest.TestCase):
    def test_replaces_message_and_discards_following_history(self):
        context = Context()
        context.add_message("user", "a1")
        context.add_message("assistant", "b1")
        context.add_message("user", "a2")
        context.add_message("assistant", "b2")

        context.replace_user_message(2, "a2-new")

        self.assertEqual(context.messages, [
            {"id": 0, "role": "user", "content": "a1"},
            {"id": 1, "role": "assistant", "content": "b1"},
            {"id": 4, "role": "user", "content": "a2-new"},
        ])
        self.assertEqual(context.id, 5)


    def test_edit_keeps_next_id_monotonic_when_history_has_gaps(self):
        context = Context()
        context.messages = [
            {"id": 2, "role": "user", "content": "a1"},
            {"id": 7, "role": "user", "content": "a2"},
            {"id": 9, "role": "assistant", "content": "b2"},
        ]
        context.id = 10

        context.replace_user_message(7, "a2-new")

        self.assertEqual(context.messages[-1]["id"], 10)
        self.assertEqual(context.id, 11)


if __name__ == "__main__":
    unittest.main()
