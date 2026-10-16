from pathlib import Path
import json

from mysimpleagent.context.context import Context


def test_add_message():
    context = Context()

    context.add_message("user", "你好")

    assert context.messages == [{"role": "user", "content": "你好"}]


def test_save_and_load_messages():
    context = Context()
    context.add_message("user", "你好")
    context.add_message("assistant", "你好，有什么可以帮你？")

    file_path = Path(__file__).with_name("context_messages.txt")
    context.save_to_file(str(file_path))

    lines = file_path.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0]) == {"role": "user", "content": "你好"}

    loaded_context = Context()
    loaded_context.load_from_file(str(file_path))

    assert loaded_context.messages == context.messages


def test_load_failure_keeps_existing_messages():
    context = Context()
    context.add_message("user", "已有消息")
    file_path = Path(__file__).with_name("invalid_context_messages.txt")
    file_path.write_text('{"role": "user", "content": "新消息"}\n坏 JSON\n', encoding="utf-8")

    try:
        context.load_from_file(str(file_path))
    except json.JSONDecodeError:
        pass
    finally:
        file_path.unlink()

    assert context.messages == [{"role": "user", "content": "已有消息"}]
