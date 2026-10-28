"""Interactive HTML cycle map: ``python -m ssme --format html -o cycle_map.html``.

The map is a schematic of the SSME staged-combustion cycle.  Pipes are coloured by fluid and drawn
with a width that grows with the reference mass flow; every component and station opens a panel
with its validation checks.  Both run modes (``isolated`` and ``chained``) and the values of the
original MATLAB scripts (:mod:`ssme.legacy`) are embedded, so the page can switch between them.

The page is a single self-contained file (the only external resource is an optional web font).
The layout below is hand-placed; ``tests/test_cycle_map.py`` checks that every component and
station of ``ssme_reference.yaml`` appears on it and that every check is attached to something.
"""

from __future__ import annotations

import json
import math
import re
from datetime import date
from importlib import resources

from . import __version__
from .cycle import Check, CycleResult, run_cycle, summary
from .legacy import original_station_flows, original_values
from .reference import Reference, load_reference
from .streams import FluidStream, GasStream

# ----------------------------------------------------------------------------- layout
# Node: id -> (type, x, y, short name).  Coordinates in the SVG viewBox (0 -16 1250 806).
NODES: dict[str, tuple[str, float, float, str]] = {
    # fuel side
    "TANKF": ("source", 40, 70, "LH2 from tank"),
    "K25": ("pump", 115, 70, "Low-pressure fuel pump"),
    "K26": ("pump", 205, 70, "High-pressure fuel pump"),
    "K64": ("valve", 290, 70, "Main fuel valve"),
    "K27": ("split", 365, 70, "Splitter K27"),
    "K35": ("split", 430, 70, "Splitter K35"),
    "K28": ("hx", 520, 30, "Nozzle coolant circuit"),
    "K36": ("valve", 520, 110, "Coolant control valve"),
    "K37": ("mixer", 610, 70, "Mixer K37"),
    "J90": ("split", 720, 70, "Splitter after K37"),
    "MCCJ": ("hx", 440, 200, "Chamber coolant jacket"),
    "K34": ("turbine", 540, 200, "Low-pressure fuel turbine"),
    "HGM": ("manifold", 640, 200, "Hot-gas manifold coolant"),
    "K38": ("valve", 720, 390, "Oxidizer preburner fuel valve"),
    # hot gas
    "K45": ("burner", 800, 310, "Fuel preburner"),
    "HPFT": ("gasturbine", 900, 310, "High-pressure fuel turbine"),
    "K49": ("mixer", 1000, 310, "Mixer K49"),
    "K40": ("burner", 720, 470, "Oxidizer preburner"),
    "K41": ("gasturbine", 830, 470, "High-pressure oxidizer turbine"),
    "D5153": ("duct", 915, 470, "Duct S51 to S53"),
    "K48": ("mixer", 1000, 470, "Mixer K48"),
    "K50": ("chamber", 1100, 390, "Main combustion chamber"),
    "NOZ": ("nozzle", 1180, 390, "Nozzle"),
    # oxidizer side
    "TANKO": ("source", 40, 650, "LOX from tank"),
    "K10": ("pump", 115, 650, "Low-pressure oxidizer pump"),
    "K12": ("mixer", 200, 650, "Mixer K12"),
    "K13": ("pump", 285, 650, "High-pressure oxidizer pump"),
    "K14": ("split", 365, 650, "Splitter K14"),
    "K15": ("turbine", 365, 740, "Low-pressure oxidizer turbine"),
    "K11": ("duct", 200, 740, "Duct K11"),
    "K66": ("split", 440, 650, "Splitter K66"),
    "K16": ("split", 520, 650, "Splitter K16"),
    "K18": ("pump", 600, 650, "Preburner boost pump"),
    "K19": ("split", 680, 650, "Splitter K19"),
    "K61": ("valve", 760, 650, "Oxidizer preburner valve K61"),
    "K20": ("valve", 840, 650, "Oxidizer preburner valve K20"),
    "K67": ("hx", 520, 740, "Oxidizer heat exchanger"),
    "K70": ("valve", 610, 740, "Pressurant valve"),
    "GOX": ("sink", 690, 740, "GOX to tank pressurisation"),
}

