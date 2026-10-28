# SSME cycle - validation report

- Mode: **isolated**  |  hydrogen: **H2**  |  real-fluid backend: **nfp**  |  nozzle model: **shifting**
- Checks: 80 pass, 12 fail, 15 informative
- Generated: 2026-10-06 with `python -m ssme`

## Failed checks

- K26 HPFP - W: 57739.70 vs 59790.00 kW (-3.43 %)
- K28 nozzle HX - T(S36): 289.30 vs 257.80 K (+12.22 %)
- MCC coolant jacket - T(S43): 284.14 vs 252.80 K (+12.40 %)
- K34 LPFT - W: -2671.90 vs -2755.00 kW (+3.02 %)
- K45 fuel preburner - T(S55): 1132.46 vs 1105.60 K (+2.43 %)
- HPFT - W: -57807.88 vs -59790.00 kW (+3.32 %)
- K40 ox preburner - T(S50): 858.42 vs 833.33 K (+3.01 %)
- K50 MCC - T(S63): 3631.24 vs 3683.60 K (-1.42 %)
- K26 HPFP power vs states - m*dh(reference states): 57687.32 vs 59790.00 kW (-3.52 %)
- K34 LPFT power vs states - m*dh(reference states): -2617.73 vs -2755.00 kW (+4.98 %)
- rho S43 - rho(P_ref, T_ref): 26.40 vs 26.54 kg/m3 (-0.52 %)
- shaft LPFTP (model) - W_pumps + W_turbines: 92.11 vs 0.00 kW

## Component validation

