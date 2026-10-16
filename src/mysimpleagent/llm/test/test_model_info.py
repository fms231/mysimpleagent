import unittest

from mysimpleagent.llm.model_info import get_model_metadata


class GetModelMetadataTest(unittest.TestCase):
    def test_returns_metadata_from_litellm(self):
        metadata = get_model_metadata("openai/gpt-6-luna")

        self.assertIsInstance(metadata, dict)
        self.assertTrue(metadata)
        self.assertGreater(metadata["max_tokens"], 0)


if __name__ == "__main__":
    unittest.main()
