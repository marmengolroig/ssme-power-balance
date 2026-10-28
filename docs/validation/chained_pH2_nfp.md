# SSME cycle - validation report

- Mode: **chained**  |  hydrogen: **pH2**  |  real-fluid backend: **nfp**  |  nozzle model: **shifting**
- Checks: 89 pass, 4 fail, 15 informative
- Generated: 2026-10-06 with `python -m ssme`

## Failed checks

- K26 HPFP - W: 57797.33 vs 59790.00 kW (-3.33 %)
- duct S51-S53 - T(S53): 767.21 vs 759.50 K (+1.02 %)
- K50 MCC - T(S63): 3633.09 vs 3683.60 K (-1.37 %)
- K26 HPFP power vs states - m*dh(reference states): 57831.71 vs 59790.00 kW (-3.28 %)

## Component validation

| Status | Item | Quantity | Computed | Reference | Unit | Error | Rel. error | Criterion | Note |
|---|---|---|---|---|---|---|---|---|---|
| PASS | K25 LPFP | T(S32) | 22.76 | 22.70 | K | 0.06 | +0.25 % | abs. err <= 2 K |  |
| PASS | K25 LPFP | W | 2753.84 | 2755.00 | kW | -1.16 | -0.04 % | rel. err <= 3 % |  |
| PASS | K26 HPFP | T(S33) | 57.31 | 57.30 | K | 0.00892 | +0.02 % | abs. err <= 2 K |  |
| **FAIL** | K26 HPFP | W | 57797.33 | 59790.00 | kW | -1992.67 | -3.33 % | rel. err <= 3 % |  |
| PASS | K64 MFV | T(S58) | 59.07 | 59.10 | K | -0.03 | -0.06 % | abs. err <= 2 K | isenthalpic valve (new check) |
| PASS | K28 nozzle HX | T(S36) | 258.13 | 257.80 | K | 0.33 | +0.13 % | rel. err <= 1 % |  |
| PASS | K28 nozzle HX | P(S36) | 431.40 | 431.40 | bar | -0.003352 | -0.00 % | rel. err <= 0.5 % | P_out = P_in / PR |
| PASS | K36 CCV | T(S89) | 61.40 | 61.40 | K | 0.001996 | +0.00 % | abs. err <= 2 K | isenthalpic valve (new check) |
| PASS | K37 mixer | T(S90) | 163.40 | 163.30 | K | 0.10 | +0.06 % | abs. err <= 2 K |  |
| PASS | MCC coolant jacket | T(S43) | 253.18 | 252.80 | K | 0.38 | +0.15 % | rel. err <= 1 % | Q = K52 = 47.77 MW (new check) |
| PASS | K34 LPFT | T(S44) | 245.55 | 244.80 | K | 0.75 | +0.31 % | rel. err <= 1 % |  |
| PASS | K34 LPFT | W | -2679.62 | -2755.00 | kW | 75.38 | +2.74 % | rel. err <= 3 % |  |
| PASS | K38 OPB fuel valve | P(S40) | 387.25 | 387.25 | bar | 0.003142 | +0.00 % | rel. err <= 0.5 % | P_out = P_in / PR |
| PASS | K10 LPOP | T(S12) | 92.26 | 92.30 | K | -0.04 | -0.04 % | abs. err <= 2 K |  |
| PASS | K10 LPOP | W | 1396.50 | 1396.00 | kW | 0.50 | +0.04 % | rel. err <= 3 % |  |
| PASS | K12 mixer | T(S13) | 94.77 | 94.80 | K | -0.03 | -0.03 % | abs. err <= 2 K |  |
| PASS | K13 HPOP | T(S14) | 108.91 | 108.90 | K | 0.005687 | +0.01 % | abs. err <= 2 K |  |
| PASS | K13 HPOP | W | 20499.02 | 20510.00 | kW | -10.98 | -0.05 % | rel. err <= 3 % |  |
| PASS | K15 LPOT | T(S160) | 107.79 | 107.80 | K | -0.01 | -0.01 % | abs. err <= 2 K |  |
| PASS | K15 LPOT | W | -1395.36 | -1396.00 | kW | 0.64 | +0.05 % | rel. err <= 3 % |  |
| PASS | K18 | T(S21) | 116.75 | 116.80 | K | -0.05 | -0.04 % | abs. err <= 2 K |  |
| PASS | K18 | W | 1262.90 | 1263.00 | kW | -0.10 | -0.01 % | rel. err <= 3 % |  |
| PASS | K67 ox HX | T(S80) | 507.71 | 507.80 | K | -0.09 | -0.02 % | rel. err <= 1 % |  |
| PASS | K67 ox HX | P(S80) | 285.52 | 285.53 | bar | -0.007096 | -0.00 % | rel. err <= 0.5 % | P_out = P_in / PR |
| PASS | K70 valve | T(S69) | 493.89 | 494.00 | K | -0.11 | -0.02 % | rel. err <= 1 % |  |
| PASS | K70 valve | rho(S69) | 1.939 | 1.940 | kg/m3 | -0.000523 | -0.03 % | rel. err <= 0.5 % |  |
| PASS | K61+K20 valves | P(S23) | 387.13 | 387.25 | bar | -0.12 | -0.03 % | rel. err <= 0.5 % | P_out = P_in / PR; should equal OPB pressure |
| PASS | K45 fuel preburner | T(S55) | 1115.39 | 1105.60 | K | 9.79 | +0.89 % | rel. err <= 1 % | adiabatic equilibrium (was imposed) |
| PASS | HPFT | T(S56) | 1018.89 | 1008.90 | K | 9.99 | +0.99 % | rel. err <= 1 % | closed with HPFTP shaft balance W = -W(K26) |
| PASS | K49 mixer | T(S59) | 984.36 | 975.00 | K | 9.36 | +0.96 % | rel. err <= 1 % |  |
| PASS | K40 ox preburner | T(S50) | 840.20 | 833.33 | K | 6.87 | +0.82 % | rel. err <= 1 % | adiabatic equilibrium (was skipped) |
| PASS | K41 HPOT | T(S51) | 767.21 | 760.90 | K | 6.31 | +0.83 % | rel. err <= 1 % | frozen ideal-gas mixture (was pure H2) |
| PASS | K41 HPOT | W | -21956.64 | -21770.00 | kW | -186.64 | -0.86 % | rel. err <= 3 % |  |
| **FAIL** | duct S51-S53 | T(S53) | 767.21 | 759.50 | K | 7.71 | +1.02 % | rel. err <= 1 % | adiabatic duct, ideal gas: T unchanged |
| PASS | K48 mixer | T(S54) | 755.63 | 748.20 | K | 7.43 | +0.99 % | rel. err <= 1 % |  |
| **FAIL** | K50 MCC | T(S63) | 3633.09 | 3683.60 | K | -50.51 | -1.37 % | rel. err <= 1 % | equilibrium, heat loss K52 = 47.77 MW |