# Edge: (station, kind, polyline).  kind: fuel | ox | pbgas (preburner gas) | mccgas (chamber gas)
EDGES: list[tuple[str, str, list[tuple[float, float]]]] = [
    ("S31", "fuel", [(40, 70), (115, 70)]),
    ("S32", "fuel", [(115, 70), (205, 70)]),
    ("S33", "fuel", [(205, 70), (290, 70)]),
    ("S58", "fuel", [(290, 70), (365, 70)]),
    ("S34", "fuel", [(365, 70), (430, 70)]),
    ("S41", "fuel", [(365, 70), (365, 200), (440, 200)]),
    ("S87", "fuel", [(430, 70), (430, 30), (520, 30)]),
    ("S88", "fuel", [(430, 70), (430, 110), (520, 110)]),
    ("S36", "fuel", [(520, 30), (610, 30), (610, 70)]),
    ("S89", "fuel", [(520, 110), (610, 110), (610, 70)]),
    ("S90", "fuel", [(610, 70), (720, 70)]),
    ("S43", "fuel", [(440, 200), (540, 200)]),
    ("S44", "fuel", [(540, 200), (640, 200)]),
    ("S72", "fuel", [(640, 200), (1000, 200), (1000, 310)]),
    ("S79", "fuel", [(640, 200), (640, 240), (1050, 240), (1050, 380), (1100, 380)]),
    ("S71", "fuel", [(640, 200), (640, 520), (1000, 520), (1000, 470)]),
    ("S38", "fuel", [(720, 70), (800, 70), (800, 310)]),
    ("S39", "fuel", [(720, 70), (720, 390)]),
    ("S40", "fuel", [(720, 390), (720, 470)]),
    ("S55", "pbgas", [(800, 310), (900, 310)]),
    ("S56", "pbgas", [(900, 310), (1000, 310)]),
    ("S59", "pbgas", [(1000, 310), (1100, 310), (1100, 390)]),
    ("S50", "pbgas", [(720, 470), (830, 470)]),
    ("S51", "pbgas", [(830, 470), (915, 470)]),
    ("S53", "pbgas", [(915, 470), (1000, 470)]),
    ("S54", "pbgas", [(1000, 470), (1065, 470), (1065, 405), (1100, 405)]),
    ("S63", "mccgas", [(1100, 390), (1180, 390)]),
    ("S68", "mccgas", [(1200, 390), (1248, 390)]),
    ("S11", "ox", [(40, 650), (115, 650)]),
    ("S12", "ox", [(115, 650), (200, 650)]),
    ("S13", "ox", [(200, 650), (285, 650)]),
    ("S14", "ox", [(285, 650), (365, 650)]),
    ("S15", "ox", [(365, 650), (365, 740)]),
    ("S160", "ox", [(365, 740), (200, 740)]),
    ("S162", "ox", [(200, 740), (200, 650)]),
    ("S17", "ox", [(365, 650), (440, 650)]),
    ("S29", "ox", [(440, 650), (520, 650)]),
    ("S74", "ox", [(440, 650), (440, 740), (520, 740)]),
    ("S80", "ox", [(520, 740), (610, 740)]),
    ("S69", "ox", [(610, 740), (690, 740)]),
    ("S18", "ox", [(520, 650), (520, 595), (1120, 595), (1120, 390)]),
    ("S20", "ox", [(520, 650), (600, 650)]),
    ("S21", "ox", [(600, 650), (680, 650)]),
    ("S24", "ox", [(680, 650), (680, 330), (800, 330)]),
    ("S22", "ox", [(680, 650), (760, 650)]),
    ("S26", "ox", [(760, 650), (840, 650)]),
    ("S23", "ox", [(840, 650), (840, 545), (735, 545), (735, 470)]),
]

# Text drawn next to each node, and where: "below" (default), "above", "inside", "left", "right", "none".
TAGS: dict[str, tuple[str, str]] = {
    "TANKF": ("LH2", "below"), "K25": ("K25 LPFP", "below"), "K26": ("K26 HPFP", "below"), "K64": ("K64 MFV", "below"),
    "K27": ("K27", "above"), "K35": ("K35", "right"), "K28": ("K28 nozzle HX", "above"), "K36": ("K36 CCV", "below"),
    "K37": ("K37", "right"), "J90": ("", "none"), "MCCJ": ("Jacket", "below"), "K34": ("K34 LPFT", "below"),
    "HGM": ("Hot-gas manifold", "above"), "K38": ("K38", "left"), "K45": ("FPB", "inside"), "HPFT": ("HPFT", "below"),
    "K49": ("K49", "below"), "K40": ("OPB", "inside"), "K41": ("K41 HPOT", "below"), "D5153": ("duct", "above"),
    "K48": ("K48", "above"), "K50": ("MCC", "inside"), "NOZ": ("Nozzle", "below"), "TANKO": ("LOX", "below"),
    "K10": ("K10 LPOP", "above"), "K12": ("K12", "above"), "K13": ("K13 HPOP", "above"), "K14": ("K14", "above"),
    "K15": ("K15 LPOT", "below"), "K11": ("K11", "below"), "K66": ("K66", "above"), "K16": ("K16", "below"),
    "K18": ("K18 PBP", "above"), "K19": ("K19", "below"), "K61": ("K61", "below"), "K20": ("K20", "below"),
    "K67": ("K67 ox HX", "below"), "K70": ("K70", "below"), "GOX": ("GOX", "below"),
}

