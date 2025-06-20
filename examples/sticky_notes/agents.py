from __future__ import annotations

import datetime as dt
import uuid
import re
from typing import Any, Iterable

from pydantic import BaseModel

from agents import Agent, function_tool, handoff, trace, Runner

from .database import (
    insert_input,
    insert_task,
    insert_note,
    search,
    init_db,
    DB_PATH,
)


class InputContext(BaseModel):
    input_id: str
    timestamp: str
    text: str


class ParsedInput(BaseModel):
    is_task: bool = False
    is_note: bool = False
    is_query: bool = False
    task_description: str | None = None
    note_content: str | None = None
    query_description: str | None = None
    topics: list[str] = []
    keywords: list[str] = []
    numbers: list[int] = []
    names: list[str] = []
    dates: list[str] = []


# --- Tool implementations ---------------------------------------------------


@function_tool
def simple_parse(text: str) -> ParsedInput:
    """Parse the raw text into a structured format."""
    lowered = text.lower()
    parsed = ParsedInput()
    parsed.is_task = "todo" in lowered or "task" in lowered
    parsed.is_note = "note" in lowered
    parsed.is_query = "?" in text

    if parsed.is_task:
        parsed.task_description = text
    if parsed.is_note:
        parsed.note_content = text
    if parsed.is_query:
        parsed.query_description = text.strip()

    parsed.numbers = [int(n) for n in re.findall(r"\b\d+\b", text)]
    parsed.names = re.findall(r"\b[A-Z][a-z]+\b", text)
    parsed.dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", text)
    parsed.keywords = [w for w in re.findall(r"\b\w+\b", text.lower()) if len(w) > 3]
    return parsed


@function_tool
def ensure_valid(parsed: ParsedInput) -> None:
    """Validate that the parsed input has at least one type set."""
    if not (parsed.is_task or parsed.is_note or parsed.is_query):
        raise ValueError("Input must be a task, note, or query")


@function_tool
def create_task_tool(context: InputContext, parsed: ParsedInput) -> str:
    """Store a task in the database."""
    task_id = f"task-{uuid.uuid4().hex[:8]}"
    desc = parsed.task_description or ""
    title = " ".join(desc.split()[:5])
    priority = "high" if "high" in desc.lower() else None
    due_date = parsed.dates[0] if parsed.dates else None
    insert_task(
        task_id,
        context.input_id,
        title,
        desc,
        priority,
        due_date,
        None,
    )
    return task_id


@function_tool
def create_note_tool(context: InputContext, parsed: ParsedInput, task_id: str | None = None) -> str:
    """Store a note in the database."""
    note_id = f"note-{uuid.uuid4().hex[:8]}"
    content = parsed.note_content or ""
    summary = " ".join(content.split()[:20])
    insert_note(
        note_id,
        context.input_id,
        task_id,
        content,
        summary,
    )
    return note_id


# --- Agents -----------------------------------------------------------------

parse_agent = Agent[InputContext](
    name="parser",
    instructions="You parse user input into structured data.",
    tools=[simple_parse, ensure_valid],
    output_type=ParsedInput,
)

query_agent = Agent[InputContext](
    name="query",
    instructions="Search existing tasks and notes.",
    tools=[],
    output_type=list[str],
)


async def run_query_agent(context: InputContext, query: str) -> list[str]:
    with trace("query"):
        return search(DB_PATH, query)


action_agent = Agent[InputContext](
    name="action",
    instructions="Create tasks or notes based on parsed input.",
    tools=[create_task_tool, create_note_tool],
)


async def process_text(text: str) -> None:
    init_db()
    for segment in [part.strip() for part in text.split(";") if part.strip()]:
        input_id = uuid.uuid4().hex[:8]
        timestamp = dt.datetime.utcnow().isoformat()
        insert_input(input_id, timestamp, segment)
        context = InputContext(input_id=input_id, timestamp=timestamp, text=segment)

        with trace("workflow"):
            parse_result = await Runner.run(parse_agent, segment, context=context)
            parsed = parse_result.final_output_as(ParsedInput)

            if parsed.is_query and parsed.query_description:
                results = await run_query_agent(context, parsed.query_description)
                print("Query results:", results)
            if parsed.is_task:
                task_id = await Runner.run(
                    action_agent,
                    {
                        "name": "create_task_tool",
                        "arguments": {"context": context, "parsed": parsed},
                    },
                    context=context,
                )
                print("Created task", task_id.final_output)
            if parsed.is_note:
                note_id = await Runner.run(
                    action_agent,
                    {
                        "name": "create_note_tool",
                        "arguments": {"context": context, "parsed": parsed},
                    },
                    context=context,
                )
                print("Created note", note_id.final_output)
