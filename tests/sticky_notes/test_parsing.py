from examples.sticky_notes.agents import simple_parse


def test_simple_parse() -> None:
    parsed = simple_parse("TODO finish project by 2025-12-31")
    assert parsed.is_task
    assert parsed.dates == ["2025-12-31"]
