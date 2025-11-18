"""Helpers to convert learning logger records into human-friendly messages."""

from __future__ import annotations

from typing import Iterable, List, Sequence


def format_record_label(record: dict) -> str:
    phase = (record.get("phase") or "").strip()
    if phase == "step":
        idx = record.get("step_index")
        if isinstance(idx, int):
            return f"step{idx}"
    if phase:
        return phase
    return "record"


def _status_label(value: str | None) -> str:
    if not value:
        return "UNKNOWN"
    value = value.strip()
    if not value:
        return "UNKNOWN"
    if value.lower() == "ok":
        return "OK"
    return value.upper()


def _expression_for(record: dict) -> str:
    expr = record.get("expression")
    if expr:
        return expr
    rendered = record.get("rendered")
    if rendered:
        return rendered
    return ""


def format_record_message(record: dict, *, include_meta: bool = True) -> List[str]:
    """Format a single record into one or more textual lines."""

    label = format_record_label(record)
    expr = _expression_for(record)
    status = _status_label(record.get("status"))
    base = f"[{label}] {expr}".rstrip()
    if expr:
        base = f"{base} [{status}]"
    else:
        base = f"[{label}] [{status}]"
    lines: List[str] = [base]
    if not include_meta:
        return lines
    meta = record.get("meta") or {}
    reason = meta.get("reason")
    if reason:
        lines.append(f"[message] {reason}")
    explanation = meta.get("explanation")
    if explanation:
        lines.append(f"[explain] {explanation}")
    expected = meta.get("expected")
    if expected:
        lines.append(f"[expected] {expected}")
    return lines


def format_records(records: Sequence[dict], *, include_meta: bool = True) -> List[str]:
    """Format all learning records into textual lines."""

    lines: List[str] = []
    for record in records:
        lines.extend(format_record_message(record, include_meta=include_meta))
    return lines


def print_formatted_records(records: Sequence[dict], *, include_meta: bool = True) -> None:
    """Convenience printer that sends formatted lines to stdout."""

    for line in format_records(records, include_meta=include_meta):
        print(line)