## System-level validation

| Status | Item | Quantity | Computed | Reference | Unit | Error | Rel. error | Criterion | Note |
|---|---|---|---|---|---|---|---|---|---|
| PASS | nozzle envelope | T(S68) | 1216.63 | 1139.30 | K | 77.33 | +6.79 % | reference within [988.1, 1217] | computed = shifting; heat loss K53 only |
| PASS | nozzle envelope | v(S68) | 4386.54 | 4351.20 | m/s | 35.34 | +0.81 % | reference within [4207, 4387] | computed = shifting; heat loss K53 only |
| PASS | nozzle envelope | M(S68) | 4.632 | 4.734 | - | -0.10 | -2.15 % | reference within [4.632, 4.778] | computed = shifting; heat loss K53 only |

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
| PASS | shaft LPFTP (model) | W_pumps + W_turbines | 74.22 | 0.000 | kW | 74.22 |  | abs. err <= 82.6152 kW | pumps 2754 kW, turbines -2680 kW |
| PASS | shaft HPFTP (reference data) | W_pumps + W_turbines | 0.000 | 0.000 | kW | 0.00 |  | abs. err <= 1793.7 kW |  |
| PASS | shaft HPFTP (model) | W_pumps + W_turbines | 2.183e-11 | 0.000 | kW | 2.183e-11 |  | abs. err <= 1733.92 kW | pumps 57797 kW, turbines -57797 kW |
| PASS | shaft LPOTP (reference data) | W_pumps + W_turbines | 0.000 | 0.000 | kW | 0.00 |  | abs. err <= 41.88 kW |  |
| PASS | shaft LPOTP (model) | W_pumps + W_turbines | 1.141 | 0.000 | kW | 1.14 |  | abs. err <= 41.8949 kW | pumps 1396 kW, turbines -1395 kW |
| PASS | shaft HPOTP (reference data) | W_pumps + W_turbines | 3.000 | 0.000 | kW | 3.00 |  | abs. err <= 653.19 kW |  |
| PASS | shaft HPOTP (model) | W_pumps + W_turbines | -194.72 | 0.000 | kW | -194.72 |  | abs. err <= 652.858 kW | pumps 21762 kW, turbines -21957 kW |

## Reference-data consistency

| Status | Item | Quantity | Computed | Reference | Unit | Error | Rel. error | Criterion | Note |
|---|---|---|---|---|---|---|---|---|---|
| PASS | K25 LPFP power vs states | m*dh(reference states) | 2712.14 | 2755.00 | kW | -42.86 | -1.56 % | rel. err <= 3 % | checks the reference data, not the model |
| **FAIL** | K26 HPFP power vs states | m*dh(reference states) | 57831.71 | 59790.00 | kW | -1958.29 | -3.28 % | rel. err <= 3 % | checks the reference data, not the model |
| PASS | K34 LPFT power vs states | m*dh(reference states) | -2773.27 | -2755.00 | kW | -18.27 | -0.66 % | rel. err <= 3 % | checks the reference data, not the model |
| PASS | K10 LPOP power vs states | m*dh(reference states) | 1423.04 | 1396.00 | kW | 27.04 | +1.94 % | rel. err <= 3 % | checks the reference data, not the model |
| PASS | K13 HPOP power vs states | m*dh(reference states) | 20466.92 | 20510.00 | kW | -43.08 | -0.21 % | rel. err <= 3 % | checks the reference data, not the model |
| PASS | K15 LPOT power vs states | m*dh(reference states) | -1392.96 | -1396.00 | kW | 3.04 | +0.22 % | rel. err <= 3 % | checks the reference data, not the model |
| PASS | K18 power vs states | m*dh(reference states) | 1266.88 | 1263.00 | kW | 3.88 | +0.31 % | rel. err <= 3 % | checks the reference data, not the model |

