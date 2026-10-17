class ToolHook:
    """Extension points around an Agent tool call."""

    def before_tool_call(self, name, arguments, context):
        pass

    def after_tool_call(self, name, arguments, result, context):
        pass

    def on_tool_error(self, name, arguments, error, context):
        pass
