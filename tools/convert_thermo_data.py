"""Convert the MATLAB data files of HGS and INIST into the formats used by ``ssme.thermo``.

Both upstream projects are CC0 (public domain):

* HGS   - https://github.com/ManelSoria/HGS   (NASA 7-coefficient polynomials, Burcat database)
* INIST - https://github.com/ManelSoria/INIST (NIST Webbook fluid tables)

Usage (from the repository root)::

    git clone https://github.com/ManelSoria/HGS.git   /tmp/HGS
    git clone https://github.com/ManelSoria/INIST.git /tmp/INIST
    python tools/convert_thermo_data.py --hgs /tmp/HGS --inist /tmp/INIST

The commits used to build the files shipped in ``src/ssme/thermo/data`` are recorded in
``src/ssme/thermo/data/SOURCES.json``, and every data file also carries its own provenance
(``"_source"`` in the JSON file, a ``source`` entry in each ``.npz``), so the credit travels
with the data if a file is copied on its own.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
import scipy.io as sio

OUT = Path(__file__).resolve().parents[1] / "src" / "ssme" / "thermo" / "data"

# Gas-phase species of the H/O(/N) system that the cycle model may need.
HGS_SPECIES = ["H", "H2", "O", "O2", "OH", "H2O", "HO2", "H2O2", "O3", "N2", "N", "NO", "Ar", "He"]

# Real-fluid tables to ship (normal hydrogen, para-hydrogen, oxygen).
NFP_FLUIDS = ["H2", "pH2", "O2"]
NFP_ISOBAR_PROPS = ["T", "h", "s", "r", "cp", "cv", "a"]
NFP_SAT_PROPS = ["Tsat", "Psat", "hl", "hv", "sl", "sv", "rl", "rv"]

HGS_CREDIT = {
    "project": "HGS - Hot Gas Simulator (MATLAB)",
    "authors": "C. Fuster, M. Soria, A. Miró - ESEIAAT, Universitat Politècnica de Catalunya",
    "url": "https://github.com/ManelSoria/HGS",
    "license": "CC0-1.0",
    "data_origin": "A. Burcat and B. Ruscic, Third Millennium Ideal Gas and Condensed Phase Thermochemical Database "
    "for Combustion with Updates from Active Thermochemical Tables, ANL-05/20 and TAE 960, Argonne National "
    "Laboratory / Technion, 2005",
}
INIST_CREDIT = {
    "project": "INIST / NFP - Non-ideal Fluid Properties (MATLAB)",
    "authors": "M. Soria, C. Fuster, L. Frezza - ESEIAAT, Universitat Politècnica de Catalunya",
    "url": "https://github.com/ManelSoria/INIST",
    "license": "CC0-1.0",
    "data_origin": "E.W. Lemmon, I.H. Bell, M.L. Huber, M.O. McLinden, Thermophysical Properties of Fluid Systems, "
    "in NIST Chemistry WebBook, NIST Standard Reference Database Number 69 (eds. P.J. Linstrom, W.G. Mallard), "
    "National Institute of Standards and Technology",
}


def git_commit(path: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except Exception:  # pragma: no cover - informational only
        return "unknown"


def convert_hgs(hgs_dir: Path) -> None:
    raw = sio.loadmat(hgs_dir / "HGSdata.mat", squeeze_me=True, struct_as_record=False)["HGSdata"]
    names = list(raw.name)
    # keys starting with "_" are metadata, not species (ssme.thermo.hgs skips them)
    db: dict = {"_source": {**HGS_CREDIT, "file": "HGSdata.mat", "commit": git_commit(hgs_dir),
                            "converted_with": "tools/convert_thermo_data.py (subset of species)"}}
    for sp in HGS_SPECIES:
        i = names.index(sp)
        ena = np.atleast_1d(raw.ena[i]).tolist()
        nat = np.atleast_1d(raw.nat[i]).astype(float).tolist()
        db[sp] = {
            "hgs_index": i + 1,  # 1-based index in HGSdata.mat (useful when comparing with MATLAB)
            "state": str(raw.state[i]),
            "Mm": float(raw.Mm[i]),  # g/mol
            "T_limits": [float(x) for x in raw.lim[i]],  # [Tmin, Tmid, Tmax] K
            "low": [float(x) for x in raw.LV[i]],  # a1..a7 valid Tmin..Tmid
            "high": [float(x) for x in raw.HV[i]],  # a1..a7 valid Tmid..Tmax
            "elements": dict(zip(ena, nat)),
        }
    (OUT / "nasa7_hgs.json").write_text(json.dumps(db, indent=1))


def convert_nfp(inist_dir: Path) -> None:
    for fluid in NFP_FLUIDS:
        d = sio.loadmat(inist_dir / "DatabaseNFP" / f"{fluid}.mat", squeeze_me=True, struct_as_record=False)[fluid]
        arrays: dict[str, np.ndarray] = {}
        P = np.array([float(np.atleast_1d(iso.P)[0]) for iso in d.isoP])
        arrays["isobars"] = P
        lengths = np.array([np.size(iso.T) for iso in d.isoP])
        arrays["lengths"] = lengths
        for prop in NFP_ISOBAR_PROPS:
            arrays[f"iso_{prop}"] = np.concatenate([np.atleast_1d(getattr(iso, prop)).astype(float) for iso in d.isoP])
        for prop in NFP_SAT_PROPS:
            arrays[prop] = np.atleast_1d(getattr(d, prop)).astype(float)
        arrays["Tcrit"] = np.array(float(d.Tcrit))
        arrays["Pcrit"] = np.array(float(d.Pcrit))
        arrays["MM"] = np.array(float(d.MM))  # kg/mol
        arrays["reference_state"] = np.array(str(d.Ref))
        source = {**INIST_CREDIT, "file": f"DatabaseNFP/{fluid}.mat", "commit": git_commit(inist_dir),
                  "converted_with": "tools/convert_thermo_data.py (columns T, h, s, rho, cp, cv, a only)"}
        arrays["source"] = np.array(json.dumps(source, ensure_ascii=False))  # read with json.loads(str(npz["source"]))
        np.savez_compressed(OUT / f"nfp_{fluid}.npz", **arrays)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hgs", type=Path, required=True)
    ap.add_argument("--inist", type=Path, required=True)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    convert_hgs(args.hgs)
    convert_nfp(args.inist)
    sources = {
        "HGS": {"url": "https://github.com/ManelSoria/HGS", "commit": git_commit(args.hgs), "license": "CC0-1.0"},
        "INIST": {"url": "https://github.com/ManelSoria/INIST", "commit": git_commit(args.inist), "license": "CC0-1.0"},
    }
    (OUT / "SOURCES.json").write_text(json.dumps(sources, indent=2))
    print("written to", OUT)


if __name__ == "__main__":
    main()