#: Edges that are not part of the computation (drawn dashed).
NOT_MODELLED_EDGES = {
    "S71": "LPFT exhaust to the hot-gas manifold coolant is not modelled: the state is the reference one",
    "S72": "LPFT exhaust to the hot-gas manifold coolant is not modelled: the state is the reference one",
    "S79": "LPFT exhaust to the hot-gas manifold coolant is not modelled: the state is the reference one",
}

# Hand-placed station labels where the automatic spot (middle of the longest segment) collides: (x, y, anchor).
LABEL_AT = {"S24": (686, 425, "start"), "S23": (787, 538, "middle"), "S71": (945, 513, "middle")}

#: Stations inside a component rather than on a pipe: station -> node that shows them.
INTERNAL_STATIONS = {"S62": "K50"}  # chamber station at the injector end (225.1 bar)

# Flows of stations that are not in the YAML (only drawn).
EXTRA_FLOWS = {"S26": 13.56}

# Check item -> node id.
ITEM_TARGETS = {
    "K25 LPFP": "K25", "K26 HPFP": "K26", "K64 MFV": "K64", "K28 nozzle HX": "K28", "K36 CCV": "K36",
    "K37 mixer": "K37", "MCC coolant jacket": "MCCJ", "K34 LPFT": "K34", "K38 OPB fuel valve": "K38",
    "K10 LPOP": "K10", "K12 mixer": "K12", "K13 HPOP": "K13", "K15 LPOT": "K15", "K18": "K18",
    "K67 ox HX": "K67", "K70 valve": "K70", "K61+K20 valves": "K20", "K45 fuel preburner": "K45", "HPFT": "HPFT",
    "K49 mixer": "K49", "K40 ox preburner": "K40", "K41 HPOT": "K41", "duct S51-S53": "D5153", "K48 mixer": "K48",
    "K50 MCC": "K50", "nozzle": "NOZ",
}
MASS_TARGETS = {"S90 split": "J90", "K45 FPB": "K45", "K40 OPB": "K40", "K50 MCC": "K50"}

_STATION_RE = re.compile(r"\b(S\d+)\b")


def check_targets(c: Check, ref: Reference) -> list[str]:
    """Nodes and stations a check belongs to (used to colour the map and fill the panels)."""
    item = c.item
    out: list[str] = []
    if item.startswith("rho "):
        out.append(item.split()[1])
    elif item.startswith("shaft "):
        shaft = item.split()[1]
        d = ref.shafts[shaft]
        out += list(d["pumps"]) + list(d["turbines"])
    elif item.startswith("mass "):
        rest = item[5:]
        node = MASS_TARGETS.get(rest) or (rest if rest in NODES else None)
        out.append(node or "ENGINE")
    else:
        best = max((k for k in ITEM_TARGETS if item.startswith(k)), key=len, default=None)
        out.append(ITEM_TARGETS[best] if best else "ENGINE")
    m = _STATION_RE.search(c.quantity)
    if m and m.group(1) not in out:
        out.append(m.group(1))
    return out


def stroke_width(m_dot: float) -> float:
    """Pipe width in viewBox units: grows with the square root of the mass flow (0.5 kg/s -> 1.3, 500 kg/s -> 11)."""
    return round(1.0 + 0.45 * math.sqrt(max(m_dot, 0.0)), 2)


# ----------------------------------------------------------------------------- data
def _r(x: float | None, nd: int = 6) -> float | None:
    return None if x is None else float(round(x, nd))


def _check_dict(c: Check, ref: Reference, original: dict | None = None) -> dict:
    d = {
        "group": c.group,
        "item": c.item,
        "quantity": c.quantity,
        "computed": _r(c.computed),
        "reference": _r(c.reference),
        "unit": c.unit,
        "error": _r(c.error),
        "rel": _r(c.rel_error, 8),
        "passed": c.passed,
        "criterion": c.criterion,
        "note": c.note,
        "targets": check_targets(c, ref),
    }
    if original is not None:
        d["original"] = original
    return d


def _state(s) -> dict | None:
    if s is None:
        return None
    d = {"P": _r(s.P), "T": _r(s.T), "m_dot": _r(s.m_dot), "rho": _r(s.rho)}
    if isinstance(s, GasStream):
        fr = s.mix.mass_fractions()
        d["composition"] = {k: round(v, 6) for k, v in sorted(fr.items(), key=lambda kv: -kv[1]) if v > 1e-5}
    elif isinstance(s, FluidStream):
        d["fluid"] = s.fluid.table
    return d


