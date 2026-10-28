"""Regenerate tests/data/golden.json (regression baseline of every computed value).

Run this only after an *intended* model change, and explain the change in the commit message:

    python tools/update_golden.py
"""

import json
from pathlib import Path

from ssme.cycle import run_cycle

OUT = Path(__file__).resolve().parents[1] / "tests" / "data" / "golden.json"


def snapshot() -> dict:
    data = {}
    for mode in ("isolated", "chained"):
        res = run_cycle(mode, hydrogen_table="pH2", backend="nfp", nozzle_model="shifting")
        data[mode] = {f"{c.item} | {c.quantity}": c.computed for c in res.checks}
    return data


if __name__ == "__main__":
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot(), indent=1, sort_keys=True))
    print("written", OUT)