| Status | Item | Quantity | Computed | Reference | Unit | Error | Rel. error | Criterion | Note |
|---|---|---|---|---|---|---|---|---|---|
| PASS | K25 LPFP | T(S32) | 22.76 | 22.70 | K | 0.06 | +0.28 % | abs. err <= 2 K |  |
| PASS | K25 LPFP | W | 2764.00 | 2755.00 | kW | 9.00 | +0.33 % | rel. err <= 3 % |  |
| PASS | K26 HPFP | T(S33) | 57.36 | 57.30 | K | 0.06 | +0.11 % | abs. err <= 2 K |  |
| **FAIL** | K26 HPFP | W | 57739.70 | 59790.00 | kW | -2050.30 | -3.43 % | rel. err <= 3 % |  |
| PASS | K64 MFV | T(S58) | 59.08 | 59.10 | K | -0.02 | -0.04 % | abs. err <= 2 K | isenthalpic valve (new check) |
| **FAIL** | K28 nozzle HX | T(S36) | 289.30 | 257.80 | K | 31.50 | +12.22 % | rel. err <= 1 % |  |
| PASS | K28 nozzle HX | P(S36) | 431.40 | 431.40 | bar | -0.003352 | -0.00 % | rel. err <= 0.5 % | P_out = P_in / PR |
| PASS | K36 CCV | T(S89) | 61.47 | 61.40 | K | 0.07 | +0.12 % | abs. err <= 2 K | isenthalpic valve (new check) |
| PASS | K37 mixer | T(S90) | 164.17 | 163.30 | K | 0.87 | +0.53 % | abs. err <= 2 K |  |
| **FAIL** | MCC coolant jacket | T(S43) | 284.14 | 252.80 | K | 31.34 | +12.40 % | rel. err <= 1 % | Q = K52 = 47.77 MW (new check) |
| PASS | K34 LPFT | T(S44) | 244.56 | 244.80 | K | -0.24 | -0.10 % | rel. err <= 1 % |  |
| **FAIL** | K34 LPFT | W | -2671.90 | -2755.00 | kW | 83.10 | +3.02 % | rel. err <= 3 % |  |
| PASS | K38 OPB fuel valve | P(S40) | 387.25 | 387.25 | bar | 0.003142 | +0.00 % | rel. err <= 0.5 % | P_out = P_in / PR |
| PASS | K10 LPOP | T(S12) | 92.26 | 92.30 | K | -0.04 | -0.04 % | abs. err <= 2 K |  |
| PASS | K10 LPOP | W | 1396.50 | 1396.00 | kW | 0.50 | +0.04 % | rel. err <= 3 % |  |
| PASS | K12 mixer | T(S13) | 94.80 | 94.80 | K | 0.0009237 | +0.00 % | abs. err <= 2 K |  |
| PASS | K13 HPOP | T(S14) | 108.94 | 108.90 | K | 0.04 | +0.04 % | abs. err <= 2 K |  |
| PASS | K13 HPOP | W | 20501.74 | 20510.00 | kW | -8.26 | -0.04 % | rel. err <= 3 % |  |
| PASS | K15 LPOT | T(S160) | 107.78 | 107.80 | K | -0.02 | -0.02 % | abs. err <= 2 K |  |
| PASS | K15 LPOT | W | -1395.33 | -1396.00 | kW | 0.67 | +0.05 % | rel. err <= 3 % |  |
| PASS | K18 | T(S21) | 116.75 | 116.80 | K | -0.05 | -0.04 % | abs. err <= 2 K |  |
| PASS | K18 | W | 1262.88 | 1263.00 | kW | -0.12 | -0.01 % | rel. err <= 3 % |  |
| PASS | K67 ox HX | T(S80) | 507.70 | 507.80 | K | -0.10 | -0.02 % | rel. err <= 1 % |  |
| PASS | K67 ox HX | P(S80) | 285.52 | 285.53 | bar | -0.007096 | -0.00 % | rel. err <= 0.5 % | P_out = P_in / PR |
| PASS | K70 valve | T(S69) | 493.99 | 494.00 | K | -0.005192 | -0.00 % | rel. err <= 1 % |  |
| PASS | K70 valve | rho(S69) | 1.939 | 1.940 | kg/m3 | -0.0009294 | -0.05 % | rel. err <= 0.5 % |  |
| PASS | K61+K20 valves | P(S23) | 387.13 | 387.25 | bar | -0.12 | -0.03 % | rel. err <= 0.5 % | P_out = P_in / PR; should equal OPB pressure |
| **FAIL** | K45 fuel preburner | T(S55) | 1132.46 | 1105.60 | K | 26.86 | +2.43 % | rel. err <= 1 % | adiabatic equilibrium (was imposed) |
| **FAIL** | HPFT | W | -57807.88 | -59790.00 | kW | 1982.12 | +3.32 % | rel. err <= 3 % | from reference inlet/outlet states |
| PASS | K49 mixer | T(S59) | 975.03 | 975.00 | K | 0.03 | +0.00 % | rel. err <= 1 % |  |
| **FAIL** | K40 ox preburner | T(S50) | 858.42 | 833.33 | K | 25.09 | +3.01 % | rel. err <= 1 % | adiabatic equilibrium (was skipped) |
| PASS | K41 HPOT | T(S51) | 760.88 | 760.90 | K | -0.02 | -0.00 % | rel. err <= 1 % | frozen ideal-gas mixture (was pure H2) |
| PASS | K41 HPOT | W | -21775.92 | -21770.00 | kW | -5.92 | -0.03 % | rel. err <= 3 % |  |
| PASS | K48 mixer | T(S54) | 748.20 | 748.20 | K | -0.001392 | -0.00 % | rel. err <= 1 % |  |
| **FAIL** | K50 MCC | T(S63) | 3631.24 | 3683.60 | K | -52.36 | -1.42 % | rel. err <= 1 % | equilibrium, heat loss K52 = 47.77 MW |

## System-level validation

| Status | Item | Quantity | Computed | Reference | Unit | Error | Rel. error | Criterion | Note |
|---|---|---|---|---|---|---|---|---|---|
| PASS | nozzle envelope | T(S68) | 1261.49 | 1139.30 | K | 122.19 | +10.72 % | reference within [999.9, 1261] | computed = shifting; heat loss K53 only |
| PASS | nozzle envelope | v(S68) | 4444.43 | 4351.20 | m/s | 93.23 | +2.14 % | reference within [4246, 4444] | computed = shifting; heat loss K53 only |
| PASS | nozzle envelope | M(S68) | 4.615 | 4.734 | - | -0.12 | -2.50 % | reference within [4.615, 4.78] | computed = shifting; heat loss K53 only |

## Mass and shaft-power balances