def _original_check(item: str, quantity: str, value, ref: Reference, model_check: Check | None) -> dict:
    """The original value judged with the same acceptance criteria as the model."""
    acc = ref.acceptance
    out = {"value": _r(value.value), "status": value.status, "note": value.note, "passed": None}
    if value.status != "computed" or value.value is None or model_check is None or model_check.reference is None:
        return out
    unit = model_check.unit
    if model_check.bounds is not None:  # nozzle: the original is a single value, judged like any other output
        tol = {"T": acc["T_rel"], "v": acc["v_rel"], "M": acc["M_rel"]}[quantity[0]]
        c = Check("system", item, quantity, value.value, model_check.reference, unit, tol_rel=tol)
    else:
        c = Check(model_check.group, item, quantity, value.value, model_check.reference, unit,
                  tol_abs=model_check.tol_abs, tol_rel=model_check.tol_rel)
    out.update(passed=c.passed, error=_r(c.error), rel=_r(c.rel_error, 8), criterion=c.criterion)
    return out


def build_data(results: dict[str, CycleResult], reference: Reference | None = None) -> dict:
    """Everything the page needs, as plain JSON-serialisable data."""
    first = next(iter(results.values()))
    ref = reference or load_reference(hydrogen_table=first.hydrogen_table, backend=first.backend)
    orig = original_values(ref.backend)
    modes = {}
    for mode, res in results.items():
        checks = []
        for c in res.checks:
            ov = orig.get((c.item, c.quantity))
            checks.append(_check_dict(c, ref, _original_check(c.item, c.quantity, ov, ref, c) if ov else None))
        states = {k: _state(v) for k, v in res.states.items() if k in ref.stations}
        modes[mode] = {"summary": summary(res), "checks": checks, "states": states,
                       "lox_loop_iterations": res.extras.get("lox_loop_iterations", {}).get("n")}
    # summary of the original scripts, on the checks where they produce a value
    some = next(iter(modes.values()))["checks"]
    o = [c["original"] for c in some if "original" in c]
    orig_summary = {"pass": sum(x["passed"] is True for x in o), "fail": sum(x["passed"] is False for x in o),
                    "imposed": sum(x["status"] == "imposed" for x in o),
                    "not_modelled": sum(x["status"] == "not_modelled" for x in o)}
    stations = {}
    for name, st in ref.stations.items():
        stations[name] = {k: st.get(k) for k in ("fluid", "m_dot", "P", "T", "rho", "v", "M", "note")}
    flows = {**{k: v["m_dot"] for k, v in stations.items()}, **EXTRA_FLOWS}
    components = {}
    for cid, (ntype, *_rest, name) in NODES.items():
        comp = dict(ref.components.get(cid, {}))
        params = {k: comp[k] for k in ("eta", "PR", "Q", "W_ref") if k in comp}
        shaft = next((s for s, d in ref.shafts.items() if cid in d["pumps"] or cid in d["turbines"]), None)
        tag, tag_pos = TAGS.get(cid, (cid, "below"))
        components[cid] = {"type": ntype, "name": name, "note": comp.get("note", ""), "params": params, "shaft": shaft,
                           "tag": tag, "tag_pos": tag_pos}
    return {
        "meta": {
            "title": "SSME cycle map",
            "generated": date.today().isoformat(),
            "version": __version__,
            "hydrogen": first.hydrogen_table,
            "backend": first.backend,
            "nozzle": first.nozzle_model,
            "acceptance": ref.acceptance,
            "original_summary": orig_summary,
            "original_flows": original_station_flows(),
        },
        "modes": modes,
        "stations": stations,
        "components": components,
        "shafts": ref.shafts,
        "data_issues": ref.raw.get("data_issues", []),
        "layout": {
            "viewBox": [0, -16, 1250, 806],
            "nodes": {k: {"type": t, "x": x, "y": y} for k, (t, x, y, _n) in NODES.items()},
            "edges": [{"id": s, "kind": k, "points": pts, "width": stroke_width(flows.get(s, 1.0)),
                       "not_modelled": NOT_MODELLED_EDGES.get(s), "label": LABEL_AT.get(s)} for s, k, pts in EDGES],
        },
    }


def render(results: dict[str, CycleResult], reference: Reference | None = None) -> str:
    """The complete HTML page."""
    template = resources.files("ssme").joinpath("templates/cycle_map.html").read_text(encoding="utf-8")
    payload = json.dumps(build_data(results, reference), ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")  # keep "</script>" out of the inline JSON
    return template.replace("/*__SSME_DATA__*/null", payload)


def cycle_map_html(*, hydrogen_table: str | None = None, backend: str = "nfp", nozzle_model: str = "shifting") -> str:
    """Run both modes and render the map (what ``python -m ssme --format html`` does)."""
    results = {m: run_cycle(m, hydrogen_table=hydrogen_table, backend=backend, nozzle_model=nozzle_model)
               for m in ("isolated", "chained")}
    return render(results)
