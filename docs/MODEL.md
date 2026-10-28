# Model description

Units throughout: P [bar], T [K], ṁ [kg/s], h [kJ/kg], power and heat [kW].

## Thermodynamic layer (`src/ssme/thermo`)

| Module | What it does | Origin |
|---|---|---|
| `nfp.py` | Real-fluid properties of para-H2, normal H2 and O2 from NIST Webbook isobars. Linear interpolation in T on the two bracketing isobars (split at the phase change), then linear in p. Inverses by bracketed root finding. | Port of INIST `NFP.m` (CC0), same data |
| `hgs.py` | NASA 7-coefficient polynomials (Burcat), ideal-gas mixtures, Gibbs-minimisation equilibrium (Gordon–McBride element-potential method), (H,p) and (S,p) problems | Port of HGS (CC0), same data and gas constant |
| `fluids.py` | `RealFluid` (backend `nfp` or `coolprop`) and the offset that puts real-fluid enthalpies on the NASA scale | New (replaces `getDeltah.m`) |
| `coolprop_backend.py` | Optional CoolProp access (Python package or shared library) | New |

Enthalpy offset (ideal-gas limit, per fluid):

    offset = h_NASA(300 K) − h_real(0.01 bar, 300 K)
    offset_pH2 = offset_H2 + h_H2,sat.liq(NBP) − h_pH2,sat.liq(NBP) − 527 kJ/kg

## Components (`src/ssme/components.py`)

| Model | Equations | Assumptions |
|---|---|---|
| `pump` | h₂ₛ = h(P₂, s₁); h₂ = h₁ + (h₂ₛ − h₁)/η; W = ṁ(h₂ − h₁) | adiabatic, real fluid |
| `turbine` (real fluid) | h₂ = h₁ + η(h₂ₛ − h₁) | adiabatic (LPOT is hydraulic, LPFT is H2) |
| `valve` | h₂ = h₁, P₂ = P₁/PR or given | isenthalpic |
| `heat_exchanger` | h₂ = h₁ + Q/ṁ, P₂ = P₁/PR or given | heat load imposed (K28 = K53, MCC jacket = K52) |
| `mixer` | Σṁh conserved, single real fluid | adiabatic |
| `splitter` | same state, ṁ₂ = ṁ₀ − ṁ₁ | |
| `gas_mixer` | ΣH (NASA scale) conserved, composition frozen | real-fluid inlets enter with their real enthalpy |
| `burner` | H_eq(T, P) = ΣH_in − Q_loss, chemical equilibrium over H, H2, O, O2, OH, H2O, HO2, H2O2 | ideal gas |
| `gas_turbine` | frozen ideal-gas mixture, isentropic efficiency | also `_from_states` (implied η) and `_for_power` (shaft closure) |
| `nozzle` | S conserved from the chamber to P_exit (shifting, frozen, or frozen after the throat); v = √(2(H₀ − H_e − Q)/ṁ); M = v/a_frozen | heat load K53 removed from the kinetic energy |

## Cycle (`src/ssme/cycle.py`)

The cycle is written as an explicit sequence that follows the station numbering of the original scripts:

1. **Fuel side**: K25 → K26 → K64 → (K27, K35) → K28 / K36 / MCC jacket → K37, K34 → K38
2. **Oxidizer side**: K10 → K12 ⟲ K13 → K14 → K15 → K11 (recirculation loop, fixed-point in chained mode) → K66 → K16 → K18 → K67 → K70, K19 → K61 → K20
3. **Hot gas**: fuel preburner K45 → HPFT → K49; oxidizer preburner K40 → HPOT K41 → duct → K48
4. **Main chamber** K50 (with K52 loss) → nozzle (with K53 loss)

In `chained` mode, the HPFT outlet comes from the HPFTP shaft balance (W_HPFT = −W_K26), since no HPFT efficiency is
given. The model reports the efficiency this requires.

Assumption in the data: the P and T of the H2 stream S79 (12.75 kg/s to the MCC) are not given in the scripts. It is
taken equal to S71/S72 (248.21 bar, 244.8 K).
