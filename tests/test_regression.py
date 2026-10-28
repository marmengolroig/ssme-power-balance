"""Regression test: every computed value must match the stored baseline.

Catches unintended changes (refactoring, library updates).  After an intended model change,
regenerate the baseline with ``python tools/update_golden.py`` and justify it in the commit.
"""

import json
from pathlib import Path

import pytest

GOLDEN = json.loads((Path(__file__).parent / "data" / "golden.json").read_text())


@pytest.mark.parametrize("mode", ["isolated", "chained"])
def test_matches_golden(mode, isolated, chained):
    res = isolated if mode == "isolated" else chained
    current = {f"{c.item} | {c.quantity}": c.computed for c in res.checks}
    assert set(current) == set(GOLDEN[mode]), "set of checks changed; regenerate the baseline if intended"
    for key, ref in GOLDEN[mode].items():
        assert current[key] == pytest.approx(ref, rel=1e-6, abs=1e-9), key
