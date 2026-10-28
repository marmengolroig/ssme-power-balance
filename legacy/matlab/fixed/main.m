%% SSME power balance - corrected MATLAB version (component validation)
%
% This is the original main.m with the errors listed in docs/CODE_REVIEW.md fixed. Each fix is
% tagged "FIX(n)" with the number used in that document. The Python package in src/ssme is the
% maintained version; this script is kept so that the two can be cross-checked
% (run export_results.m, then pytest compares both).
%
% Every component is fed with its REFERENCE inlet state and its outlet is compared with the
% reference outlet (component validation, FIX(10)). Errors therefore do not propagate.
%
% Requirements: HGS (https://github.com/ManelSoria/HGS) and INIST
% (https://github.com/ManelSoria/INIST). INIST's NFP uses fsolve (Optimization Toolbox) and
% HGSeq uses fmincon (Optimization Toolbox).
%
% NOTE: this file was corrected by review and has not been executed in MATLAB yet.

clear; close all; clc;

%% Paths (FIX(15): no hard-coded absolute paths). Set HGS_DIR / INIST_DIR or clone them next to the repo.
here = fileparts(mfilename('fullpath'));
HGS_DIR = getenv('HGS_DIR');
if isempty(HGS_DIR), HGS_DIR = fullfile(here, '..', '..', '..', '..', 'HGS'); end
INIST_DIR = getenv('INIST_DIR');
if isempty(INIST_DIR), INIST_DIR = fullfile(here, '..', '..', '..', '..', 'INIST'); end
addpath(HGS_DIR); addpath(INIST_DIR);

FUEL = 'pH2';   % FIX(1): the reference data were generated with PARA-hydrogen, not normal 'H2'
OX   = 'O2';
SP   = {'H2','O2','H2O','H','O','OH','HO2','H2O2'};   % FIX(8): atomic H included; FIX(7): one fixed cellstr order

R = struct();   % results exported by export_results.m

%% ======================================================================= FUEL SIDE
%% K25 LPFP: S31 -> S32
S31 = station(73.22, 2.07, 20.6, 70.57);
S32 = station(73.22, 19.50, 22.7, 70.52);
K25.etais = 0.650;  K25.Wref = 2.755e3;                                  % kW
[S32.T, K25.W] = pump(FUEL, S31.P, S31.Tref, S32.P, S31.m_dot, K25.etais);
K25.W_relErr = relativeError(K25.Wref, K25.W);
S32.T_relErr = relativeError(S32.Tref, S32.T);
R.T32 = S32.T;  R.K25_W = K25.W;

%% K26 HPFP: S32 -> S33
S33 = station(73.22, 486.49, 57.3, 80.32);
K26.etais = 0.730;  K26.Wref = 59.79e3;
[S33.T, K26.W] = pump(FUEL, S32.P, S32.Tref, S33.P, S32.m_dot, K26.etais);
K26.W_relErr = relativeError(K26.Wref, K26.W);   % ~ -3.4 %: W_ref is inconsistent with the reference states (FIX(17))
S33.T_relErr = relativeError(S33.Tref, S33.T);
R.T33 = S33.T;  R.K26_W = K26.W;

%% K64 main fuel valve: S33 -> S58 (isenthalpic; was only a pressure/temperature ratio, FIX(14))
S58 = station(73.22, 463.32, 59.1, 78.52);
[S58.T, ~, ~] = IsentalpicValve(FUEL, S33.P, S33.Tref, S33.P / S58.P);
S58.T_relErr = relativeError(S58.Tref, S58.T);
R.T58 = S58.T;

%% Splitters K27 (S34, S41) and K35 (S87, S88): same state as S58
S34.m_dot = 57.76;
[S34.m_dot, S41.m_dot] = splitter(S58.m_dot, S34.m_dot);     % S41 = 15.46 kg/s (MCC coolant)
[S87.m_dot, S88.m_dot] = splitter(S34.m_dot, 28.88);

%% K28 nozzle coolant HX: S87 -> S36   (FIX(2): pressure ratio; FIX(15): duplicate block removed)
S36 = station(28.88, 431.40, 257.8, 30.97);
K28.Q = 93.13e3;  K28.PR = 1.074;                                         % kW, P_in/P_out
[S36.T, S36.Pcomp] = heatexanger(FUEL, S58.P, S58.Tref, S87.m_dot, K28.Q, K28.PR);
S36.T_relErr = relativeError(S36.Tref, S36.T);
S36.P_relErr = relativeError(S36.P, S36.Pcomp);
R.T36 = S36.T;  R.P36 = S36.Pcomp;

%% K36 coolant control valve: S88 -> S89 (FIX(14): new check)
S89 = station(28.88, 431.40, 61.4, 75.95);
[S89.T, ~, ~] = IsentalpicValve(FUEL, S58.P, S58.Tref, S58.P / S89.P);
S89.T_relErr = relativeError(S89.Tref, S89.T);
R.T89 = S89.T;

%% K37 mixer: S36 + S89 -> S90
S90 = station(57.76, 431.40, 163.3, NaN);   % rho in the original (30.97) was copied from S36 (FIX(17))
S90.T = mixer(FUEL, S90.P, S36.P, S89.P, S36.Tref, S89.Tref, S36.m_dot, S89.m_dot);
S90.T_relErr = relativeError(S90.Tref, S90.T);
R.T90 = S90.T;

%% MCC coolant jacket (heat K52): S41 -> S43 (FIX(14): new check)
S43 = station(15.46, 345.50, 252.8, 26.54);
K52.Q = 47.77e3;
[S43.T, ~] = heatexanger(FUEL, S58.P, S58.Tref, S41.m_dot, K52.Q, S58.P / S43.P);
S43.T_relErr = relativeError(S43.Tref, S43.T);
R.T43 = S43.T;

%% K34 LPFT: S43 -> S44
S44 = station(15.46, 261.36, 244.8, 21.76);
K34.etais = 0.520;  K34.Wref = -2.755e3;
[S44.T, K34.W] = turbine(FUEL, S43.P, S43.Tref, S44.P, S43.m_dot, K34.etais);
K34.W_relErr = relativeError(K34.Wref, K34.W);
S44.T_relErr = relativeError(S44.Tref, S44.T);
R.T44 = S44.T;  R.K34_W = K34.W;

%% S90 -> S38 (fuel preburner) + S39 (oxidizer preburner);  K38 OPB fuel valve: S39 -> S40
S38 = station(37.82, 431.40, 163.3, NaN);
S39 = station(19.94, 431.40, 163.3, NaN);
K38.PR = 1.114;
[S40.T, S40.P, S40.rho] = IsentalpicValve(FUEL, S39.P, S39.Tref, K38.PR);
S40.m_dot = 19.94;                         % FIX(3): was 19.34 (S39 = 19.94; S51 = 19.94 + 13.56 = 33.50)
R.T40 = S40.T;  R.P40 = S40.P;

%% ======================================================================= OXIDIZER SIDE
%% K10 LPOP: S11 -> S12
S11 = station(439.34, 6.89, 91.1, 1137.99);
S12 = station(439.34, 29.70, 92.3, 1137.38);
K10.etais = 0.630;  K10.Wref = 1.396e3;
[S12.T, K10.W] = pump(OX, S11.P, S11.Tref, S12.P, S11.m_dot, K10.etais);
K10.W_relErr = relativeError(K10.Wref, K10.W);
S12.T_relErr = relativeError(S12.Tref, S12.T);
R.T12 = S12.T;  R.K10_W = K10.W;

%% K12 mixer: S12 + S162 -> S13   (FIX(16): the original overwrote K10.type here)
S162 = station(83.06, 29.70, 107.8, 1056.78);   % defined once (FIX(16))
S13  = station(522.40, 29.70, 94.8, 1125.00);
S13.T = mixer(OX, S13.P, S12.P, S162.P, S12.Tref, S162.Tref, S12.m_dot, S162.m_dot);
S13.T_relErr = relativeError(S13.Tref, S13.T);
R.T13 = S13.T;

%% K13 HPOP: S13 -> S14
S14 = station(522.40, 330.35, 108.9, 1127.96);
K13.etais = 0.670;  K13.Wref = 20.51e3;
[S14.T, K13.W] = pump(OX, S13.P, S13.Tref, S14.P, S13.m_dot, K13.etais);
K13.W_relErr = relativeError(K13.Wref, K13.W);
S14.T_relErr = relativeError(S14.Tref, S14.T);
R.T14 = S14.T;  R.K13_W = K13.W;

%% K14 splitter: S15 (to LPOT) and S17   (FIX(16): the original set S15.P/T in the S17 block)
[S15.m_dot, S17.m_dot] = splitter(S14.m_dot, 83.06);

%% K15 LPOT: S15 -> S160
S160 = station(83.06, 29.70, 107.8, 1056.78);
K15.etais = 0.620;  K15.Wref = -1.396e3;
[S160.T, K15.W] = turbine(OX, S14.P, S14.Tref, S160.P, S15.m_dot, K15.etais);
K15.W_relErr = relativeError(K15.Wref, K15.W);
S160.T_relErr = relativeError(S160.Tref, S160.T);
R.T160 = S160.T;  R.K15_W = K15.W;

%% K66 splitter: S29 and S74;  K16 splitter: S18 (main injector) and S20 (PBP)
[S29.m_dot, S74.m_dot] = splitter(S17.m_dot, 438.59);        % FIX(10): computed S17, not S17.m_dot_ref
[S18.m_dot, S20.m_dot] = splitter(S29.m_dot, 388.13);

%% K18 preburner boost pump: S20 -> S21
S21 = station(50.46, 558.71, 116.8, 1141.64);   % FIX(3): m_dot was 50.16 (S20 = 50.46 = S22 + S24)
K18.etais = 0.800;  K18.Wref = 1.263e3;
[S21.T, K18.W] = pump(OX, S14.P, S14.Tref, S21.P, S20.m_dot, K18.etais);
K18.W_relErr = relativeError(K18.Wref, K18.W);
S21.T_relErr = relativeError(S21.Tref, S21.T);
R.T21 = S21.T;  R.K18_W = K18.W;

%% K67 oxidizer HX: S74 -> S80
S80 = station(0.75, 285.53, 507.8, 199.71);
K67.Q = 0.4051e3;  K67.PR = 1.157;
[S80.T, S80.Pcomp] = heatexanger(OX, S14.P, S14.Tref, S74.m_dot, K67.Q, K67.PR);
S80.T_relErr = relativeError(S80.Tref, S80.T);
S80.P_relErr = relativeError(S80.P, S80.Pcomp);
R.T80 = S80.T;  R.P80 = S80.Pcomp;

%% K70 pressurant valve: S80 -> S69   (FIX(2): true ratio 285.53/2.49 instead of the tuned 1.991)
S69 = station(0.75, 2.49, 494.0, 1.94);
[S69.T, S69.Pcomp, S69.rho] = IsentalpicValve(OX, S80.P, S80.Tref, S80.P / S69.P);
S69.T_relErr   = relativeError(S69.Tref, S69.T);
S69.rho_relErr = relativeError(S69.rho_ref, S69.rho);
R.T69 = S69.T;  R.rho69 = S69.rho;

%% K19 splitter: S22 (OPB) and S24 (FPB);  K61 + K20 valves: S22 -> S26 -> S23
[S22.m_dot, S24.m_dot] = splitter(S21.m_dot, 13.56);          % S24 = 36.90 (ref 36.89)
K61.PR = 1.182;  K20.PR = 1.221;
[S26.T, S26.P, ~] = IsentalpicValve(OX, S21.P, S21.Tref, K61.PR);
[S23.T, S23.P, ~] = IsentalpicValve(OX, S26.P, S26.T, K20.PR);
S23.m_dot = S22.m_dot;
R.T23 = S23.T;  R.P23 = S23.P;                                % P23 ~ 387.1 bar = OPB pressure

%% ======================================================================= HOT-GAS SIDE
%% K45 fuel preburner: S38 + S24 -> S55  (FIX(6): adiabatic equilibrium, T predicted)
S55 = station(74.71, 391.47, 1105.6, NaN);
[nH, HH] = realfluid_to_gas(SP, FUEL, S38.m_dot, S38.P, S38.Tref);
[nO, HO] = realfluid_to_gas(SP, OX,   36.89, S21.P, S21.Tref);   % reference S24 flow (splitter gives 36.90)
[S55.T, S55.n] = burner_hp(SP, nH + nO, HH + HO, S55.P, 0);
S55.T_relErr = relativeError(S55.Tref, S55.T);
R.T55 = S55.T;

%% HP fuel turbine: S55 -> S56 (not in the original; power and efficiency from reference states)
S56 = station(74.71, 248.21, 1008.9, 11.78);
[~, HPFT.W, HPFT.eta] = turbine_mix(SP, S55.n, S55.P, S55.Tref, S56.P, [], S56.Tref);
R.HPFT_W = HPFT.W;  R.HPFT_eta = HPFT.eta;                     % compare with -K26.W

%% K49 mixer: S56 + S72 -> S59 (frozen composition)
S59 = station(76.61, 248.21, 975.0, 11.91);
S72 = station(1.90, 248.21, 244.8, NaN);   % rho in the original (21.76) was copied from S44
[n72, H72] = realfluid_to_gas(SP, FUEL, S72.m_dot, S72.P, S72.Tref);
H56 = HGSprop(SP, S55.n, S56.Tref, S56.P, 'H');
S59.n = S55.n + n72;
S59.T = mixer_gas(SP, S59.n, H56 + H72, S59.P);
S59.T_relErr = relativeError(S59.Tref, S59.T);
R.T59 = S59.T;

%% K40 oxidizer preburner: S40 + S23 -> S50 (was skipped in mainLOX.m; struct K45 was reused)
S50 = station(33.50, 387.25, 833.33, 18.93);
[nH, HH] = realfluid_to_gas(SP, FUEL, S40.m_dot, S40.P, S40.T);
[nO, HO] = realfluid_to_gas(SP, OX,   S23.m_dot, S23.P, S23.T);
[S50.T, S50.n] = burner_hp(SP, nH + nO, HH + HO, S50.P, 0);
S50.T_relErr = relativeError(S50.Tref, S50.T);
R.T50 = S50.T;

%% K41 HPOT: S50 -> S51 (FIX(5): H2/H2O mixture, frozen)
S51 = station(33.50, 251.43, 760.9, 13.46);
K41.etais = 0.780;  K41.Wref = -21.77e3;
[S51.T, K41.W] = turbine_mix(SP, S50.n, S50.P, S50.Tref, S51.P, K41.etais);
K41.W_relErr = relativeError(K41.Wref, K41.W);
S51.T_relErr = relativeError(S51.Tref, S51.T);
R.T51 = S51.T;  R.K41_W = K41.W;

%% K48 mixer: S53 + S71 -> S54 (frozen composition)
S53 = station(33.50, 248.21, 759.5, 13.31);
S54 = station(33.97, 248.21, 748.2, 13.39);
S71 = station(0.47, 248.21, 244.8, NaN);
[n71, H71] = realfluid_to_gas(SP, FUEL, S71.m_dot, S71.P, S71.Tref);
H53 = HGSprop(SP, S50.n, S53.Tref, S53.P, 'H');
S54.n = S50.n + n71;
S54.T = mixer_gas(SP, S54.n, H53 + H71, S54.P);
S54.T_relErr = relativeError(S54.Tref, S54.T);
R.T54 = S54.T;

%% K50 main combustion chamber: S59 + S54 + S79 + S19 -> S62 / S63
S79 = station(12.75, 248.21, 244.8, NaN);   % P, T not given in the original: assumed as S71/S72
[n79, H79] = realfluid_to_gas(SP, FUEL, S79.m_dot, S79.P, S79.Tref);
[n19, H19] = realfluid_to_gas(SP, OX,   S18.m_dot, S14.P, S14.Tref);
H59 = HGSprop(SP, S59.n, S59.Tref, S59.P, 'H');
H54 = HGSprop(SP, S54.n, S54.Tref, S54.P, 'H');
n_mcc = S59.n + S54.n + n79 + n19;           % FIX(7): numeric vectors in one fixed species order
H_mcc = H59 + H54 + H79 + H19;
S62 = station(511.46, 225.10, 3613.0, NaN);
S63 = station(511.46, 219.70, 3683.6, NaN);
[S62.T_ad, ~] = burner_hp(SP, n_mcc, H_mcc, S62.P, 0);
[S63.T, ~]    = burner_hp(SP, n_mcc, H_mcc, S63.P, K52.Q);
R.T_ad_MCC = S62.T_ad;  R.T63_loss = S63.T;

%% Nozzle: chamber at the reference S63 state, shifting equilibrium to S86/S68
[~, S63.n, ~] = HGSeq(SP, n_mcc, S63.Tref, S63.P);
S68 = station(511.46, 0.19243, 1139.3, 0.02874);
S68.vref = 4351.2;  S68.Mref = 4.734;
K53.Q = 93.13e3;
[S68.T, S68.v, S68.a, S68.M] = nozzle_exit(SP, S63.n, S63.Tref, S63.P, S68.P, K53.Q, 'Shifting');  % FIX(9): K53 only
S68.v_relErr = relativeError(S68.vref, S68.v);
S68.M_relErr = relativeError(S68.Mref, S68.M);
S68.T_relErr = relativeError(S68.Tref, S68.T);
R.T68 = S68.T;  R.v68 = S68.v;  R.M68 = S68.M;

%% Summary
fprintf('\n%-28s %12s %12s %9s\n', 'quantity', 'computed', 'reference', 'rel.err%');
rows = {'T(S32) K25', S32.T, S32.Tref; 'W K25 [kW]', K25.W, K25.Wref; 'T(S33) K26', S33.T, S33.Tref; ...
        'W K26 [kW]', K26.W, K26.Wref; 'T(S36) K28', S36.T, S36.Tref; 'T(S90) K37', S90.T, S90.Tref; ...
        'T(S43) MCC jacket', S43.T, S43.Tref; 'T(S44) K34', S44.T, S44.Tref; 'W K34 [kW]', K34.W, K34.Wref; ...
        'T(S12) K10', S12.T, S12.Tref; 'T(S13) K12', S13.T, S13.Tref; 'T(S14) K13', S14.T, S14.Tref; ...
        'T(S160) K15', S160.T, S160.Tref; 'T(S21) K18', S21.T, S21.Tref; 'T(S80) K67', S80.T, S80.Tref; ...
        'T(S69) K70', S69.T, S69.Tref; 'T(S55) FPB', S55.T, S55.Tref; 'T(S59) K49', S59.T, S59.Tref; ...
        'T(S50) OPB', S50.T, S50.Tref; 'T(S51) K41', S51.T, S51.Tref; 'W K41 [kW]', K41.W, K41.Wref; ...
        'T(S54) K48', S54.T, S54.Tref; 'T(S63) MCC', S63.T, S63.Tref; 'T(S68) nozzle', S68.T, S68.Tref; ...
        'v(S68) nozzle', S68.v, S68.vref; 'M(S68) nozzle', S68.M, S68.Mref};
for i = 1:size(rows, 1)
    fprintf('%-28s %12.3f %12.3f %+9.3f\n', rows{i,1}, rows{i,2}, rows{i,3}, relativeError(rows{i,3}, rows{i,2}));
end

%% ----------------------------------------------------------------------- local functions
function s = station(m_dot, P, Tref, rho_ref)
%STATION Reference data of a station (m_dot [kg/s], P [bar], Tref [K], rho_ref [kg/m^3]).
    s = struct('m_dot', m_dot, 'P', P, 'Tref', Tref, 'rho_ref', rho_ref);
end
