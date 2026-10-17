import json
import logging
from time import perf_counter

from ..context.context import Context
from ..tools.base_tools import BaseTools
from ..tools.tool_repository import ToolRepository
from ..observability import Observability
from ..observability import (
    LLMEndEvent,
    LLMErrorEvent,
    LLMStartEvent,
    ToolEndEvent,
    ToolErrorEvent,
    ToolStartEvent,
)


logger = logging.getLogger(__name__)


class Agent:
    def __init__(
        self,
        llm,
        tools: ToolRepository | None = None,
        max_tool_rounds: int = 10,
        hooks: list | None = None,
        skills: list | None = None,
        observability: Observability | None = None,
    ):
        self.llm = llm
        self.tools = tools if tools is not None else BaseTools()
        self.max_tool_rounds = max_tool_rounds
        self.hooks = hooks or []
        self.skills = skills or []
        self.observability = observability

    def run(self, context: Context):
        skill_prompts = [skill.to_prompt() for skill in self.skills]
        while True:
            model_messages = context.model_messages(
                extra_system_prompts=skill_prompts
            )
            started = perf_counter()
            if self.observability is not None:
                self.observability.emit("on_llm_start", LLMStartEvent(self.llm.model, model_messages))
            try:
                response = self.llm.chat(model_messages, tools=self.tools.list_tools())
            except Exception as error:
                if self.observability is not None:
                    self.observability.emit(
                        "on_llm_error",
                        LLMErrorEvent(self.llm.model, error, (perf_counter() - started) * 1000),
                    )
                raise
            if self.observability is not None:
                self.observability.emit(
                    "on_llm_end",
                    LLMEndEvent(self.llm.model, response, (perf_counter() - started) * 1000),
                )

            message = response.choices[0].message
            tool_calls = getattr(message, "tool_calls", None) or []
            if not tool_calls:
                context.add_message("assistant", getattr(message, "content", None) or "")
                return response

            context.add_message(
                "assistant",
                getattr(message, "content", None),
                tool_calls=[
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in tool_calls
                ],
            )

            for call in tool_calls:
                result = None
                for attempt in range(self.max_tool_rounds + 1):
                    arguments = {}
                    started = None
                    try:
                        arguments = json.loads(call.function.arguments)
                        for hook in self.hooks:
                            hook.before_tool_call(call.function.name, arguments, context)
                    except Exception as error:
                        for hook in self.hooks:
                            hook.on_tool_error(call.function.name, arguments, error, context)
                        if attempt == self.max_tool_rounds:
                            result = (
                                f"Tool '{call.function.name}' is unavailable after "
                                f"{self.max_tool_rounds} failed retries: {error}"
                            )
                        continue

                    try:
                        started = perf_counter()
                        if self.observability is not None:
                            self.observability.emit(
                                "on_tool_start",
                                ToolStartEvent(call.function.name, arguments),
                            )
                        result = self.tools.call(call.function.name, **arguments)
                    except Exception as error:
                        if self.observability is not None and started is not None:
                            self.observability.emit(
                                "on_tool_error",
                                ToolErrorEvent(
                                    call.function.name,
                                    arguments,
                                    error,
                                    (perf_counter() - started) * 1000,
                                ),
                            )
                        for hook in self.hooks:
                            hook.on_tool_error(call.function.name, arguments, error, context)
                        if attempt == self.max_tool_rounds:
                            result = (
                                f"Tool '{call.function.name}' is unavailable after "
                                f"{self.max_tool_rounds} failed retries: {error}"
                            )
                        continue

                    for hook in self.hooks:
                        try:
                            hook.after_tool_call(call.function.name, arguments, result, context)
                        except Exception:
                            logger.exception("after_tool_call hook failed for tool '%s'", call.function.name)
                    serialization_succeeded = True
                    event_result = result
                    if not isinstance(result, str):
                        try:
                            result = json.dumps(result, ensure_ascii=False)
                        except Exception as error:
                            serialization_succeeded = False
                            if self.observability is not None:
                                self.observability.emit(
                                    "on_tool_error",
                                    ToolErrorEvent(
                                        call.function.name,
                                        arguments,
                                        error,
                                        (perf_counter() - started) * 1000,
                                    ),
                                )
                            for hook in self.hooks:
                                hook.on_tool_error(call.function.name, arguments, error, context)
                            result = (
                                f"Tool '{call.function.name}' result could not be serialized: "
                                f"{error}"
                            )
                    if self.observability is not None and serialization_succeeded:
                        self.observability.emit(
                            "on_tool_end",
                            ToolEndEvent(
                                call.function.name,
                                arguments,
                                event_result,
                                (perf_counter() - started) * 1000,
                            ),
                        )
                    break
                context.add_message("tool", result, tool_call_id=call.id)

