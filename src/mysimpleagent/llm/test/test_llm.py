import unittest
from unittest.mock import patch

from mysimpleagent.llm.llm import LLM


class LLMChatTest(unittest.TestCase):
    @patch("mysimpleagent.llm.llm.litellm.completion")
    @patch("mysimpleagent.llm.llm.get_model_metadata", side_effect=ValueError("unknown model"))
    def test_unknown_model_omits_max_tokens(self, _get_model_metadata, completion):
        llm = LLM("custom/model", base_url="https://example.com/v1", api_key="key")

        llm.chat([{"role": "user", "content": "hello"}])

        self.assertIsNone(llm.max_output_tokens)
        self.assertNotIn("max_tokens", completion.call_args.kwargs)

    @patch("mysimpleagent.llm.llm.get_model_metadata")
    def test_records_input_output_and_total_context(self, get_metadata):
        get_metadata.return_value = {"max_input_tokens": 900, "max_output_tokens": 100}

        llm = LLM("custom/model", max_context=800)

        self.assertEqual(llm.max_input_tokens, 900)
        self.assertEqual(llm.max_output_tokens, 100)
        self.assertEqual(llm.max_context, 800)
        self.assertEqual(llm.get_max_tokens(), 800)
        self.assertEqual(llm.get_max_output_tokens(), 100)

    @patch("mysimpleagent.llm.llm.get_model_metadata")
    def test_rejects_context_above_model_total(self, get_metadata):
        get_metadata.return_value = {"max_input_tokens": 900, "max_output_tokens": 100}

        with self.assertRaises(ValueError):
            LLM("custom/model", max_context=1001)

    @patch("mysimpleagent.llm.llm.get_model_metadata", return_value={
        "max_input_tokens": 900,
        "max_output_tokens": 100,
        "max_context_window": 800,
    })
    def test_context_window_takes_priority_over_input_output_sum(self, _get_metadata):
        llm = LLM("custom/model")

        self.assertEqual(llm.max_context, 800)

    @patch("mysimpleagent.llm.llm.get_model_metadata", return_value={"max_input_tokens": 900})
    def test_input_limit_is_used_when_context_window_is_missing(self, _get_metadata):
        llm = LLM("custom/model")

        self.assertEqual(llm.max_context, 900)

    @patch("mysimpleagent.llm.llm.litellm.completion")
    @patch("mysimpleagent.llm.llm.get_model_metadata", return_value={"max_tokens": 8192})
    def test_chat_max_tokens_override(self, _get_model_metadata, completion):
        llm = LLM("custom/model", base_url="https://example.com/v1", api_key="key")

        llm.chat([], max_tokens=100)

        self.assertEqual(completion.call_args.kwargs["max_tokens"], 100)

    @patch("mysimpleagent.llm.llm.litellm.completion")
    @patch("mysimpleagent.llm.llm.litellm.token_counter", return_value=900)
    @patch("mysimpleagent.llm.llm.get_model_metadata", return_value={"max_input_tokens": 900, "max_output_tokens": 500})
    def test_chat_limits_output_to_remaining_context(self, _metadata, _token_counter, completion):
        llm = LLM("custom/model", base_url="https://example.com/v1", api_key="key", max_context=1000)

        llm.chat([])

        self.assertEqual(completion.call_args.kwargs["max_tokens"], 100)

    def test_chat_returns_litellm_response(self):
        llm = LLM("openai/gpt-6-luna")
        messages = [{"role": "user", "content": "请你只回答你好"}]

        response = llm.chat(messages, temperature=1)

        print(f"Response: {response.choices[0].message.content}")


if __name__ == "__main__":
    unittest.main()
