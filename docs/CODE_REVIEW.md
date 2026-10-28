# Code review of the original MATLAB project

Scope: the 13 files in `legacy/matlab/original/` (`main.m`, `mainLOX.m` and the 11 helper functions),
together with the two libraries they call: [HGS](https://github.com/ManelSoria/HGS) (ideal-gas
thermochemistry) and [INIST](https://github.com/ManelSoria/INIST) (NIST real-fluid tables, function `NFP`).

All numbers below come from re-running the original logic with the Python port
(`python tools/bug_impact.py`), so each one can be reproduced. The corrected MATLAB files in
`legacy/matlab/fixed/` tag every change with the `FIX(n)` number used here.

Severity:

- **High**: gives wrong results or makes a component unusable.
- **Medium**: inconsistent or fragile; wrong only in some situations.
- **Low**: cosmetic or bookkeeping.

---

## High severity

### FIX(1) Normal hydrogen used instead of para-hydrogen
Every `NFP` call uses `'H2'`, which is INIST's **normal** hydrogen table (75 % ortho). The
reference data were clearly generated with **para-hydrogen** (`'pH2'`, the equilibrium form of
liquid H2):

| Check | Normal H2 (original) | Para H2 (fixed) | Reference |
|---|---|---|---|
| K28 nozzle-coolant outlet T(S36) | 289.30 K | 258.15 K | 257.80 K |
| MCC coolant-jacket outlet T(S43) | 284.14 K | 253.20 K | 252.80 K |
| Fuel preburner T(S55) | 1132.5 K | 1115.0 K | 1105.6 K |
| Oxidizer preburner T(S50) | 858.4 K | 840.1 K | 833.3 K |
| Tank density at S31 | 70.72 kg/m³ | 70.56 kg/m³ | 70.57 kg/m³ |

With normal H2, 12 validation checks fail; with para-H2, 4 fail, and those 4 are explained below.
**Fix:** use `'pH2'` throughout (one variable, `FUEL`, in the fixed `main.m`).

### FIX(2) Pressure-loss formula `P_out = P_in*(2-deltaP)`
`heatexanger.m` and `IsentalpicValve.m` apply `P_out = P_in*(2-deltaP)`. The `deltaP` values in
`main.m` are **pressure ratios** P_in/P_out (463.32/431.40 = 1.0740; 431.40/387.25 = 1.1140;
558.71/(1.182·1.221) = 387.1 bar, which is exactly the OPB pressure). The formula is only a
first-order approximation of `P_in/deltaP`:

| Element | original | `P_in/PR` | reference |
|---|---|---|---|
| K28 (S58→S36) | 429.03 bar | 431.40 | 431.40 |
| K67 (S74→S80) | 278.49 bar | 285.52 | 285.53 |
| K61+K20 (S22→S23) | **356.02 bar** | 387.13 | 387.25 |
| K38 (S39→S40) | 382.22 bar | 387.25 | 387.25 |

For K70 the value `1.991` was tuned so that `285.53*(2-1.991) ≈ 2.49` bar. The true ratio is
285.53/2.49 = 114.7. **Fix:** `P_out = P_in/PR`. In Python, `components.outlet_pressure()` takes
either `PR` or `P_out` explicitly.

### FIX(3) Mass-flow typos
- `S21.m_dot = 50.16` should be **50.46**. S20 = 50.46 feeds pump K18, and S22 + S24 = 13.56 + 36.89 = 50.45.
  With the typo, K19 gives S24 = 36.60 kg/s instead of 36.89, which is the −0.79 % "error" reported in `S22.m_dot_relErr`.
- `S40.m_dot = 19.34` should be **19.94**. S39 = 19.94, and S51 = 33.50 = 19.94 + 13.56. The typo shifts the
  OPB O/F from 0.680 to 0.701 and raises T(S50) from 840.1 K to **860.3 K** (reference 833.3 K).

### FIX(4) Inconsistent enthalpy reference states (`getDeltah`, `mixer_multispecies*.m`)
NIST tables and NASA polynomials use different enthalpy zeros, so they can only be combined through an offset.
`getDeltah(P)` computed that offset for **H2 at 675 K and at the stream pressure**. At 248 bar, H2
is not an ideal gas, so the offset is −4135 kJ/kg instead of −3931 kJ/kg (**~204 kJ/kg error**; −4254 at 391 bar).
`mixer_multispecies2.m` then:

- subtracted this **H2** offset from the HGS enthalpies of H2O, OH, O, HO2 and H2O2, which is meaningless;
- evaluated each species with `try NFP ... catch HGS`. This mixes three reference states (NIST H2, NIST O2, NIST H2O, HGS)
  in one balance. It also makes H(T) discontinuous wherever NFP's range ends (fatal for `fzero`). And NFP's pure-water
  table at 248 bar describes *liquid* water below 647 K, not steam at its partial pressure;
- recomputed `getDeltah` (≈2000 property evaluations) inside every `fzero` iteration, which is why it was so slow.

**Fix:** one offset per fluid, computed in the ideal-gas limit (300 K, 0.01 bar), where both data sets describe
the same physics. Para-H2 is tied to normal H2 through the 527 kJ/kg ortho→para conversion enthalpy. The gas
mixers then do one consistent energy balance on the NASA scale (`ssme/thermo/fluids.py`; MATLAB:
`realfluid_offset.m`, `mixer_gas.m`). The fixed mixers K49 and K48 reproduce the reference within 0.2 K.

### FIX(5) HP oxidizer turbine K41 computed as pure hydrogen
`mainLOX.m` set `S50.sp = "H2"` and called the real-fluid `turbine()`. `main.m` commented the call out ("ME DA MAL").
The preburner gas is 45 % H2O by mass:

| | pure H2 (original) | H2/H2O frozen mixture (fixed) | reference |
|---|---|---|---|
| T(S51) | 762.1 K | 760.88 K | 760.9 K |
| W | **−39 074 kW** | −21 776 kW | −21 770 kW |

`turbine()` cannot take a species list anyway (`char()` of a string array is a char matrix). **Fix:**
`gas_turbine()` (Python) / `turbine_mix.m` (MATLAB) for ideal-gas mixtures with frozen composition.

### FIX(6) Combustor temperatures imposed instead of predicted
The preburner (K45) and the main chamber (K50) call `HGSeq(species, n0, Tref, Pref)`, which gives the
equilibrium composition **at the reference temperature**. The temperature, the main output of a
combustor, is therefore an input and cannot be validated. `mainLOX.m` skipped the oxidizer preburner
("ME SALTO EL BURNER K40"). In `main.m` the OPB reused (and overwrote) the struct `K45`.
**Fix:** adiabatic (H, p) equilibrium from the inlet enthalpies (`components.burner()`; MATLAB `burner_hp.m`
via `HGStp`). Results: FPB 1115.0 K (ref 1105.6, +0.85 %), OPB 840.1 K (ref 833.3, +0.81 %).

### FIX(7) Species/mole order can be scrambled when `char(cellstr(...))` is passed to HGS (please verify)
For K50 and the nozzle, the species list goes through `unique` (alphabetical), `cellstr` and `char`. The result is a
padded char *matrix* that is passed to `HGSeq`/`HGSprop`/`HGSisentropic`. `HGSid` treats a char input as a single name
and runs `find(ismember(HGSdata.name, name))`. If MATLAB expands the matrix row by row, the ids come back in
**database order** (OH, HO2, H2, H2O, H2O2, O, O2), not in the alphabetical order of `n`
(H2, H2O, H2O2, HO2, O, O2, OH). The element inventory would then be wrong: O/H atom ratio **1.423 instead of 0.379**.
I could not run MATLAB to confirm this. Check it with
`HGSid(char(S60.sp))` vs `HGSid(cellstr(S60.sp))`. **Fix:** always pass a cell array of char, in a fixed order, and
add numeric molar-flow vectors in that same order (`SP` in the fixed `main.m`).

### FIX(8) Atomic hydrogen missing from the product species
`{'H2','O2','H2O','H2O2','HO2','O','OH'}` leaves out **H**, which is a major radical at chamber temperature.
Adiabatic T at 225 bar: 3646 K with H, **3722 K without** (+76 K).

### FIX(9) Nozzle energy balance
`main.m` subtracted **K52 + K53** (MCC + nozzle coolant heat) from the chamber enthalpy. K52 is taken from the gas
*in the chamber*, before S63, so subtracting it again double-counts it (v = 4423 vs 4444 m/s with shifting
equilibrium). Also, the specific enthalpy used a hard-coded mass flow (76.61+12.75+388.13+33.97) and ignored the
computed `total_mass`. `throat_nozzle.m` actually computes the **exit** state, and its failure branch leaves `T_static`,
`n` and `Mm` unassigned. **Fix:** `components.nozzle()` / `nozzle_exit.m`.

---

## Medium severity

### FIX(10) Mixed component-validation and chained logic
Some components get the computed upstream state (`pump(S13.sp, S13.P, S13.T, ...)`), others the reference one
(`pump(S32.sp, S32.P, S32.Tref, ...)`, `splitter(S17.m_dot_ref, ...)`). The results are neither a clean component
validation nor a cycle calculation. **Fix:** two explicit modes in Python. `isolated`: every component is fed with
reference inlets. `chained`: states propagate, the LOX recirculation loop is converged, and the HPFT is closed with
the shaft power balance.

### FIX(11) Fragile inverse property calls in INIST
`NFP(...,'t_hp')` and `NFP(...,'t_ps')` use `fsolve` (Optimization Toolbox) from a fixed guess (1.1·Tsat or 1.1·Tcrit)
and never check the exit flag. Inside the two-phase dome they return **`[quality, Tsat]`**, which the calling code would
treat as a temperature. **Fix:** Python uses a bracketed `brentq` on the same interpolated function and raises
`TwoPhaseError`. MATLAB: `check_single_phase.m`.

### FIX(12) `mixer.m` input handling
`mixer([S12.sp, S162.sp], ...)` works only because both are *strings*. With two char vectors, `['O2','O2']` becomes
`'O2O2'` and `sp(1)` is `'O'`. The inlet-pressure check uses exact floating-point equality.

### FIX(13) Performance
`getDeltah` evaluates 1000 HGS + 1000 NFP points per call and was called inside `fzero` loops. The Python offset is
computed once and cached.

### FIX(14) Components missing from the power balance
- The main fuel valve K64 only stored pressure/temperature ratios.
- The coolant control valve K36 and the MCC coolant jacket (heat K52 into S41→S43) were not modelled.
- The HP fuel turbine (S55→S56) was missing, so the HPFTP shaft could not be balanced.

All four are now modelled and validated: K64 −0.04 K, K36 +0.03 K, jacket +0.40 K, HPFT implied η = 0.780.

### FIX(15) Project hygiene
- Absolute Windows paths from two different computers (`D:\Altres\...`, `C:\Users\Toni\...`).
- `mainLOX.m` is an older copy of the LOX section that diverged from `main.m`.
- `main.m` repeats the K28/S87/S36 block at the end and overwrites the earlier values.

---

## Low severity (bookkeeping)

### FIX(16) Copy-paste slips
- `V_dot` of S13, S14, S21, S80, S69 and S162 is computed with another station's `m_dot`/`rho`.
- The S17 block assigns `S15.P` and `S15.T`.
- `S80.sp = "O2"` sits under the S69 header.
- `K10.type = 'mixer'` overwrites the pump K10 (the mixer is K12).
- The S24 error is stored as `S22.m_dot_relErr`.
- S162 is defined twice with different densities (1056.87 / 1056.78).
- Headers are misleading: "After H2 tank K24" on the LOX tank, "After K61" on K20, and `throat_nozzle` computes the exit.
- Unused variables (`total_mass`, `h_target`, `a`…`d`), mixed char/string species, `"O2"'` transposes.

### FIX(17) Reference-data issues (in the data, not the code)
- `S90.rho = 30.97` is copied from S36 (para-H2 at 431.4 bar / 163.3 K: ~43.7 kg/m³).
- `S71.rho = S72.rho = 21.76` is copied from S44 (at 248.21 bar: 20.85 kg/m³).
- **K26 HPFP `W_ref = 59.79 MW` is 3.3 % larger than m·Δh between the reference states S32→S33 (57.83 MW).** No
  model can match both. It may include mechanical losses. The HPFT power derived from the reference states (−57.81 MW)
  balances the *state-based* pump power, which supports that reading.

### FIX(18) Property-table limitation (INIST)
Above 300 bar the INIST isobars are 100 bar apart (300, 400, 500, 600, 700 bar), and NFP interpolates linearly in
pressure. Most SSME states sit at 330–560 bar. Effect: the LPFT power (small isentropic drop between 345.5 and
261.4 bar) is 2.9 % low with the tables, while CoolProp matches the reference within 0.07 %. Everything else agrees
with CoolProp within 0.2 %. The Python package can run on either backend (`--backend coolprop`).

---

## Open issue (not a code error)
**Main-chamber temperature.** With the reference inlet states, the adiabatic equilibrium temperature is 3646 K at
225.1 bar, and 3631 K at 219.7 bar after removing K52. The reference gives S62 = 3613 K and S63 = **3683.6 K**.
S63 is *above* the adiabatic value, which an equilibrium model cannot produce from these inlets. Treating the LOX as
an ideal gas (ignoring its liquid enthalpy) adds only about +17 K. Leaving out atomic H gives +76 K. The reference tool
probably used a different species set or thermochemical model. This needs input from whoever produced the reference
data.
