from pathlib import Path
import json

from mysimpleagent.context.context import Context


def test_add_message():
    context = Context()

    context.add_message("user", "你好")

    assert context.messages == [{"id": 0, "role": "user", "content": "你好"}]
    assert context.id == 1

    context.add_message("assistant", "你好")
    assert context.id == 2


def test_system_prompt_is_first_message():
    context = Context(system_prompt="你是一个简洁的助手")

    context.add_message("user", "你好")

    assert context.messages == [
        {"id": 0, "role": "user", "content": "你好"},
    ]
    assert context.model_message == [
        {"role": "user", "content": "你好"},
    ]
    assert context.model_messages()[0] == {
        "role": "system",
        "content": "你是一个简洁的助手",
    }


def test_save_and_load_messages():
    context = Context()
    context.add_message("user", "你好")
    context.add_message("assistant", "你好，有什么可以帮你？")

    file_path = Path(__file__).with_name("context_messages.txt")
    context.save_to_file(str(file_path))

    lines = file_path.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0]) == {"id": 0, "role": "user", "content": "你好"}

    loaded_context = Context()
    loaded_context.load_from_file(str(file_path))

    assert loaded_context.messages == context.messages
    assert loaded_context.id == 2


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

    assert context.messages == [{"id": 0, "role": "user", "content": "已有消息"}]


def test_load_assigns_missing_ids_without_colliding_with_explicit_ids(tmp_path):
    file_path = tmp_path / "context.jsonl"
    file_path.write_text(
        '{"role": "user", "content": "missing"}\n'
        '{"id": 0, "role": "assistant", "content": "explicit"}\n',
        encoding="utf-8",
    )

    context = Context()
    context.load_from_file(str(file_path))

    assert [message["id"] for message in context.messages] == [1, 0]
    assert context.id == 2


def test_load_reassigns_duplicate_explicit_ids(tmp_path):
    file_path = tmp_path / "duplicate_ids.jsonl"
    file_path.write_text(
        '{"id": 0, "role": "user", "content": "first"}\n'
        '{"id": 0, "role": "user", "content": "second"}\n',
        encoding="utf-8",
    )

    context = Context()
    context.load_from_file(str(file_path))

    assert [message["id"] for message in context.messages] == [0, 1]
    assert len({message["id"] for message in context.messages}) == len(context.messages)
