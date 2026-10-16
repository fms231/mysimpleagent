import unittest

from src.llm.llm import LLM


class LLMChatTest(unittest.TestCase):
    def test_chat_returns_litellm_response(self):
        llm = LLM("openai/gpt-6-luna")
        messages = [{"role": "user", "content": "请你只回答你好"}]

        response = llm.chat(messages, temperature=1)

        print(f"Response: {response.choices[0].message.content}")


if __name__ == "__main__":
    unittest.main()
