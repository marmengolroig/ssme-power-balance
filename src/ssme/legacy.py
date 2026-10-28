"""What the original MATLAB scripts compute, re-created with the Python port.

``legacy/matlab/original/main.m`` (and ``mainLOX.m`` for the HP oxidizer turbine) is replayed here
with the same inputs and the same mistakes, so that the cycle map and the reports can show the
original results next to the corrected model and the reference data:

* normal hydrogen (``'H2'``) instead of para-hydrogen (FIX 1);
* pressure ratios applied as ``P_in * (2 - deltaP)`` (FIX 2);
* the mass-flow typos ``S21 = 50.16`` and ``S40 = 19.34`` kg/s (FIX 3);
* the HPOT computed as pure hydrogen (``mainLOX.m``; commented out in ``main.m``) (FIX 5);
* preburner and chamber temperatures imposed, not computed (FIX 6);
* no atomic H in the products, and K52 + K53 subtracted in the nozzle (FIX 8, FIX 9);
* the mixed use of reference and computed inlet states (FIX 10).

MATLAB itself was not run: the values come from the same equations evaluated with the Python
property layer, which reproduces INIST's forward functions exactly (``tests/test_nfp.py``).  The
possible species scrambling of FIX(7) is *not* reproduced (it still has to be confirmed in MATLAB).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

from . import components as C
from .reference import load_reference
from .streams import FluidStream, GasStream
from .thermo import hgs
from .thermo.fluids import RealFluid
from .thermo.hgs import Mixture

#: Product species of the original scripts (``K45.sp0``): no atomic hydrogen.
ORIGINAL_SPECIES = ("H2", "O2", "H2O", "H2O2", "HO2", "O", "OH")


@dataclass(frozen=True)
class OriginalValue:
    """One quantity as the original scripts produce it.

    ``status``: ``"computed"`` (a prediction that can be validated), ``"imposed"`` (the script
    sets the reference value as an input) or ``"not_modelled"`` (the script has no such component).
    """

    value: float | None
    status: str = "computed"
    note: str = ""


def _p(P_in: float, deltaP: float) -> float:
    """The original pressure-loss rule (heatexanger.m, IsentalpicValve.m)."""
    return P_in * (2.0 - deltaP)


@cache
def _original(backend: str) -> dict[tuple[str, str], OriginalValue]:
    ref = load_reference(hydrogen_table="H2", backend=backend)
    st = ref.st
    H2 = RealFluid("H2", ref.backend)  # normal hydrogen, as in every NFP call of the scripts
    O2 = RealFluid("O2", ref.backend)

    def fs(fluid: RealFluid, m: float, P: float, T: float) -> FluidStream:
        return FluidStream(fluid, m, P, T)

    out: dict[tuple[str, str], OriginalValue] = {}

    def put(item: str, q: str, v: float | None, status: str = "computed", note: str = "") -> None:
        out[(item, q)] = OriginalValue(None if v is None else float(v), status, note)

    cp = ref.components
    # ---------------------------------------------------------------- fuel side (main.m)
    s32, d = C.pump(fs(H2, 73.22, st("S31")["P"], st("S31")["T"]), st("S32")["P"], cp["K25"]["eta"])
    put("K25 LPFP", "T(S32)", s32.T)
    put("K25 LPFP", "W", d["W"])
    s33, d = C.pump(fs(H2, 73.22, st("S32")["P"], st("S32")["T"]), st("S33")["P"], cp["K26"]["eta"])
    put("K26 HPFP", "T(S33)", s33.T, note="inlet: reference S32")
    put("K26 HPFP", "W", d["W"])
    put("K64 MFV", "T(S58)", None, "not_modelled", "only P and T ratios were stored")
    s36, _ = C.heat_exchanger(fs(H2, 28.88, st("S58")["P"], st("S58")["T"]), cp["K28"]["Q"], P_out=_p(st("S58")["P"], 1.074))
    put("K28 nozzle HX", "T(S36)", s36.T)
    put("K28 nozzle HX", "P(S36)", s36.P, note="P_in*(2-1.074)")
    put("K36 CCV", "T(S89)", None, "not_modelled")
    s90, _ = C.mixer([fs(H2, 28.88, st("S36")["P"], st("S36")["T"]), fs(H2, 28.88, st("S89")["P"], st("S89")["T"])], st("S90")["P"])
    put("K37 mixer", "T(S90)", s90.T, note="inlets: reference S36 and S89")
    put("MCC coolant jacket", "T(S43)", None, "not_modelled", "heat K52 not applied to the coolant")
    s44, d = C.turbine(fs(H2, 15.46, st("S43")["P"], st("S43")["T"]), st("S44")["P"], cp["K34"]["eta"])
    put("K34 LPFT", "T(S44)", s44.T)
    put("K34 LPFT", "W", d["W"])
    s40, _ = C.valve(fs(H2, 19.94, st("S39")["P"], st("S39")["T"]), P_out=_p(st("S39")["P"], 1.114))
    put("K38 OPB fuel valve", "P(S40)", s40.P, note="P_in*(2-1.114)")
    put("K38 OPB fuel valve", "T(S40)", s40.T)
    # ---------------------------------------------------------------- oxidizer side (main.m)
    s12, d = C.pump(fs(O2, 439.34, st("S11")["P"], st("S11")["T"]), st("S12")["P"], cp["K10"]["eta"])
    put("K10 LPOP", "T(S12)", s12.T)
    put("K10 LPOP", "W", d["W"])
    s13, _ = C.mixer([s12, fs(O2, 83.06, st("S162")["P"], st("S162")["T"])], st("S13")["P"])
    put("K12 mixer", "T(S13)", s13.T, note="inlets: computed S12, reference S162")
    s14, d = C.pump(s13, st("S14")["P"], cp["K13"]["eta"])
    put("K13 HPOP", "T(S14)", s14.T, note="inlet: computed S13")
    put("K13 HPOP", "W", d["W"])
    s160, d = C.turbine(fs(O2, 83.06, st("S15")["P"], st("S15")["T"]), st("S160")["P"], cp["K15"]["eta"])
    put("K15 LPOT", "T(S160)", s160.T)
    put("K15 LPOT", "W", d["W"])
    s21, d = C.pump(fs(O2, 50.46, st("S20")["P"], st("S20")["T"]), st("S21")["P"], cp["K18"]["eta"])
    put("K18", "T(S21)", s21.T)
    put("K18", "W", d["W"])
    s80, _ = C.heat_exchanger(fs(O2, 0.75, st("S74")["P"], st("S74")["T"]), cp["K67"]["Q"], P_out=_p(st("S74")["P"], 1.157))
    put("K67 ox HX", "T(S80)", s80.T)
    put("K67 ox HX", "P(S80)", s80.P, note="P_in*(2-1.157)")
    s69, _ = C.valve(fs(O2, 0.75, st("S80")["P"], st("S80")["T"]), P_out=_p(st("S80")["P"], 1.991))
    put("K70 valve", "T(S69)", s69.T, note="deltaP = 1.991 tuned to give 2.49 bar")
    put("K70 valve", "rho(S69)", s69.rho)
    s26, _ = C.valve(fs(O2, 13.56, st("S22")["P"], st("S22")["T"]), P_out=_p(st("S22")["P"], 1.182))
    s23, _ = C.valve(s26, P_out=_p(s26.P, 1.221))
    put("K61+K20 valves", "P(S23)", s23.P, note="P_in*(2-1.182)*(2-1.221)")
    put("K61+K20 valves", "T(S23)", s23.T)
    # ---------------------------------------------------------------- hot gas
    put("K45 fuel preburner", "T(S55)", st("S55")["T"], "imposed", "HGSeq at the reference temperature")
    put("HPFT", "W", None, "not_modelled")
    put("HPFT", "T(S56)", None, "not_modelled")
    put("K49 mixer", "T(S59)", None, "not_modelled", "composition only (enthalpy mixer unusable, FIX 4)")
    put("K40 ox preburner", "T(S50)", st("S50")["T"], "imposed", "HGSeq at the reference temperature; S40 = 19.34 kg/s typo")
    hpot, d = C.turbine(fs(H2, 33.5, st("S50")["P"], st("S50")["T"]), st("S51")["P"], cp["K41"]["eta"])
    put("K41 HPOT", "T(S51)", hpot.T, note="pure H2 (mainLOX.m; commented out in main.m)")
    put("K41 HPOT", "W", d["W"], note="pure H2 (mainLOX.m)")
    put("duct S51-S53", "T(S53)", None, "not_modelled")
    put("K48 mixer", "T(S54)", None, "not_modelled", "composition only (enthalpy mixer unusable, FIX 4)")
    put("K50 MCC", "T(S63)", st("S63")["T"], "imposed", "HGSeq at the reference temperature")
    # nozzle: chamber at the reference (T, P), no atomic H, K52 + K53 removed
    o2_in = 388.13 + 13.56 + 36.89 - (50.46 - 50.16)  # S18 + S22 + S24 with the S21 typo (S24 = 36.60)
    h2_in = 37.82 + 19.34 + 1.90 + 0.47 + 12.75  # S38 + S40 (typo) + S72 + S71 + S79
    base = Mixture.combine(Mixture.from_mass_flows({"H2": h2_in, "O2": o2_in}), extra_species=ORIGINAL_SPECIES)
    chamber = hgs.equilibrate_TP(base, st("S63")["T"], st("S63")["P"])
    noz = C.nozzle(GasStream(chamber.mixture, st("S63")["P"], st("S63")["T"]), st("S68")["P"],
                   Q_loss=cp["K52"]["Q"] + cp["K53"]["Q"], model="shifting")
    for q, key in (("T(S68)", "T"), ("v(S68)", "v"), ("M(S68)", "M")):
        put("nozzle envelope", q, noz[key], note="shifting, no atomic H, K52+K53 subtracted")
    return out


def original_values(backend: str = "nfp") -> dict[tuple[str, str], OriginalValue]:
    """``{(check item, quantity): OriginalValue}`` keyed like :class:`ssme.cycle.Check`."""
    return dict(_original(backend))


def original_station_flows() -> dict[str, float]:
    """Mass flows the original scripts used where they differ from the reference (typos)."""
    return {"S21": 50.16, "S24": 50.16 - 13.56, "S40": 19.34}