| Status | Item | Quantity | Computed | Reference | Unit | Error | Rel. error | Criterion | Note |
|---|---|---|---|---|---|---|---|---|---|
| PASS | mass K27 | sum(S34+S41) | 73.22 | 73.22 | kg/s | 0.00 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass K35 | sum(S87+S88) | 57.76 | 57.76 | kg/s | 0.00 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass K37 | sum(S36+S89) | 57.76 | 57.76 | kg/s | 0.00 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass S90 split | sum(S38+S39) | 57.76 | 57.76 | kg/s | 7.105e-15 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass K12 | sum(S12+S162) | 522.40 | 522.40 | kg/s | 0.00 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass K14 | sum(S15+S17) | 522.40 | 522.40 | kg/s | 0.00 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass K66 | sum(S29+S74) | 439.34 | 439.34 | kg/s | 0.00 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass K16 | sum(S18+S20) | 438.59 | 438.59 | kg/s | 0.00 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass K19 | sum(S22+S24) | 50.45 | 50.46 | kg/s | -0.01 | -0.02 % | abs. err <= 0.02 kg/s |  |
| PASS | mass K45 FPB | sum(S38+S24) | 74.71 | 74.71 | kg/s | 1.421e-14 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass K40 OPB | sum(S40+S23) | 33.50 | 33.50 | kg/s | 0.00 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass K49 | sum(S56+S72) | 76.61 | 76.61 | kg/s | 0.00 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass K48 | sum(S53+S71) | 33.97 | 33.97 | kg/s | 0.00 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass K50 MCC | sum(S59+S54+S79+S18) | 511.46 | 511.46 | kg/s | 0.00 | +0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | mass engine O2 | O2 to injector + preburners + HX | 439.33 | 439.34 | kg/s | -0.01 | -0.00 % | abs. err <= 0.02 kg/s |  |
| PASS | shaft LPFTP (reference data) | W_pumps + W_turbines | 0.000 | 0.000 | kW | 0.00 |  | abs. err <= 82.65 kW |  |
| **FAIL** | shaft LPFTP (model) | W_pumps + W_turbines | 92.11 | 0.000 | kW | 92.11 |  | abs. err <= 82.92 kW | pumps 2764 kW, turbines -2672 kW |
| PASS | shaft HPFTP (reference data) | W_pumps + W_turbines | 0.000 | 0.000 | kW | 0.00 |  | abs. err <= 1793.7 kW |  |
| PASS | shaft HPFTP (model) | W_pumps + W_turbines | -68.18 | 0.000 | kW | -68.18 |  | abs. err <= 1732.19 kW | pumps 57740 kW, turbines -57808 kW |
| PASS | shaft LPOTP (reference data) | W_pumps + W_turbines | 0.000 | 0.000 | kW | 0.00 |  | abs. err <= 41.88 kW |  |
| PASS | shaft LPOTP (model) | W_pumps + W_turbines | 1.168 | 0.000 | kW | 1.17 |  | abs. err <= 41.8949 kW | pumps 1396 kW, turbines -1395 kW |
| PASS | shaft HPOTP (reference data) | W_pumps + W_turbines | 3.000 | 0.000 | kW | 3.00 |  | abs. err <= 653.19 kW |  |
| PASS | shaft HPOTP (model) | W_pumps + W_turbines | -11.30 | 0.000 | kW | -11.30 |  | abs. err <= 652.938 kW | pumps 21765 kW, turbines -21776 kW |

## Reference-data consistency

