"""Tests for the dr_rd.record_parser module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dr_rd.record_parser import parse_key_value_lines, split_records


def test_parse_key_value_lines_handles_mixed_separators_and_continuations() -> None:
    """The parser should normalize keys and combine wrapped values."""

    text = """
    Name: Alice Johnson
    Title – Director of Outreach
    Organization: Community Helpers
    Notes:
        Leads the volunteer program
        Coordinates events across the county
    """

    result = parse_key_value_lines(text)

    assert result["name"] == "Alice Johnson"
    assert result["title"] == "Director of Outreach"
    assert result["organization"] == "Community Helpers"
    assert result["notes"] == "Leads the volunteer program Coordinates events across the county"


def test_parse_key_value_lines_accumulates_repeated_keys() -> None:
    """Repeated keys should be returned as a list preserving order."""

    text = """
    Award: Service Medal
    Award: Volunteer of the Year
    Award - Community Impact Citation
    """

    result = parse_key_value_lines(text)

    assert result["award"] == [
        "Service Medal",
        "Volunteer of the Year",
        "Community Impact Citation",
    ]


def test_parse_key_value_lines_preserves_bullet_lists() -> None:
    """Bullet lines should be kept on separate lines for readability."""

    text = """
    Highlights:
      - Led the robotics team
      - Organized outreach events
      - Mentored new volunteers
    """

    result = parse_key_value_lines(text)

    assert result["highlights"] == (
        "Led the robotics team\n"
        "Organized outreach events\n"
        "Mentored new volunteers"
    )


def test_split_records_breaks_on_blank_lines() -> None:
    """Multiple records separated by blank lines should be parsed individually."""

    text = """
    Name: Jordan Smith
    Title: Captain

    Name: Priya Patel
    Title: Director of Outreach
    Award: Service Medal
    Award: Community Volunteer of the Year
    """

    records = split_records(text)

    assert len(records) == 2
    assert records[0]["name"] == "Jordan Smith"
    assert records[0]["title"] == "Captain"
    assert records[1]["name"] == "Priya Patel"
    assert records[1]["title"] == "Director of Outreach"
    assert records[1]["award"] == [
        "Service Medal",
        "Community Volunteer of the Year",
    ]
