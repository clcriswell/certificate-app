"""Helpers for parsing loosely structured key-value records."""

from __future__ import annotations

import re
from typing import Callable, Dict, List, MutableMapping

Value = str | List[str]
Normalizer = Callable[[str], str]

_BULLET_PATTERN = re.compile(
    r"""
    ^(
        (?:[\-\*\u2022\u2023\u2043]+)    # bullet characters
        |
        (?:\d+\.)                        # numbered list
        |
        (?:[A-Za-z]\))                    # alpha enumerations
    )\s+
    """,
    re.VERBOSE,
)

_DASH_SEPARATOR = re.compile(r"\s[-–—]\s")


def _default_normalizer(key: str) -> str:
    cleaned = re.sub(r"[^0-9a-z]+", "_", key.lower())
    return cleaned.strip("_")


def _strip_bullet(line: str) -> tuple[str, bool]:
    stripped = line.lstrip()
    match = _BULLET_PATTERN.match(stripped)
    if match:
        return stripped[match.end() :], True
    return stripped, False


def _extract_key_value(line: str) -> tuple[str, str, bool] | None:
    candidate, was_bullet = _strip_bullet(line)
    if not candidate.strip():
        return None

    for sep in (":", "="):
        if sep in candidate:
            key, value = candidate.split(sep, 1)
            key = key.strip()
            if not key:
                continue
            return key, value.strip(), was_bullet

    dash_match = _DASH_SEPARATOR.search(candidate)
    if dash_match:
        key = candidate[: dash_match.start()].strip()
        value = candidate[dash_match.end() :].strip()
        if key:
            return key, value, was_bullet

    return None


def parse_key_value_lines(
    text: str,
    *,
    key_normalizer: Normalizer | None = None,
) -> Dict[str, Value]:
    """Parse a block of text into a dictionary of normalized keys.

    Lines that begin with bullet characters or numbering are treated as
    continuations of the previous key unless they contain a recognised
    separator. Repeated keys produce a list preserving the order of the
    values encountered.
    """

    normalizer = key_normalizer or _default_normalizer
    aggregated: MutableMapping[str, List[str]] = {}
    current_key: str | None = None

    for raw_line in text.splitlines():
        if not raw_line.strip():
            current_key = None
            continue

        parsed = _extract_key_value(raw_line)
        if parsed:
            key_text, value_text, _ = parsed
            norm_key = normalizer(key_text)
            if not norm_key:
                current_key = None
                continue

            bucket = aggregated.setdefault(norm_key, [])
            if value_text:
                bucket.append(value_text)
            else:
                bucket.append("")
            current_key = norm_key
            continue

        if current_key is None:
            continue

        continuation, is_bullet = _strip_bullet(raw_line)
        continuation = continuation.strip()
        if not continuation:
            continue

        bucket = aggregated[current_key]
        if not bucket:
            bucket.append(continuation)
            continue

        last = bucket[-1]
        if not last:
            bucket[-1] = continuation
        elif is_bullet:
            bucket[-1] = f"{last}\n{continuation}"
        else:
            bucket[-1] = f"{last} {continuation}".strip()

    result: Dict[str, Value] = {}
    for key, values in aggregated.items():
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            continue
        result[key] = cleaned[0] if len(cleaned) == 1 else cleaned

    return result


def split_records(
    text: str,
    *,
    key_normalizer: Normalizer | None = None,
) -> List[Dict[str, Value]]:
    """Split multi-record text into structured dictionaries.

    Blank lines delimit records. Empty records are ignored.
    """

    records: List[Dict[str, Value]] = []
    buffer: List[str] = []

    def flush() -> None:
        if not buffer:
            return
        block = "\n".join(buffer)
        parsed = parse_key_value_lines(block, key_normalizer=key_normalizer)
        if parsed:
            records.append(parsed)
        buffer.clear()

    for line in text.splitlines():
        if line.strip():
            buffer.append(line)
        else:
            flush()

    flush()
    return records