| Status | Item | Quantity | Computed | Reference | Unit | Error | Rel. error | Criterion | Note |
|---|---|---|---|---|---|---|---|---|---|
| PASS | K25 LPFP power vs states | m*dh(reference states) | 2715.59 | 2755.00 | kW | -39.41 | -1.43 % | rel. err <= 3 % | checks the reference data, not the model |
| **FAIL** | K26 HPFP power vs states | m*dh(reference states) | 57687.32 | 59790.00 | kW | -2102.68 | -3.52 % | rel. err <= 3 % | checks the reference data, not the model |
| **FAIL** | K34 LPFT power vs states | m*dh(reference states) | -2617.73 | -2755.00 | kW | 137.27 | +4.98 % | rel. err <= 3 % | checks the reference data, not the model |
| PASS | K10 LPOP power vs states | m*dh(reference states) | 1423.04 | 1396.00 | kW | 27.04 | +1.94 % | rel. err <= 3 % | checks the reference data, not the model |
| PASS | K13 HPOP power vs states | m*dh(reference states) | 20466.92 | 20510.00 | kW | -43.08 | -0.21 % | rel. err <= 3 % | checks the reference data, not the model |
| PASS | K15 LPOT power vs states | m*dh(reference states) | -1392.96 | -1396.00 | kW | 3.04 | +0.22 % | rel. err <= 3 % | checks the reference data, not the model |
| PASS | K18 power vs states | m*dh(reference states) | 1266.88 | 1263.00 | kW | 3.88 | +0.31 % | rel. err <= 3 % | checks the reference data, not the model |

## Property model vs reference densities

| Status | Item | Quantity | Computed | Reference | Unit | Error | Rel. error | Criterion | Note |
|---|---|---|---|---|---|---|---|---|---|
| PASS | rho S31 | rho(P_ref, T_ref) | 70.72 | 70.57 | kg/m3 | 0.15 | +0.21 % | rel. err <= 0.5 % |  |
| PASS | rho S32 | rho(P_ref, T_ref) | 70.64 | 70.52 | kg/m3 | 0.12 | +0.17 % | rel. err <= 0.5 % |  |
| PASS | rho S33 | rho(P_ref, T_ref) | 80.12 | 80.32 | kg/m3 | -0.20 | -0.25 % | rel. err <= 0.5 % |  |
| PASS | rho S58 | rho(P_ref, T_ref) | 78.29 | 78.52 | kg/m3 | -0.23 | -0.30 % | rel. err <= 0.5 % |  |
| PASS | rho S87 | rho(P_ref, T_ref) | 78.29 | 78.58 | kg/m3 | -0.29 | -0.38 % | rel. err <= 0.5 % |  |
| PASS | rho S36 | rho(P_ref, T_ref) | 30.85 | 30.97 | kg/m3 | -0.12 | -0.37 % | rel. err <= 0.5 % |  |
| PASS | rho S89 | rho(P_ref, T_ref) | 75.78 | 75.95 | kg/m3 | -0.17 | -0.23 % | rel. err <= 0.5 % |  |
| **FAIL** | rho S43 | rho(P_ref, T_ref) | 26.40 | 26.54 | kg/m3 | -0.14 | -0.52 % | rel. err <= 0.5 % |  |
| PASS | rho S44 | rho(P_ref, T_ref) | 21.75 | 21.76 | kg/m3 | -0.01 | -0.06 % | rel. err <= 0.5 % |  |
| PASS | rho S56 | ideal-gas rho(P_ref, T_ref) | 11.78 | 11.78 | kg/m3 | 0.003783 | +0.03 % | rel. err <= 0.5 % | validates the computed gas composition (mean molar mass) |
| PASS | rho S59 | ideal-gas rho(P_ref, T_ref) | 11.91 | 11.91 | kg/m3 | -0.004511 | -0.04 % | rel. err <= 0.5 % | validates the computed gas composition (mean molar mass) |
| PASS | rho S50 | ideal-gas rho(P_ref, T_ref) | 18.93 | 18.93 | kg/m3 | -7.91e-06 | -0.00 % | rel. err <= 0.5 % | validates the computed gas composition (mean molar mass) |
| PASS | rho S51 | ideal-gas rho(P_ref, T_ref) | 13.46 | 13.46 | kg/m3 | 0.0006346 | +0.00 % | rel. err <= 0.5 % | validates the computed gas composition (mean molar mass) |
| PASS | rho S53 | ideal-gas rho(P_ref, T_ref) | 13.31 | 13.31 | kg/m3 | 0.002742 | +0.02 % | rel. err <= 0.5 % | validates the computed gas composition (mean molar mass) |
| PASS | rho S54 | ideal-gas rho(P_ref, T_ref) | 13.39 | 13.39 | kg/m3 | -0.002161 | -0.02 % | rel. err <= 0.5 % | validates the computed gas composition (mean molar mass) |
| PASS | rho S11 | rho(P_ref, T_ref) | 1137.94 | 1137.99 | kg/m3 | -0.05 | -0.00 % | rel. err <= 0.5 % |  |
| PASS | rho S12 | rho(P_ref, T_ref) | 1137.16 | 1137.38 | kg/m3 | -0.22 | -0.02 % | rel. err <= 0.5 % |  |
| PASS | rho S162 | rho(P_ref, T_ref) | 1056.81 | 1056.78 | kg/m3 | 0.03 | +0.00 % | rel. err <= 0.5 % |  |
| PASS | rho S13 | rho(P_ref, T_ref) | 1124.80 | 1125.00 | kg/m3 | -0.20 | -0.02 % | rel. err <= 0.5 % |  |
| PASS | rho S14 | rho(P_ref, T_ref) | 1127.79 | 1127.96 | kg/m3 | -0.17 | -0.01 % | rel. err <= 0.5 % |  |
| PASS | rho S160 | rho(P_ref, T_ref) | 1056.81 | 1056.78 | kg/m3 | 0.03 | +0.00 % | rel. err <= 0.5 % |  |
| PASS | rho S21 | rho(P_ref, T_ref) | 1141.31 | 1141.64 | kg/m3 | -0.33 | -0.03 % | rel. err <= 0.5 % |  |
| PASS | rho S80 | rho(P_ref, T_ref) | 199.69 | 199.71 | kg/m3 | -0.02 | -0.01 % | rel. err <= 0.5 % |  |
| PASS | rho S69 | rho(P_ref, T_ref) | 1.939 | 1.940 | kg/m3 | -0.0009499 | -0.05 % | rel. err <= 0.5 % |  |

