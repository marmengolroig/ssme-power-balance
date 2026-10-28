"""SSME cycle model and validation against the reference operating point.

Two run modes
-------------
``isolated`` (component validation)
    Every component receives its *reference* inlet state and its outputs are compared with the
    reference outlet state.  Errors do not propagate, so each comparison validates one component
    model.  This is what most of the original ``main.m`` did (although not consistently).

``chained`` (system validation)
    Computed outlet states are passed downstream, as in a real cycle calculation.  The LOX
    recirculation loop (HPOP -> LPOT -> K12 mixer) is converged by fixed-point iteration and the
    HP fuel turbine is closed with the HPFTP shaft power balance.

Each run returns a list of :class:`Check` objects (the validation matrix) plus all computed
states.  ``python -m ssme`` prints them; ``tests/`` asserts on them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from . import components as C
from .reference import Reference, load_reference
from .streams import FluidStream, GasStream, Stream

Mode = Literal["isolated", "chained"]


@dataclass
class Check:
    group: str  # 'component' | 'system' | 'property' | 'balance' | 'data' | 'info'
    item: str
    quantity: str
    computed: float
    reference: float | None
    unit: str
    tol_abs: float | None = None
    tol_rel: float | None = None
    note: str = ""
    bounds: tuple[float, float] | None = None  # envelope check: pass if lower <= reference <= upper

    @property
    def error(self) -> float | None:
        return None if self.reference is None else self.computed - self.reference

    @property
    def rel_error(self) -> float | None:
        if self.reference in (None, 0):
            return None
        return (self.computed - self.reference) / abs(self.reference)

    @property
    def passed(self) -> bool | None:
        if self.reference is not None and self.bounds is not None:
            lo, hi = sorted(self.bounds)
            return bool(lo <= self.reference <= hi)
        if self.reference is None or (self.tol_abs is None and self.tol_rel is None):
            return None
        ok = True
        if self.tol_abs is not None:
            ok &= abs(self.error) <= self.tol_abs
        if self.tol_rel is not None:
            ok &= abs(self.rel_error) <= self.tol_rel
        return bool(ok)

    @property
    def criterion(self) -> str:
        if self.bounds is not None:
            lo, hi = sorted(self.bounds)
            return f"reference within [{lo:.4g}, {hi:.4g}]"
        parts = []
        if self.tol_abs is not None:
            parts.append(f"abs. err <= {self.tol_abs:g} {self.unit}")
        if self.tol_rel is not None:
            parts.append(f"rel. err <= {100 * self.tol_rel:g} %")
        return " and ".join(parts) or "info"


@dataclass
class CycleResult:
    mode: Mode
    hydrogen_table: str
    backend: str = "nfp"
    nozzle_model: str = "shifting"
    checks: list[Check] = field(default_factory=list)
    states: dict[str, Stream] = field(default_factory=dict)
    extras: dict[str, dict] = field(default_factory=dict)

    def check(self, item: str, quantity: str) -> Check:
        for c in self.checks:
            if c.item == item and c.quantity == quantity:
                return c
        raise KeyError((item, quantity))

    @property
    def failed(self) -> list[Check]:
        return [c for c in self.checks if c.passed is False]


class _Run:
    def __init__(self, ref: Reference, mode: Mode, nozzle_model: str, lox_loop_tol: float):
        self.ref = ref
        self.mode = mode
        self.acc = ref.acceptance
        self.res = CycleResult(mode, ref.hydrogen_table, ref.backend, nozzle_model)
        self.nozzle_model = nozzle_model
        self.lox_loop_tol = lox_loop_tol

    # ------------------------------------------------------------------ helpers
    @property
    def S(self) -> dict[str, Stream]:
        return self.res.states

    def inlet(self, name: str) -> Stream:
        """Inlet stream for a component according to the run mode."""
        if self.mode == "isolated" and self.ref.st(name)["fluid"] != "gas" and self.ref.has_state(name):
            return self.ref.stream(name)
        if name in self.S:
            return self.S[name]
        if self.ref.st(name)["fluid"] != "gas" and self.ref.has_state(name):
            return self.ref.stream(name)
        raise KeyError(f"no state available for {name}")

    def gas_inlet(self, name: str) -> GasStream:
        """Gas inlet: computed composition; (T, P) from the reference in isolated mode."""
        comp = self.S[name]
        assert isinstance(comp, GasStream)
        if self.mode == "isolated":
            st = self.ref.st(name)
            return GasStream(comp.mix, st["P"], st["T"])
        return comp

    def P(self, name: str) -> float:
        return self.ref.st(name)["P"]

    def m(self, name: str) -> float:
        return self.ref.st(name)["m_dot"]

    def add(self, *a, **k) -> None:
        self.res.checks.append(Check(*a, **k))

    def check_T(self, item: str, station: str, T: float, note: str = "") -> None:
        Tref = self.ref.st(station).get("T")
        if Tref is None:
            self.add("info", item, f"T({station})", T, None, "K", note=note or "no reference value")
        elif Tref < 200:
            self.add("component", item, f"T({station})", T, Tref, "K", tol_abs=self.acc["T_abs_cryogenic"], note=note)
        else:
            self.add("component", item, f"T({station})", T, Tref, "K", tol_rel=self.acc["T_rel"], note=note)

    def check_W(self, item: str, comp: str, W: float, note: str = "") -> None:
        Wref = self.ref.components[comp].get("W_ref")
        self.add("component", item, "W", W, Wref, "kW", tol_rel=self.acc["W_rel"] if Wref else None, note=note)

    def check_P(self, item: str, station: str, P: float, note: str = "") -> None:
        self.add("component", item, f"P({station})", P, self.P(station), "bar", tol_rel=self.acc["P_rel"], note=note)

    def label(self, comp: str) -> str:
        note = self.ref.components[comp].get("note", "")
        short = note.split(" ")[0] if note and note.split(" ")[0].isupper() else ""
        return f"{comp} {short}".strip()

    # ------------------------------------------------------------------ fuel side
    def fuel_pumps_and_cooling(self) -> None:
        cp = self.ref.components
        S = self.S
        # K25 LPFP
        S["S32"], d = C.pump(self.inlet("S31"), self.P("S32"), cp["K25"]["eta"])
        self.check_T(self.label("K25"), "S32", S["S32"].T)
        self.check_W(self.label("K25"), "K25", d["W"])
        self.res.extras["K25"] = d
        # K26 HPFP
        S["S33"], d = C.pump(self.inlet("S32"), self.P("S33"), cp["K26"]["eta"])
        self.check_T(self.label("K26"), "S33", S["S33"].T)
        self.check_W(self.label("K26"), "K26", d["W"])
        self.res.extras["K26"] = d
        # K64 main fuel valve (isenthalpic, outlet pressure from the reference)
        S["S58"], _ = C.valve(self.inlet("S33"), P_out=self.P("S58"))
        self.check_T("K64 MFV", "S58", S["S58"].T, note="isenthalpic valve (new check)")
        # K27, K35 splitters
        S["S34"], S["S41"] = C.splitter(self.inlet("S58"), self.m("S34"))
        S["S87"], S["S88"] = C.splitter(S["S34"], self.m("S87"))
        # K28 nozzle coolant
        k28 = cp["K28"]
        S["S36"], _ = C.heat_exchanger(self.inlet_branch("S87", "S58"), k28["Q"], PR=k28["PR"])
        self.check_T("K28 nozzle HX", "S36", S["S36"].T)
        self.check_P("K28 nozzle HX", "S36", S["S36"].P, note="P_out = P_in / PR")
        # K36 coolant control valve
        S["S89"], _ = C.valve(self.inlet_branch("S88", "S58"), P_out=self.P("S89"))
        self.check_T("K36 CCV", "S89", S["S89"].T, note="isenthalpic valve (new check)")
        # K37 mixer
        S["S90"], _ = C.mixer([self.inlet("S36"), self.inlet("S89")], self.P("S90"))
        self.check_T("K37 mixer", "S90", S["S90"].T)
        # MCC coolant jacket (heat K52)
        S["S43"], _ = C.heat_exchanger(self.inlet_branch("S41", "S58"), cp["MCCJ"]["Q"], P_out=self.P("S43"))
        self.check_T("MCC coolant jacket", "S43", S["S43"].T, note="Q = K52 = 47.77 MW (new check)")
        # K34 LPFT
        S["S44"], d = C.turbine(self.inlet("S43"), self.P("S44"), cp["K34"]["eta"])
        self.check_T(self.label("K34"), "S44", S["S44"].T)
        self.check_W(self.label("K34"), "K34", d["W"])
        self.res.extras["K34"] = d
        # S90 -> S38 (FPB) + S39 (OPB);  K38 OPB fuel valve
        S["S38"], S["S39"] = C.splitter(self.inlet("S90"), self.m("S38"))
        S["S40"], _ = C.valve(self.inlet("S39"), PR=cp["K38"]["PR"])
        self.check_P("K38 OPB fuel valve", "S40", S["S40"].P, note="P_out = P_in / PR")
        self.add("info", "K38 OPB fuel valve", "T(S40)", S["S40"].T, None, "K")

    def inlet_branch(self, branch: str, parent: str) -> FluidStream:
        """Inlet of a component fed by a splitter branch: parent state with the branch flow."""
        if self.mode == "isolated":
            return self.ref.stream(parent).with_(m_dot=self.m(branch))
        s = self.S[branch]
        assert isinstance(s, FluidStream)
        return s

    # ------------------------------------------------------------------ oxidizer side
    def lox_side(self) -> None:
        cp = self.ref.components
        S = self.S
        S["S12"], d = C.pump(self.inlet("S11"), self.P("S12"), cp["K10"]["eta"])
        self.check_T(self.label("K10"), "S12", S["S12"].T)
        self.check_W(self.label("K10"), "K10", d["W"])
        self.res.extras["K10"] = d

        def loop(s162: FluidStream):
            s13, _ = C.mixer([self.inlet("S12"), s162], self.P("S13"))
            S["S13"] = s13
            s14, d13 = C.pump(self.inlet("S13"), self.P("S14"), cp["K13"]["eta"])
            S["S14"] = s14
            s15, s17 = C.splitter(self.inlet("S14"), self.m("S15"))
            S["S15"], S["S17"] = s15, s17
            src15 = self.inlet_branch("S15", "S14")
            s160, d15 = C.turbine(src15, self.P("S160"), cp["K15"]["eta"])
            S["S160"] = s160
            # K11: S160 -> S162 at the same pressure (29.70 bar): identity
            return s160.with_(P=self.P("S162")), d13, d15

        if self.mode == "isolated":
            s162_new, d13, d15 = loop(self.ref.stream("S162"))
            iters = 1
        else:
            s162 = self.ref.stream("S162")  # initial guess
            for iters in range(1, 51):  # noqa: B007 (iters is reported after the loop)
                s162_new, d13, d15 = loop(s162)
                if abs(s162_new.T - s162.T) < self.lox_loop_tol:
                    break
                s162 = s162_new
            else:  # pragma: no cover
                raise RuntimeError("LOX recirculation loop did not converge")
        S["S162"] = s162_new
        self.res.extras["lox_loop_iterations"] = {"n": iters}
        self.check_T("K12 mixer", "S13", S["S13"].T)
        self.check_T(self.label("K13"), "S14", S["S14"].T)
        self.check_W(self.label("K13"), "K13", d13["W"])
        self.res.extras["K13"] = d13
        self.check_T(self.label("K15"), "S160", S["S160"].T)
        self.check_W(self.label("K15"), "K15", d15["W"])
        self.res.extras["K15"] = d15
        # K66, K16 splitters
        S["S29"], S["S74"] = C.splitter(self.inlet("S17"), self.m("S29"))
        S["S18"], S["S20"] = C.splitter(S["S29"], self.m("S18"))
        # K18 preburner boost pump
        S["S21"], d = C.pump(self.inlet_branch("S20", "S14"), self.P("S21"), cp["K18"]["eta"])
        self.check_T(self.label("K18"), "S21", S["S21"].T)
        self.check_W(self.label("K18"), "K18", d["W"])
        self.res.extras["K18"] = d
        # K67 oxidizer heat exchanger, K70 pressurant valve
        k67 = cp["K67"]
        S["S80"], _ = C.heat_exchanger(self.inlet_branch("S74", "S14"), k67["Q"], PR=k67["PR"])
        self.check_T("K67 ox HX", "S80", S["S80"].T)
        self.check_P("K67 ox HX", "S80", S["S80"].P, note="P_out = P_in / PR")
        S["S69"], _ = C.valve(self.inlet("S80"), P_out=self.P("S69"))
        self.check_T("K70 valve", "S69", S["S69"].T)
        self.add("component", "K70 valve", "rho(S69)", S["S69"].rho, self.ref.st("S69")["rho"], "kg/m3", tol_rel=self.acc["rho_rel"])
        # K19 splitter, K61 + K20 valves
        S["S22"], S["S24"] = C.splitter(self.inlet("S21"), self.m("S22"))
        S["S26"], _ = C.valve(self.inlet_branch("S22", "S21"), PR=cp["K61"]["PR"])
        S["S23"], _ = C.valve(S["S26"], PR=cp["K20"]["PR"])
        self.check_P("K61+K20 valves", "S23", S["S23"].P, note="P_out = P_in / PR; should equal OPB pressure")
        self.add("info", "K61+K20 valves", "T(S23)", S["S23"].T, None, "K")

    # ------------------------------------------------------------------ hot gas side
    def hot_gas(self) -> None:
        cp = self.ref.components
        S = self.S
        # fuel preburner K45
        fpb_in = [self.inlet("S38"), self.inlet_branch("S24", "S21")]
        S["S55"], d = C.burner(fpb_in, self.P("S55"))
        self.check_T("K45 fuel preburner", "S55", S["S55"].T, note="adiabatic equilibrium (was imposed)")
        self.res.extras["K45"] = d
        # HP fuel turbine
        k26_W = self.res.extras["K26"]["W"]
        if self.mode == "isolated":
            inlet = self.gas_inlet("S55")
            outlet = GasStream(inlet.mix, self.P("S56"), self.ref.st("S56")["T"])
            d = C.gas_turbine_from_states(inlet, outlet)
            S["S56"] = outlet
            self.check_W("HPFT", "HPFT", d["W"], note="from reference inlet/outlet states")
            self.add("info", "HPFT", "eta (implied)", d["eta"], None, "-")
        else:
            S["S56"], d = C.gas_turbine_for_power(S["S55"], self.P("S56"), -k26_W)
            self.check_T("HPFT", "S56", S["S56"].T, note="closed with HPFTP shaft balance W = -W(K26)")
            self.add("info", "HPFT", "eta (required)", d["eta"], None, "-")
        self.res.extras["HPFT"] = d
        # K49 mixer
        S["S59"], _ = C.gas_mixer([self.gas_inlet("S56"), self.inlet("S72")], self.P("S59"))
        self.check_T("K49 mixer", "S59", S["S59"].T)
        # oxidizer preburner K40
        opb_in = [self.inlet("S40"), self.inlet("S23")]
        S["S50"], d = C.burner(opb_in, self.P("S50"))
        self.check_T("K40 ox preburner", "S50", S["S50"].T, note="adiabatic equilibrium (was skipped)")
        self.res.extras["K40"] = d
        # HPOT K41
        S["S51"], d = C.gas_turbine(self.gas_inlet("S50"), self.P("S51"), cp["K41"]["eta"])
        self.check_T(self.label("K41"), "S51", S["S51"].T, note="frozen ideal-gas mixture (was pure H2)")
        self.check_W(self.label("K41"), "K41", d["W"])
        self.res.extras["K41"] = d
        # duct S51 -> S53 (pressure loss only)
        S["S53"] = S["S51"].with_(P=self.P("S53"))
        if self.mode == "chained":
            self.check_T("duct S51-S53", "S53", S["S53"].T, note="adiabatic duct, ideal gas: T unchanged")
        # K48 mixer
        S["S54"], _ = C.gas_mixer([self.gas_inlet("S53"), self.inlet("S71")], self.P("S54"))
        self.check_T("K48 mixer", "S54", S["S54"].T)

    def chamber_and_nozzle(self) -> None:
        cp = self.ref.components
        S = self.S
        mcc_in = [self.gas_inlet("S59"), self.gas_inlet("S54"), self.inlet("S79"), self.inlet_branch("S18", "S14")]
        Q52, Q53 = cp["K52"]["Q"], cp["K53"]["Q"]
        adiabatic, _ = C.burner(mcc_in, self.P("S62"))
        self.add("info", "K50 MCC", "T_ad at P(S62), no heat loss", adiabatic.T, self.ref.st("S62")["T"], "K",
                 note="compare: reference S62")
        chamber, _ = C.burner(mcc_in, self.P("S63"), Q_loss=Q52)
        S["S63c"] = chamber
        self.check_T("K50 MCC", "S63", chamber.T, note="equilibrium, heat loss K52 = 47.77 MW")
        self.res.extras["K50"] = {"T_adiabatic": adiabatic.T, "T_with_loss": chamber.T,
                                  "mass_fractions": chamber.mix.mass_fractions()}
        # nozzle
        if self.mode == "isolated":  # chamber at the reference (T, P), as the original code did
            st = self.ref.st("S63")
            noz_in = C.equilibrium_state(mcc_in, st["T"], st["P"])
        else:
            noz_in = chamber
        S["S63"] = noz_in
        e = self.ref.st("S68")
        runs = {m: C.nozzle(noz_in, e["P"], Q_loss=Q53, model=m) for m in ("shifting", "frozen_throat", "frozen")}
        for m, out in runs.items():
            for q, unit in (("T", "K"), ("v", "m/s"), ("M", "-")):
                self.add("info", f"nozzle {m}", f"{q}(S68)", out[q], e[q], unit)
        # Validation: chemistry is neither fully shifting nor fully frozen in a real nozzle, so the
        # reference must fall inside the [frozen, shifting] envelope of the equilibrium model.
        for q, unit in (("T", "K"), ("v", "m/s"), ("M", "-")):
            self.add("system", "nozzle envelope", f"{q}(S68)", runs[self.nozzle_model][q], e[q], unit,
                     bounds=(runs["frozen"][q], runs["shifting"][q]),
                     note=f"computed = {self.nozzle_model}; heat loss K53 only")
        orig = C.nozzle(noz_in, e["P"], Q_loss=Q52 + Q53, model="shifting")
        self.add("info", "nozzle shifting", "v(S68) with K52+K53 loss", orig["v"], e["v"], "m/s",
                 note="original script subtracted both heat flows")
        self.res.extras["nozzle"] = {m: {k: v for k, v in out.items() if k != "mixture"} for m, out in runs.items()}

    # ------------------------------------------------------------------ balances
    def balances(self) -> None:
        st = self.ref.stations
        tol = self.acc["m_dot_abs"]
        groups = {
            "K27": ("S58", ["S34", "S41"]),
            "K35": ("S34", ["S87", "S88"]),
            "K37": ("S90", ["S36", "S89"]),
            "S90 split": ("S90", ["S38", "S39"]),
            "K12": ("S13", ["S12", "S162"]),
            "K14": ("S14", ["S15", "S17"]),
            "K66": ("S17", ["S29", "S74"]),
            "K16": ("S29", ["S18", "S20"]),
            "K19": ("S21", ["S22", "S24"]),
            "K45 FPB": ("S55", ["S38", "S24"]),
            "K40 OPB": ("S50", ["S40", "S23"]),
            "K49": ("S59", ["S56", "S72"]),
            "K48": ("S54", ["S53", "S71"]),
            "K50 MCC": ("S63", ["S59", "S54", "S79", "S18"]),
        }
        for name, (total, parts) in groups.items():
            s = sum(st[p]["m_dot"] for p in parts)
            self.add("balance", f"mass {name}", f"sum({'+'.join(parts)})", s, st[total]["m_dot"], "kg/s", tol_abs=tol)
        h2_use = sum(st[p]["m_dot"] for p in ("S38", "S39", "S71", "S72", "S79"))
        self.add("info", "mass engine H2", "H2 to burners + MCC", h2_use, st["S31"]["m_dot"], "kg/s",
                 note="difference = GH2 tank pressurant (not listed in the data)")
        o2_use = sum(st[p]["m_dot"] for p in ("S18", "S22", "S24", "S74"))
        self.add("balance", "mass engine O2", "O2 to injector + preburners + HX", o2_use, st["S11"]["m_dot"], "kg/s", tol_abs=tol)
        # shaft power balances: reference data and model
        ex = self.res.extras
        for shaft, d in self.ref.shafts.items():
            Wp_ref = sum(self.ref.components[k]["W_ref"] for k in d["pumps"])
            Wt_ref = sum(self.ref.components[k]["W_ref"] for k in d["turbines"])
            self.add("balance", f"shaft {shaft} (reference data)", "W_pumps + W_turbines", Wp_ref + Wt_ref, 0.0, "kW",
                     tol_abs=self.acc["W_rel"] * Wp_ref)
            if all(k in ex for k in d["pumps"] + d["turbines"]):
                Wp = sum(ex[k]["W"] for k in d["pumps"])
                Wt = sum(ex[k]["W"] for k in d["turbines"])
                self.add("balance", f"shaft {shaft} (model)", "W_pumps + W_turbines", Wp + Wt, 0.0, "kW",
                         tol_abs=self.acc["W_rel"] * Wp, note=f"pumps {Wp:.0f} kW, turbines {Wt:.0f} kW")

    def data_consistency(self) -> None:
        """Do the reference powers agree with the reference states?  (m * dh between stations)."""
        pairs = {"K25": ("S31", "S32", "S31"), "K26": ("S32", "S33", "S32"), "K34": ("S43", "S44", "S43"),
                 "K10": ("S11", "S12", "S11"), "K13": ("S13", "S14", "S13"), "K15": ("S14", "S160", "S15"),
                 "K18": ("S14", "S21", "S20")}
        for comp, (a, b, mflow) in pairs.items():
            sa, sb = self.ref.stream(a), self.ref.stream(b)
            W = self.m(mflow) * (sb.h - sa.h)
            Wref = self.ref.components[comp]["W_ref"]
            self.add("data", f"{self.label(comp)} power vs states", "m*dh(reference states)", W, Wref, "kW",
                     tol_rel=self.acc["W_rel"], note="checks the reference data, not the model")

    def properties(self) -> None:
        for name, st in self.ref.stations.items():
            if "rho" not in st or "P" not in st or "T" not in st:
                continue
            if st["fluid"] in ("H2", "O2"):
                rho = self.ref.stream(name).rho
                self.add("property", f"rho {name}", "rho(P_ref, T_ref)", rho, st["rho"], "kg/m3", tol_rel=self.acc["rho_rel"])
            elif name in self.S and isinstance(self.S[name], GasStream):
                g = self.S[name]
                rho = g.mix.density(st["T"], st["P"])
                # The reference densities of the hot-gas stations agree with an ideal-gas mixture of the
                # computed composition, which validates the mean molar mass (i.e. the composition).
                self.add("property", f"rho {name}", "ideal-gas rho(P_ref, T_ref)", rho, st["rho"], "kg/m3",
                         tol_rel=self.acc["rho_rel"], note="validates the computed gas composition (mean molar mass)")

    def run(self) -> CycleResult:
        self.fuel_pumps_and_cooling()
        self.lox_side()
        self.hot_gas()
        self.chamber_and_nozzle()
        self.data_consistency()
        self.properties()
        self.balances()
        return self.res


def run_cycle(
    mode: Mode = "isolated",
    *,
    hydrogen_table: str | None = None,
    backend: str = "nfp",
    reference: Reference | None = None,
    nozzle_model: str = "shifting",
    lox_loop_tol: float = 1e-6,
) -> CycleResult:
    """Run the SSME cycle model and build the validation matrix."""
    if mode not in ("isolated", "chained"):
        raise ValueError("mode must be 'isolated' or 'chained'")
    ref = reference or load_reference(hydrogen_table=hydrogen_table, backend=backend)
    if hydrogen_table and reference is not None and reference.hydrogen_table != hydrogen_table:
        raise ValueError("hydrogen_table conflicts with the given reference")
    if nozzle_model not in ("shifting", "frozen", "frozen_throat"):
        raise ValueError("nozzle_model must be 'shifting', 'frozen' or 'frozen_throat'")
    return _Run(ref, mode, nozzle_model, lox_loop_tol).run()


def summary(res: CycleResult) -> dict[str, int]:
    n_pass = sum(1 for c in res.checks if c.passed is True)
    n_fail = sum(1 for c in res.checks if c.passed is False)
    return {"pass": n_pass, "fail": n_fail, "info": len(res.checks) - n_pass - n_fail}
