"""Command-line entry point: ``python -m ssme [options]``.

Examples::

    python -m ssme                                  # isolated components, para-H2, NIST tables
    python -m ssme --mode chained                   # propagate states through the cycle
    python -m ssme --hydrogen H2                    # normal hydrogen (what the MATLAB code used)
    python -m ssme --backend coolprop               # CoolProp instead of the NIST tables
    python -m ssme --format md -o docs/VALIDATION_REPORT.md
    python -m ssme --format html -o cycle_map.html   # interactive cycle map (both modes)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .cycle import run_cycle, summary
from .report import to_csv, to_markdown


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m ssme", description="SSME power-balance model and validation report")
    ap.add_argument("--mode", choices=["isolated", "chained"], default="isolated")
    ap.add_argument("--hydrogen", choices=["pH2", "H2"], default=None, help="para (default) or normal hydrogen")
    ap.add_argument("--backend", choices=["nfp", "coolprop"], default="nfp", help="real-fluid property backend")
    ap.add_argument("--nozzle", choices=["shifting", "frozen_throat", "frozen"], default="shifting")
    ap.add_argument("--format", choices=["md", "csv", "summary", "html"], default="md",
                    help="html: interactive cycle map with both run modes (--mode is ignored)")
    ap.add_argument("-o", "--output", type=Path, default=None)
    ap.add_argument("--strict", action="store_true", help="exit with status 1 if any check fails")
    args = ap.parse_args(argv)

    if args.format == "html":
        from .cycle_map import cycle_map_html

        text = cycle_map_html(hydrogen_table=args.hydrogen, backend=args.backend, nozzle_model=args.nozzle)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(text, encoding="utf-8")
        else:
            sys.stdout.write(text)
        return 0
    res = run_cycle(args.mode, hydrogen_table=args.hydrogen, backend=args.backend, nozzle_model=args.nozzle)
    if args.format == "md":
        text = to_markdown(res)
    elif args.format == "csv":
        text = to_csv(res)
    else:
        s = summary(res)
        text = f"{res.mode} / {res.hydrogen_table} / {res.backend}: {s['pass']} pass, {s['fail']} fail, {s['info']} info\n"
        text += "".join(f"  FAIL {c.item}: {c.quantity}\n" for c in res.failed)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    else:
        sys.stdout.write(text)
    return 1 if (args.strict and res.failed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