## Property model vs reference densities

| Status | Item | Quantity | Computed | Reference | Unit | Error | Rel. error | Criterion | Note |
|---|---|---|---|---|---|---|---|---|---|
| PASS | rho S31 | rho(P_ref, T_ref) | 70.56 | 70.57 | kg/m3 | -0.01 | -0.01 % | rel. err <= 0.5 % |  |
| PASS | rho S32 | rho(P_ref, T_ref) | 70.56 | 70.52 | kg/m3 | 0.04 | +0.05 % | rel. err <= 0.5 % |  |
| PASS | rho S33 | rho(P_ref, T_ref) | 80.26 | 80.32 | kg/m3 | -0.06 | -0.07 % | rel. err <= 0.5 % |  |
| PASS | rho S58 | rho(P_ref, T_ref) | 78.39 | 78.52 | kg/m3 | -0.13 | -0.17 % | rel. err <= 0.5 % |  |
| PASS | rho S87 | rho(P_ref, T_ref) | 78.39 | 78.58 | kg/m3 | -0.19 | -0.24 % | rel. err <= 0.5 % |  |
| PASS | rho S36 | rho(P_ref, T_ref) | 30.90 | 30.97 | kg/m3 | -0.07 | -0.21 % | rel. err <= 0.5 % |  |
| PASS | rho S89 | rho(P_ref, T_ref) | 75.83 | 75.95 | kg/m3 | -0.12 | -0.16 % | rel. err <= 0.5 % |  |
| PASS | rho S43 | rho(P_ref, T_ref) | 26.44 | 26.54 | kg/m3 | -0.10 | -0.38 % | rel. err <= 0.5 % |  |
| PASS | rho S44 | rho(P_ref, T_ref) | 21.76 | 21.76 | kg/m3 | 0.001943 | +0.01 % | rel. err <= 0.5 % |  |
| PASS | rho S56 | ideal-gas rho(P_ref, T_ref) | 11.79 | 11.78 | kg/m3 | 0.00536 | +0.05 % | rel. err <= 0.5 % | validates the computed gas composition (mean molar mass) |
| PASS | rho S59 | ideal-gas rho(P_ref, T_ref) | 11.91 | 11.91 | kg/m3 | -0.002957 | -0.02 % | rel. err <= 0.5 % | validates the computed gas composition (mean molar mass) |
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
| info | K38 OPB fuel valve | T(S40) | 164.94 |  | K |  |  | info |  |
| info | K61+K20 valves | T(S23) | 122.81 |  | K |  |  | info |  |
| info | HPFT | eta (required) | 0.773 |  | - |  |  | info |  |
| info | K50 MCC | T_ad at P(S62), no heat loss | 3648.08 | 3613.00 | K | 35.08 | +0.97 % | info | compare: reference S62 |
| info | nozzle shifting | T(S68) | 1216.63 | 1139.30 | K | 77.33 | +6.79 % | info |  |
| info | nozzle shifting | v(S68) | 4386.54 | 4351.20 | m/s | 35.34 | +0.81 % | info |  |
| info | nozzle shifting | M(S68) | 4.632 | 4.734 | - | -0.10 | -2.15 % | info |  |
| info | nozzle frozen_throat | T(S68) | 1040.90 | 1139.30 | K | -98.40 | -8.64 % | info |  |
| info | nozzle frozen_throat | v(S68) | 4260.52 | 4351.20 | m/s | -90.68 | -2.08 % | info |  |
| info | nozzle frozen_throat | M(S68) | 4.752 | 4.734 | - | 0.02 | +0.38 % | info |  |
| info | nozzle frozen | T(S68) | 988.14 | 1139.30 | K | -151.16 | -13.27 % | info |  |
| info | nozzle frozen | v(S68) | 4207.06 | 4351.20 | m/s | -144.14 | -3.31 % | info |  |
| info | nozzle frozen | M(S68) | 4.778 | 4.734 | - | 0.04 | +0.92 % | info |  |
| info | nozzle shifting | v(S68) with K52+K53 loss | 4365.20 | 4351.20 | m/s | 14.00 | +0.32 % | info | original script subtracted both heat flows |
| info | mass engine H2 | H2 to burners + MCC | 72.88 | 73.22 | kg/s | -0.34 | -0.46 % | info | difference = GH2 tank pressurant (not listed in the data) |

## Main chamber composition (mass fractions)

H2: 0.0364, O2: 0.0056, H2O: 0.9047, H: 0.0020, O: 0.0026, OH: 0.0485, HO2: 0.0001, H2O2: 0.0000
