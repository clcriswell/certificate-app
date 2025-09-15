import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from LegAid.utils.shared_functions import extract_json_block


def test_extract_json_block_from_code_fence():
    content = """
    ```json
    {"foo": [1, 2, 3]}
    ```
    Extra commentary.
    """

    cleaned = extract_json_block(content)
    assert json.loads(cleaned) == {"foo": [1, 2, 3]}


def test_extract_json_block_skips_non_json_curly_section():
    content = "Sure, here is what I found {not real json}. {\"valid\": true}"

    cleaned = extract_json_block(content)
    assert json.loads(cleaned) == {"valid": True}


def test_extract_json_block_reports_truncated_content():
    with pytest.raises(ValueError) as excinfo:
        extract_json_block("Result begins { but never ends")

    assert "truncated" in str(excinfo.value)
