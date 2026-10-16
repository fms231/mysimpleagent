import unittest
from unittest.mock import patch

from mysimpleagent.llm.llm import LLM


class LLMChatTest(unittest.TestCase):
    @patch("mysimpleagent.llm.llm.litellm.completion")
    @patch("mysimpleagent.llm.llm.get_model_metadata", side_effect=ValueError("unknown model"))
    def test_unknown_model_omits_max_tokens(self, _get_model_metadata, completion):
        llm = LLM("custom/model", base_url="https://example.com/v1", api_key="key")

        llm.chat([{"role": "user", "content": "hello"}])

        self.assertIsNone(llm.max_tokens)
        self.assertNotIn("max_tokens", completion.call_args.kwargs)

    @patch("mysimpleagent.llm.llm.litellm.completion")
    @patch("mysimpleagent.llm.llm.get_model_metadata", return_value={"max_tokens": 8192})
    def test_chat_max_tokens_override(self, _get_model_metadata, completion):
        llm = LLM("custom/model", base_url="https://example.com/v1", api_key="key")

        llm.chat([], max_tokens=100)

        self.assertEqual(completion.call_args.kwargs["max_tokens"], 100)

    def test_chat_returns_litellm_response(self):
        llm = LLM("openai/gpt-6-luna")
        messages = [{"role": "user", "content": "请你只回答你好"}]

        response = llm.chat(messages, temperature=1)

        print(f"Response: {response.choices[0].message.content}")


if __name__ == "__main__":
    unittest.main()
