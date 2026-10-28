"""Quantify the effect of the errors found in the original MATLAB code.

Each block re-creates one original mistake with the Python port and compares it with the
corrected calculation and the reference value.  The numbers are quoted in docs/CODE_REVIEW.md.

    python tools/bug_impact.py
"""

from __future__ import annotations

from ssme import components as C
from ssme.cycle import run_cycle
from ssme.reference import load_reference
from ssme.streams import FluidStream, GasStream
from ssme.thermo import hgs
from ssme.thermo.fluids import RealFluid, enthalpy_offset, getDeltah_original
from ssme.thermo.hgs import Mixture


def line(label: str, original: float, corrected: float, reference: float | None, unit: str) -> None:
    ref = f"{reference:10.2f}" if reference is not None else " " * 10
    print(f"  {label:44s} original {original:10.2f}   corrected {corrected:10.2f}   reference {ref} {unit}")


def main() -> None:
    para = load_reference(hydrogen_table="pH2")
    normal = load_reference(hydrogen_table="H2")

    print("1. Normal hydrogen ('H2') instead of para-hydrogen ('pH2')")
    rn, rp = run_cycle("isolated", reference=normal), run_cycle("isolated", reference=para)
    for item, q in [("K28 nozzle HX", "T(S36)"), ("MCC coolant jacket", "T(S43)"), ("K37 mixer", "T(S90)"),
                    ("K45 fuel preburner", "T(S55)"), ("K40 ox preburner", "T(S50)")]:
        cn, cp_ = rn.check(item, q), rp.check(item, q)
        line(f"{item} {q}", cn.computed, cp_.computed, cp_.reference, "K")
    print(f"  checks failing: normal H2 {len(rn.failed)}, para H2 {len(rp.failed)}")

    print("\n2. Pressure loss P_out = P_in*(2-PR) instead of P_in/PR")
    for label, Pin, PRs, Pref in [("K28  S58->S36", 463.32, [1.074], 431.40), ("K67  S74->S80", 330.35, [1.157], 285.53),
                                  ("K61+K20  S22->S23", 558.71, [1.182, 1.221], 387.25), ("K38  S39->S40", 431.40, [1.114], 387.25)]:
        po, pc = Pin, Pin
        for pr in PRs:
            po, pc = po * (2 - pr), pc / pr
        line(label, po, pc, Pref, "bar")

    print("\n3. Mass-flow typos")
    line("K19 splitter: S24 = S21 - S22", 50.16 - 13.56, 50.46 - 13.56, 36.89, "kg/s")
    S = rp.states
    for m40 in (19.34, 19.94):
        s40 = S["S40"].with_(m_dot=m40)
        g, _ = C.burner([s40, S["S23"]], 387.25)
        print(f"  OPB K40 with S40 = {m40:5.2f} kg/s: O/F = {13.56 / m40:.3f}, T50 = {g.T:7.2f} K (reference 833.33 K)")

    print("\n4. getDeltah(P): offset taken at the stream pressure, applied to every species")
    for P in (248.21, 391.47):
        line(f"H2 offset at {P} bar", getDeltah_original(P), enthalpy_offset("H2"), None, "kJ/kg")
    print("  (the original also subtracted this H2 offset from H2O, OH, O, HO2, H2O2 enthalpies)")

    print("\n5. HPOT K41 treated as pure hydrogen (mainLOX.m) instead of the H2/H2O preburner gas")
    h2 = FluidStream(RealFluid("H2"), 33.5, 387.25, 833.33)
    out, d = C.turbine(h2, 251.43, 0.78)
    gas = GasStream(S["S50"].mix, 387.25, 833.33)
    out2, d2 = C.gas_turbine(gas, 251.43, 0.78)
    line("T(S51)", out.T, out2.T, 760.9, "K")
    line("W", d["W"], d2["W"], -21770.0, "kW")

    print("\n6. Main chamber species without atomic hydrogen H (original K45/K50 species list)")
    elem = Mixture.combine(*[S[k].mix for k in ("S59", "S54")], para.stream("S79").as_mixture(), S["S18"].as_mixture()).element_moles()
    base = {"H2": elem["H"] / 2, "O2": elem["O"] / 2}
    H_in = sum(s.H_abs for s in [GasStream(S["S59"].mix, 248.21, 975.0), GasStream(S["S54"].mix, 248.21, 748.2),
                                 para.stream("S79"), para.stream("S14").with_(m_dot=388.13)])
    for sp in (C.PRODUCT_SPECIES, ("H2", "O2", "H2O", "H2O2", "HO2", "O", "OH")):
        mix = Mixture.combine(Mixture.from_dict(base), extra_species=sp)
        T = hgs.equilibrate_HP(mix, H_in, 225.10).T
        print(f"  {len(sp)} species {'(with H)   ' if 'H' in sp else '(without H)'}: adiabatic T = {T:7.1f} K")

    print("\n7. Nozzle: K52 + K53 subtracted (original) vs K53 only")
    v_orig = rp.check("nozzle shifting", "v(S68) with K52+K53 loss").computed
    v_new = rp.check("nozzle envelope", "v(S68)").computed
    line("v(S68), shifting equilibrium", v_orig, v_new, 4351.2, "m/s")

    print("\n8. Possible species/mole scrambling when char(cellstr(...)) is passed to HGS (verify in MATLAB!)")
    # MATLAB's unique() returns species alphabetically; HGSid(char matrix) would return database order.
    alpha = ["H2", "H2O", "H2O2", "HO2", "O", "O2", "OH"]
    db_order = sorted(alpha, key=_hgs_index)
    mix_true = Mixture.combine(*[S[k].mix for k in ("S59", "S54")], para.stream("S79").as_mixture(), S["S18"].as_mixture())
    n_alpha = [mix_true.as_dict().get(s, 0.0) for s in alpha]
    scr = Mixture(db_order, n_alpha)
    e_true, e_scr = Mixture(alpha, n_alpha).element_moles(), scr.element_moles()
    print(f"  alphabetical order : {alpha}")
    print(f"  HGS database order : {db_order}")
    print(f"  O/H atom ratio: correct {e_true['O'] / e_true['H']:.3f}, scrambled {e_scr['O'] / e_scr['H']:.3f}")


def _hgs_index(name: str) -> int:
    import json

    from ssme.thermo.hgs import DATA_FILE

    return json.loads(DATA_FILE.read_text())[name]["hgs_index"]


if __name__ == "__main__":
    main()
