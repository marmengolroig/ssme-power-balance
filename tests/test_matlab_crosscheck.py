"""Code-to-code verification of the Python port against the corrected MATLAB model.

Run ``legacy/matlab/fixed/export_results.m`` in MATLAB (with HGS and INIST on the path); it writes
``legacy/matlab/results/matlab_results.json``.  This test then compares every exported value
with the Python ``isolated`` run.  Skipped until that file exists.

Expected agreement: identical data and formulas, so differences come only from the solvers
(NFP's fsolve, HGS's fmincon/secant tolerances).
"""

import json
from pathlib import Path

import pytest

RESULTS = Path(__file__).resolve().parents[1] / "legacy" / "matlab" / "results" / "matlab_results.json"

# MATLAB key -> (Python check item, quantity, absolute tolerance, relative tolerance)
MAP = {
    "T32": ("K25 LPFP", "T(S32)", 0.01, None), "K25_W": ("K25 LPFP", "W", None, 1e-4),
    "T33": ("K26 HPFP", "T(S33)", 0.01, None), "K26_W": ("K26 HPFP", "W", None, 1e-4),
    "T58": ("K64 MFV", "T(S58)", 0.01, None),
    "T36": ("K28 nozzle HX", "T(S36)", 0.01, None), "P36": ("K28 nozzle HX", "P(S36)", None, 1e-9),
    "T89": ("K36 CCV", "T(S89)", 0.01, None), "T90": ("K37 mixer", "T(S90)", 0.01, None),
    "T43": ("MCC coolant jacket", "T(S43)", 0.01, None),
    "T44": ("K34 LPFT", "T(S44)", 0.01, None), "K34_W": ("K34 LPFT", "W", None, 1e-4),
    "P40": ("K38 OPB fuel valve", "P(S40)", None, 1e-9), "T40": ("K38 OPB fuel valve", "T(S40)", 0.01, None),
    "T12": ("K10 LPOP", "T(S12)", 0.01, None), "K10_W": ("K10 LPOP", "W", None, 1e-4),
    "T13": ("K12 mixer", "T(S13)", 0.01, None),
    "T14": ("K13 HPOP", "T(S14)", 0.01, None), "K13_W": ("K13 HPOP", "W", None, 1e-4),
    "T160": ("K15 LPOT", "T(S160)", 0.01, None), "K15_W": ("K15 LPOT", "W", None, 1e-4),
    "T21": ("K18", "T(S21)", 0.01, None), "K18_W": ("K18", "W", None, 1e-4),
    "T80": ("K67 ox HX", "T(S80)", 0.01, None), "P80": ("K67 ox HX", "P(S80)", None, 1e-9),
    "T69": ("K70 valve", "T(S69)", 0.01, None), "rho69": ("K70 valve", "rho(S69)", None, 1e-4),
    "T23": ("K61+K20 valves", "T(S23)", 0.01, None), "P23": ("K61+K20 valves", "P(S23)", None, 1e-9),
    "T55": ("K45 fuel preburner", "T(S55)", 0.5, None),
    "HPFT_W": ("HPFT", "W", None, 1e-3), "HPFT_eta": ("HPFT", "eta (implied)", None, 1e-3),
    "T59": ("K49 mixer", "T(S59)", 0.5, None), "T50": ("K40 ox preburner", "T(S50)", 0.5, None),
    "T51": ("K41 HPOT", "T(S51)", 0.5, None), "K41_W": ("K41 HPOT", "W", None, 1e-3),
    "T54": ("K48 mixer", "T(S54)", 0.5, None),
    "T_ad_MCC": ("K50 MCC", "T_ad at P(S62), no heat loss", 1.0, None), "T63_loss": ("K50 MCC", "T(S63)", 1.0, None),
    "T68": ("nozzle shifting", "T(S68)", 2.0, None), "v68": ("nozzle shifting", "v(S68)", None, 2e-3),
    "M68": ("nozzle shifting", "M(S68)", None, 3e-3),
}

pytestmark = pytest.mark.skipif(not RESULTS.exists(), reason="run legacy/matlab/fixed/export_results.m first")


def _load():
    return json.loads(RESULTS.read_text())


@pytest.mark.parametrize("key", sorted(MAP))
def test_python_matches_matlab(key, isolated):
    data = _load()
    if key not in data:
        pytest.skip(f"{key} not exported by MATLAB")
    item, q, atol, rtol = MAP[key]
    py = isolated.check(item, q).computed
    assert py == pytest.approx(data[key], abs=atol, rel=rtol), f"{key}: Python {py} vs MATLAB {data[key]}"
