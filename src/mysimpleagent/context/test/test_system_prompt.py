import unittest

from mysimpleagent.context.context import Context
from mysimpleagent.systemprompt.system_prompt import SystemPrompt


class SystemPromptTest(unittest.TestCase):
    def test_converts_to_system_message(self):
        prompt = SystemPrompt("Be concise")

        self.assertEqual(prompt.to_message(), {"role": "system", "content": "Be concise"})

    def test_context_accepts_system_prompt_object(self):
        context = Context(system_prompt=SystemPrompt("Be concise"))

        self.assertEqual(context.messages, [])
        self.assertEqual(context.model_message, [])
        self.assertEqual(context.id, 0)
        self.assertEqual(context.model_messages(), [
            {"role": "system", "content": "Be concise"},
        ])


if __name__ == "__main__":
    unittest.main()