## Additional results (no acceptance criterion)

| Status | Item | Quantity | Computed | Reference | Unit | Error | Rel. error | Criterion | Note |
|---|---|---|---|---|---|---|---|---|---|
| info | K38 OPB fuel valve | T(S40) | 165.20 |  | K |  |  | info |  |
| info | K61+K20 valves | T(S23) | 122.86 |  | K |  |  | info |  |
| info | HPFT | eta (implied) | 0.780 |  | - |  |  | info |  |
| info | K50 MCC | T_ad at P(S62), no heat loss | 3646.24 | 3613.00 | K | 33.24 | +0.92 % | info | compare: reference S62 |
| info | nozzle shifting | T(S68) | 1261.49 | 1139.30 | K | 122.19 | +10.72 % | info |  |
| info | nozzle shifting | v(S68) | 4444.43 | 4351.20 | m/s | 93.23 | +2.14 % | info |  |
| info | nozzle shifting | M(S68) | 4.615 | 4.734 | - | -0.12 | -2.50 % | info |  |
| info | nozzle frozen_throat | T(S68) | 1056.30 | 1139.30 | K | -83.00 | -7.29 % | info |  |
| info | nozzle frozen_throat | v(S68) | 4302.07 | 4351.20 | m/s | -49.13 | -1.13 % | info |  |
| info | nozzle frozen_throat | M(S68) | 4.753 | 4.734 | - | 0.02 | +0.41 % | info |  |
| info | nozzle frozen | T(S68) | 999.95 | 1139.30 | K | -139.35 | -12.23 % | info |  |
| info | nozzle frozen | v(S68) | 4245.51 | 4351.20 | m/s | -105.69 | -2.43 % | info |  |
| info | nozzle frozen | M(S68) | 4.780 | 4.734 | - | 0.05 | +0.97 % | info |  |
| info | nozzle shifting | v(S68) with K52+K53 loss | 4423.37 | 4351.20 | m/s | 72.17 | +1.66 % | info | original script subtracted both heat flows |
| info | mass engine H2 | H2 to burners + MCC | 72.88 | 73.22 | kg/s | -0.34 | -0.46 % | info | difference = GH2 tank pressurant (not listed in the data) |

## Main chamber composition (mass fractions)

H2: 0.0364, O2: 0.0056, H2O: 0.9050, H: 0.0019, O: 0.0026, OH: 0.0483, HO2: 0.0001, H2O2: 0.0000
