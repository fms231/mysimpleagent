import unittest
from unittest.mock import patch

from mysimpleagent.context.context import Context
from mysimpleagent.context.context_strategy import ContextStrategy


class ContextStrategyTest(unittest.TestCase):
    @patch("mysimpleagent.context.context_strategy.litellm.token_counter", return_value=80)
    def test_logs_error_at_eighty_percent(self, _token_counter):
        strategy = ContextStrategy(model="custom/model", max_context=100)
        context = Context(context_strategy=strategy)

        with self.assertLogs("mysimpleagent.context.context_strategy", level="ERROR") as logs:
            context.add_message("user", "message")

        self.assertIn("80.0%", logs.output[0])

    @patch("mysimpleagent.context.context_strategy.litellm.token_counter", return_value=79)
    def test_does_not_log_below_threshold(self, _token_counter):
        strategy = ContextStrategy(model="custom/model", max_context=100)
        context = Context(context_strategy=strategy)

        context.add_message("user", "message")

    @patch("mysimpleagent.context.context_strategy.litellm.token_counter", return_value=80)
    def test_logs_each_time_context_remains_over_threshold(self, _token_counter):
        context = Context(
            context_strategy=ContextStrategy(model="custom/model", max_context=100)
        )

        with self.assertLogs("mysimpleagent.context.context_strategy", level="ERROR") as logs:
            context.add_message("user", "first")
            context.add_message("user", "second")

        self.assertEqual(len(logs.records), 2)


if __name__ == "__main__":
    unittest.main()
