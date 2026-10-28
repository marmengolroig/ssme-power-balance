"""Render validation results as Markdown or CSV."""

from __future__ import annotations

import csv
import io
from datetime import date

from .cycle import Check, CycleResult, summary

GROUP_TITLES = {
    "component": "Component validation",
    "system": "System-level validation",
    "balance": "Mass and shaft-power balances",
    "data": "Reference-data consistency",
    "property": "Property model vs reference densities",
    "info": "Additional results (no acceptance criterion)",
}
STATUS = {True: "PASS", False: "**FAIL**", None: "info"}


def _fmt(x: float | None, nd: int = 2) -> str:
    if x is None:
        return ""
    ax = abs(x)
    if ax != 0 and (ax < 1e-2 or ax >= 1e6):
        return f"{x:.4g}"
    return f"{x:.{nd}f}"


def _row(c: Check) -> list[str]:
    rel = "" if c.rel_error is None else f"{100 * c.rel_error:+.2f} %"
    return [
        STATUS[c.passed],
        c.item,
        c.quantity,
        _fmt(c.computed, 3 if abs(c.computed) < 10 else 2),
        _fmt(c.reference, 3 if c.reference is not None and abs(c.reference) < 10 else 2),
        c.unit,
        _fmt(c.error),
        rel,
        c.criterion,
        c.note,
    ]


HEADER = ["Status", "Item", "Quantity", "Computed", "Reference", "Unit", "Error", "Rel. error", "Criterion", "Note"]


def to_markdown(res: CycleResult, *, title: str | None = None) -> str:
    s = summary(res)
    out = io.StringIO()
    out.write(f"# {title or 'SSME cycle - validation report'}\n\n")
    out.write(
        f"- Mode: **{res.mode}**  |  hydrogen: **{res.hydrogen_table}**  |  real-fluid backend: **{res.backend}**"
        f"  |  nozzle model: **{res.nozzle_model}**\n"
    )
    out.write(f"- Checks: {s['pass']} pass, {s['fail']} fail, {s['info']} informative\n")
    out.write(f"- Generated: {date.today().isoformat()} with `python -m ssme`\n\n")
    if res.failed:
        out.write("## Failed checks\n\n")
        for c in res.failed:
            rel = "" if c.rel_error is None else f" ({100 * c.rel_error:+.2f} %)"
            out.write(f"- {c.item} - {c.quantity}: {_fmt(c.computed)} vs {_fmt(c.reference)} {c.unit}{rel}\n")
        out.write("\n")
    for group, title_ in GROUP_TITLES.items():
        rows = [c for c in res.checks if c.group == group]
        if not rows:
            continue
        out.write(f"## {title_}\n\n")
        out.write("| " + " | ".join(HEADER) + " |\n")
        out.write("|" + "|".join(["---"] * len(HEADER)) + "|\n")
        for c in rows:
            out.write("| " + " | ".join(x.replace("|", "/") for x in _row(c)) + " |\n")
        out.write("\n")
    k50 = res.extras.get("K50")
    if k50:
        out.write("## Main chamber composition (mass fractions)\n\n")
        out.write(", ".join(f"{k}: {v:.4f}" for k, v in k50["mass_fractions"].items()) + "\n")
    return out.getvalue()


def to_csv(res: CycleResult) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["group"] + HEADER)
    for c in res.checks:
        w.writerow([c.group] + [x.replace("**", "") for x in _row(c)])
    return buf.getvalue()
