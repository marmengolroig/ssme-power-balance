"""The interactive cycle map (``python -m ssme --format html``) and the original-script values behind it."""

import json
import re

import pytest

from ssme import cycle_map as M
from ssme.__main__ import main
from ssme.legacy import original_values
from ssme.reference import load_reference

REF = load_reference()


@pytest.fixture(scope="module")
def page(isolated, chained):
    return M.render({"isolated": isolated, "chained": chained})


def _payload(html: str) -> dict:
    m = re.search(r"const DATA = (\{.*?\});\n", html, re.S)
    assert m, "embedded data not found"
    return json.loads(m.group(1))


def test_every_component_and_station_is_on_the_map():
    heat_only = {k for k, v in REF.components.items() if v["type"] == "heat"}  # K52, K53: heat flows, not hardware
    assert set(REF.components) - heat_only <= set(M.NODES)
    assert set(REF.stations) <= {e[0] for e in M.EDGES} | set(M.INTERNAL_STATIONS)
    assert set(M.INTERNAL_STATIONS.values()) <= set(M.NODES)
    assert set(M.TAGS) == set(M.NODES)


def test_pipes_start_and_end_on_nodes():
    centres = [(x, y) for _t, x, y, _n in M.NODES.values()]

    def on_node(p):  # inside the drawn body of a node (the main chamber is the largest, 52 x 68)
        return any(abs(p[0] - x) <= 26 and abs(p[1] - y) <= 34 for x, y in centres)

    for station, _kind, pts in M.EDGES:
        assert on_node(pts[0]), station
        if station != "S68":  # the nozzle exit points out of the engine
            assert on_node(pts[-1]), station
        assert all(a[0] == b[0] or a[1] == b[1] for a, b in zip(pts, pts[1:])), f"{station}: not orthogonal"


@pytest.mark.parametrize("mode", ["isolated", "chained"])
def test_every_check_is_attached_to_the_map(mode, isolated, chained):
    res = isolated if mode == "isolated" else chained
    known = set(M.NODES) | set(REF.stations) | {"ENGINE"}
    for c in res.checks:
        targets = M.check_targets(c, REF)
        assert targets and set(targets) <= known, (c.item, c.quantity, targets)
    on_engine = [c.item for c in res.checks if M.check_targets(c, REF) == ["ENGINE"]]
    assert set(on_engine) <= {"mass engine H2", "mass engine O2"}


def test_page_embeds_both_modes_and_the_original_values(page, isolated):
    assert "/*__SSME_DATA__*/" not in page
    data = _payload(page)
    assert set(data["modes"]) == {"isolated", "chained"}
    assert data["modes"]["isolated"]["summary"] == {"pass": 88, "fail": 4, "info": 15}
    rows = {(c["item"], c["quantity"]): c for c in data["modes"]["isolated"]["checks"]}
    assert rows[("K41 HPOT", "W")]["original"]["passed"] is False  # pure H2 turbine: -39 MW
    assert rows[("K45 fuel preburner", "T(S55)")]["original"]["status"] == "imposed"
    assert rows[("HPFT", "W")]["original"]["status"] == "not_modelled"
    assert data["meta"]["original_summary"]["fail"] > data["modes"]["isolated"]["summary"]["fail"]
    assert "Soria" in page and "Fuster" in page  # credit in the footer


def test_original_values_reproduce_the_code_review_numbers():
    ov = original_values()
    # FIX(2): pressure ratios applied as P_in*(2-deltaP)
    assert ov[("K28 nozzle HX", "P(S36)")].value == pytest.approx(429.03, abs=0.01)
    assert ov[("K67 ox HX", "P(S80)")].value == pytest.approx(278.49, abs=0.01)
    assert ov[("K61+K20 valves", "P(S23)")].value == pytest.approx(356.02, abs=0.01)
    assert ov[("K38 OPB fuel valve", "P(S40)")].value == pytest.approx(382.22, abs=0.01)
    # FIX(1): normal hydrogen makes the nozzle coolant ~31 K too hot; FIX(5): HPOT as pure H2
    assert ov[("K28 nozzle HX", "T(S36)")].value == pytest.approx(289.4, abs=0.3)
    assert ov[("K41 HPOT", "W")].value == pytest.approx(-39074, abs=5)
    # FIX(6): combustor temperatures were inputs
    combustors = [("K45 fuel preburner", "T(S55)"), ("K40 ox preburner", "T(S50)"), ("K50 MCC", "T(S63)")]
    assert {ov[k].status for k in combustors} == {"imposed"}


def test_command_line_writes_the_map(tmp_path):
    out = tmp_path / "map.html"
    assert main(["--format", "html", "-o", str(out)]) == 0
    html = out.read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>") and "<title>SSME cycle map</title>" in html
    assert html.count("</script>") == 1  # the embedded JSON cannot close the script element
