clear;
close all;

addpath('D:\Altres\universitat\MUEA\Extension of Rocket Engine\HGS-main');
addpath('D:\Altres\universitat\MUEA\Extension of Rocket Engine\INIST-main');

%% After H2 tank K24: S31
S31.sp = "H2";
S31.m_dot = 73.22;              % [kg/s]
S31.P = 2.07;                   % [bar]
S31.T = 20.6;                   % [K]
S31.rho = 70.57;                % [kg/m^3]
S31.V_dot = S31.m_dot/S31.rho;     % [m^3/s]

%% After H2 pump K25: S32
% K25
K25.type = "pump";
K25.etais = 0.650;
K25.Wref = 2.755e3;             % [kW]
% S32
S32.sp = "H2";
S32.m_dot = 73.22;              % [kg/s]
S32.P = 19.50;                  % [bar]
S32.Tref = 22.7;                % [K]
S32.rho = 70.52;                % [kg/m^3]
S32.V_dot = S32.m_dot/S32.rho;  % [m^3/s]

[S32.T,K25.W] = pump(S31.sp,S31.P,S31.T,S32.P,S31.m_dot,K25.etais);

K25.W_relErr = relativeError(K25.Wref,K25.W);   % Percentage
S32.T_relErr = relativeError(S32.Tref,S32.T);   % Percentage

%% After H2 pump K26: S33
% Pump K26
K26.type = "pump";
K26.etais = 0.730;
K26.Wref = 59.79e3;             % [kW]
% S33
S33.sp = "H2";
S33.m_dot = 73.22;              % [kg/s]
S33.P = 486.49;                 % [bar]
S33.Tref = 57.3;                % [K]
S33.rho = 80.32;                % [kg/m^3]
S33.V_dot = S33.m_dot/S33.rho;  % [m^3/s]

[S33.T,K26.W] = pump(S32.sp,S32.P,S32.Tref,S33.P,S31.m_dot,K26.etais);

K26.W_relErr = relativeError(K26.Wref,K26.W);   % Percentage
S33.T_relErr = relativeError(S33.Tref,S33.T);   % Percentage

%% After Main Fuel Valve K64 ***: S58           ??????????????????????
S58.sp = "H2";
S58.m_dot = 73.22;              % [kg/s]
S58.P = 463.32;                 % [bar]
S58.Tref = 59.1;                % [K]
S58.rho = 78.52;                % [kg/m^3]
S58.V_dot = S58.m_dot/S58.rho;  % [m^3/s]

K64.type = "valve";
K64.Pratio = S58.P/S33.P;
K64.Tratio = S58.Tref/S33.Tref;

%% After Flow Splitter K27: S41, S34
% S34
S34.sp = "H2";
S34.m_dot = 57.76;              % [kg/s]

% S41
S41.sp = "H2";
S41.m_dot = S58.m_dot-S34.m_dot;% [kg/s]

%% After Flow Splitter K35: S87, S88
% S87
S87.sp = "H2";
S87.m_dot = S34.m_dot/2;        % [kg/s]
% S88
S88.sp = "H2";
S88.m_dot = S34.m_dot-S87.m_dot;% [kg/s]

%% After HeatEx K28 || Valve K36: S36, S89
% S36
S36.sp = "H2";
S36.m_dot = S87.m_dot;          % [kg/s]
S36.P = 431.40;                 % [bar]
S36.Tref = 257.8;               % [K]
S36.rho = 30.97;                % [kg/m^3]
S36.V_dot = S36.m_dot/S36.rho;  % [m^3/s]
% K28
K28.W = 93.13e3;                % kW

[S36.T, S36.Pcomp] = heatexanger(S87.sp,S58.P,S58.Tref,S87.m_dot,K28.W,1.074);

% S89
S89.sp = "H2";
S89.m_dot = S88.m_dot;          % [kg/s]
S89.P = 431.40;                 % [bar]
S89.Tref = 61.4;                % [K]
S89.rho = 75.95;                % [kg/m^3]
S89.V_dot = S89.m_dot/S89.rho;  % [m^3/s]



%% After Mixer K37: S90
% S90
S90.sp = "H2";
S90.m_dot = S36.m_dot+S89.m_dot;% [kg/s]
S90.P = 431.40;                 % [bar]
S90.Tref = 163.3;               % [K]
S90.rho = 30.97;                % [kg/m^3]
S90.V_dot = S90.m_dot/S90.rho;  % [m^3/s]

S90.T = mixer([S36.sp; S89.sp], S90.P, S36.P, S89.P, S36.Tref, S89.Tref, S36.m_dot, S89.m_dot);
S90.T_relErr = relativeError(S90.Tref, S90.T);

S36.n = S36.m_dot*1000/HGSsingle(char(S36.sp),'Mm');  % mol/s
S89.n = S89.m_dot*1000/HGSsingle(char(S89.sp),'Mm');  % mol/s
% S90.Tmulti = mixer_multispecies2([S36.sp; S89.sp], [S36.n, S89.n], S90.P, S36.P, S89.P, S36.Tref, S89.Tref, [1,2]);

%% After Turbine K34: S44
% S43
S43.sp = "H2";
S43.m_dot = 15.46;              % [kg/s]
S43.P = 345.50;                 % [bar]
S43.Tref = 252.8;               % [K]
S43.rho = 26.54;                % [kg/m^3]
S43.V_dot = S43.m_dot/S43.rho;  % [m^3/s]
% K34
K34.type = "turbine";
K34.etais = 0.520;
K34.Wref = -2.755e3;            % [kW]
% S33
S44.sp = "H2";
S44.m_dot = 15.46;              % [kg/s]
S44.P = 261.36;                 % [bar]
S44.Tref = 244.8;               % [K]
S44.rho = 21.76;                % [kg/m^3]
S44.V_dot = S44.m_dot/S44.rho;  % [m^3/s]

[S44.T,K34.W] = turbine(S43.sp,S43.P,S43.Tref,S44.P,S43.m_dot,K34.etais);

K34.W_relErr = relativeError(K34.Wref,K34.W);   % Percentage
S44.T_relErr = relativeError(S44.Tref,S44.T);   % Percentage

%% After Combustion Chamber K45
% S38
S38.sp = "H2";
S38.m_dot = 37.82;              % [kg/s]
% S38.P = 345.50;                 % [bar]
% S38.Tref = 252.8;               % [K]
% S38.rho = 26.54;                % [kg/m^3]
% S38.V_dot = S38.m_dot/S38.rho;  % [m^3/s]
% S25
S25.sp = "O2"';
S25.m_dot = 74.71-37.82;          % [kg/s]
% S25.P = 345.50;                 % [bar]
% S25.Tref = 252.8;               % [K]
% S25.rho = 26.54;                % [kg/m^3]
% S25.V_dot = S25.m_dot/S25.rho;  % [m^3/s]

% K45
K45.type = "burner";
K45.sp0 = {S38.sp, S25.sp, "H2O","H2O2","HO2","O","OH"};
a = S38.m_dot*1000/HGSsingle(char(S38.sp),"Mm");
b = S25.m_dot*1000/HGSsingle(char(S25.sp),"Mm");
K45.n0 = [a, b, 0, 0, 0, 0, 0];
K45.Tout = 1105.6;  % [K]
K45.Pout = 391.47;  % [bar]
[S55.sp,S55.n,~] = HGSeq(K45.sp0,K45.n0,K45.Tout,K45.Pout);

%% After Mixer K49: S59
% S59
S59.sp = "";
S59.n = [];
S59.m_dot = 76.61;              % [kg/s]
S59.P = 248.21;                 % [bar]
S59.Tref = 975.0;               % [K]
S59.rho = 11.91;                % [kg/m^3]
S59.V_dot = S59.m_dot/S59.rho;  % [m^3/s]
% S56
S56.sp = S55.sp;
S56.n = S55.n;
S56.m_dot = 74.71;              % [kg/s]
S56.P = 248.21;                 % [bar]
S56.Tref = 1008.9;              % [K]
S56.rho = 11.78;                % [kg/m^3]
S56.V_dot = S56.m_dot/S56.rho;  % [m^3/s]
% S72
S72.sp = "H2";
S72.m_dot = 1.90;               % [kg/s]
S72.n = S72.m_dot*1000/HGSsingle(char(S72.sp),'Mm');  % mol/s
S72.P = 248.21;                 % [bar]
S72.Tref = 244.8;               % [K]
S72.rho = 21.76;                % [kg/m^3]
S72.V_dot = S72.m_dot/S72.rho;  % [m^3/s]
% K49
K49.sp0 = [S56.sp, S72.sp];
K49.n0 = [S56.n, S72.n];
K49.flag = [ones(1,length(S56.n)), 2*ones(1,length(S72.n))];

[K49.sp, ~, idx] = unique(K49.sp0);
K49.n = accumarray(idx, K49.n0(:))';

S59.sp = K49.sp;
S59.n = K49.n;
% [S59.T] = mixer_multispecies2([S56.sp,S72.sp],[S56.n,S72.n],S59.P,S56.P,S72.P,S56.Tref,S72.Tref, K49.flag);






%% After H2 tank K24: S31
S11.sp = 'O2';
S11.m_dot = 439.34;              % [kg/s]
S11.P = 6.89;                   % [bar]
S11.T = 91.1;                   % [K]
S11.rho = 1137.99;                % [kg/m^3]
S11.V_dot = S11.m_dot/S11.rho;     % [m^3/s]

%% After O2 pump K10: S12

% K10
K10.type = 'pump';
K10.etais = 0.630;
K10.Wref = 1.396e3;             % [kW]

% S12
S12.sp = "O2";
S12.m_dot = 439.34;              % [kg/s]
S12.P = 29.70;                  % [bar]
S12.Tref = 92.3;                % [K]
S12.rho = 1137.38;                % [kg/m^3]
S12.V_dot = S12.m_dot/S12.rho;  % [m^3/s]

[S12.T,K10.W] = pump(S11.sp,S11.P,S11.T,S12.P,S11.m_dot,K10.etais);

K10.W_relErr = relativeError(K10.Wref,K10.W);   % Percentage
S12.T_relErr = relativeError(S12.Tref,S12.T);   % Percentage

%% After O2 mixer K12: S13

% K10
K10.type = 'mixer';

% S162
S162.sp = "O2";
S162.m_dot = 83.06;              % [kg/s]
S162.P = 29.70;                  % [bar]
S162.T = 107.8;                % [K]
S162.rho = 1056.87;                % [kg/m^3]
S162.V_dot = S162.m_dot/S162.rho;  % [m^3/s]

% S13
S13.sp = "O2";
S13.m_dot = 522.40;              % [kg/s]
S13.P = 29.70;                  % [bar]
S13.Tref = 94.8;                % [K]
S13.rho = 1125.00;                % [kg/m^3]
S13.V_dot = S12.m_dot/S12.rho;  % [m^3/s]

[S13.T] = mixer([S12.sp,S162.sp],S13.P,S12.P,S162.P,S12.T,S162.T,S12.m_dot,S162.m_dot);

S13.T_relErr = relativeError(S13.Tref,S13.T);   % Percentage

%% After K13 pump: S14

% K13
K13.type = 'pump';
K13.etais = 0.670;
K13.Wref = 20.51e3;             % [kW]

% S14
S14.sp = "O2";
S14.m_dot = 522.40;              % [kg/s]
S14.P = 330.35;                  % [bar]
S14.Tref = 108.9;                % [K]
S14.rho = 1127.96;                % [kg/m^3]
S14.V_dot = S12.m_dot/S12.rho;  % [m^3/s]

[S14.T,K13.W] = pump(S13.sp, S13.P, S13.T, S14.P, S13.m_dot, K13.etais);

K13.W_relErr = relativeError(K13.Wref,K13.W);   % Percentage
S14.T_relErr = relativeError(S14.Tref,S14.T);   % Percentage

%% After K14 splitter: S15 and S17
% Same Pressure and same temperature are considered in the input/outputs

% S15
S15.sp = "O2";
S15.m_dot_ref = 83.06;              % [kg/s]
S15.P = 330.35;                  % [bar]
S15.T = 108.9;                % [K]

% S17
S17.sp = "O2";
S17.m_dot_ref = 439.34;              % [kg/s]
S15.P = 330.35;                  % [bar]
S15.T = 108.9;                % [K]

[S15.m_dot, S17.m_dot] = splitter(S14.m_dot, S15.m_dot_ref);

%% After K15 turbine: S160

% K15
K15.type = 'turbine';
K15.etais = 0.620;
K15.Wref = -1.396e3;             % [kW]

% S160
S160.sp = "O2";
S160.m_dot = 83.06;              % [kg/s]
S160.P = 29.70;                       % [bar]
S160.Tref = 107.8;                     % [K]
S160.rho = 1056.78;                    % [kg/m^3]
S160.V_dot = S160.m_dot / S160.rho;  % [m^3/s]

[S160.T, K15.W] = turbine(S160.sp, S15.P, S15.T, S160.P, S160.m_dot, K15.etais);

K15.W_relErr = relativeError(K15.Wref,K15.W);   % Percentage
S160.T_relErr = relativeError(S160.Tref,S160.T);   % Percentage

%% After K11 Init. Value: S162

% S162
S162.sp = "O2";
S162.m_dot = 83.06;              % [kg/s]
S162.P = 29.70;                       % [bar]
S162.Tref = 107.8;                     % [K]
S162.rho = 1056.78;                    % [kg/m^3]
S162.V_dot = S160.m_dot / S160.rho;  % [m^3/s]

%% After K66 O2 Flow splitter: S29 and S74

% S29
S29.sp = "O2";
S29.m_dot_ref = 438.59;              % [kg/s]
S29.P = 330.35;                  % [bar]
S29.T = 108.9;                % [K]

% S74
S74.sp = "O2";
S74.P = 330.35;               % [bar]
S74.T = 108.9;                % [K]

[S29.m_dot_ref, S74.m_dot] = splitter(S17.m_dot_ref, S29.m_dot_ref);

%% After K16 O2 Flow splitter: S18 and S20

% S18
S18.sp = "O2";
S18.m_dot_ref = 388.13;              % [kg/s]
S18.P = 330.35;                  % [bar]
S18.T = 108.9;                % [K]

% S20
S20.sp = "O2";
S20.m_dot_ref = 50.46;        % [kg/s]
S20.P = 330.35;               % [bar]
S20.T = 108.9;                % [K]

[S20.m_dot_ref, S18.m_dot] = splitter(S29.m_dot_ref, S20.m_dot_ref);

%% After K18 O2 pump: S21

% K18
K18.type = 'pump';
K18.etais = 0.800;
K18.Wref = 1.263e3;             % [kW]

% S21
S21.sp = "O2";
S21.m_dot = 50.16;              % [kg/s]
S21.P = 558.71;                       % [bar]
S21.Tref = 116.8;                     % [K]
S21.rho = 1141.64;                    % [kg/m^3]
S21.V_dot = S160.m_dot / S160.rho;  % [m^3/s]

[S21.T, K18.W] = pump(S21.sp, S20.P, S20.T, S21.P, S20.m_dot_ref, K18.etais);

K18.W_relErr = relativeError(K18.Wref,K18.W);   % Percentage
S21.T_relErr = relativeError(S21.Tref,S21.T);   % Percentage

%% After K67 O2 HX: S80

%K67
K67.type = 'HeatExanger';
K67.W = +0.4051e3;             % [kW]
K67.deltaP = 1.157;             % [bar]

%S80
S80.sp = "O2";
S80.m_dot_ref = 0.75;              % [kg/s]
S80.Pref = 285.53;                       % [bar]
S80.Tref = 507.8;                     % [K]
S80.rho = 199.71;                    % [kg/m^3]
S80.V_dot = S160.m_dot / S160.rho;  % [m^3/s]


[S80.T, S80.P] = heatexanger(S74.sp, S74.P, S74.T, S74.m_dot, K67.W, K67.deltaP);
S80.T_relErr = relativeError(S80.Tref,S80.T);   % Percentage
S80.P_relErr = relativeError(S80.Pref,S80.P);   % Percentage

%% After K70 O2 Isentalpic valve: S69

%K70
K70.type = 'IsentalpicValve';
K70.deltaP=1.991; %% Obtained from P69 and P80

% S69
S80.sp = "O2";
S69.m_dot_ref = 0.75;              % [kg/s]
S69.Pref = 2.49;                 % [bar]
S69.Tref = 494.0;                  % [K]
S69.rho_ref = 1.94;                  % [kg/m^3]
S69.V_dot = S160.m_dot / S160.rho; % [m^3/s]

[S69.T, S69.P, S69.rho] = IsentalpicValve(S80.sp, S80.Pref, S80.Tref, K70.deltaP);

S69.T_relErr = relativeError(S69.Tref,S69.T);   % Percentage
S69.P_relErr = relativeError(S69.Pref,S69.P);   % Percentage
S69.rho_relErr = relativeError(S69.rho_ref,S69.rho);   % Percentage

%% After K19 O2 splitter: S22 and S24

% S22
S22.sp = "O2";
S22.m_dot_ref = 13.56;              % [kg/s]
S22.P = 558.71;                  % [bar]
S22.T = 116.8;                % [K]

% S24
S24.sp = "O2";
S24.m_dot_ref = 36.89;        % [kg/s]
S24.P = 558.71;                  % [bar]
S24.T = 116.8;                % [K]

[S22.m_dot_ref, S24.m_dot] = splitter(S21.m_dot, S22.m_dot_ref);
S22.m_dot_relErr = relativeError(S24.m_dot_ref, S24.m_dot);   % Percentage

%% After K61 Isentalpic Valve: S26

%K61
K61.type = 'IsentalpicValve';
K61.deltaP=1.182;

% S26
S26.sp = "O2";
S26.m_dot = 13.56;              % [kg/s]

[S26.T, S26.P, S26.rho] = IsentalpicValve(S26.sp, S22.P, S22.T, K61.deltaP);

%% After K61 Isentalpic Valve: S26

%K20
K20.type = 'IsentalpicValve';
K20.deltaP=1.221;

% S23
S23.sp = "O2";
S23.m_dot = 13.56;              % [kg/s]

[S23.T, S23.P, S23.rho] = IsentalpicValve(S26.sp, S26.P, S26.T, K20.deltaP);

%% After K38 isentalpic valve: S40

%K38
K38.type = 'IsentalpicValve';
K38.deltaP=1.114;

% S39 %% en realidad lo uso de apoyo pero se tiene q hacer en otro sitio
S39.sp = "H2";%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%Revisar porque esta mal creo
S39.m_dot_ref = 19.94;              % [kg/s]
S39.P = 431.40;                          % [bar]
S39.T = 163.3;                          % [K]


[S40.T, S40.P, S40.rho] = IsentalpicValve(S39.sp, S39.P, S39.T, K38.deltaP);

%% After combustion chamber K40: S50

% S40
S40.sp = "H2";
S40.m_dot = 19.34;              % [kg/s]
% S23
S23.sp = "O2"';
S23.m_dot = 13.56;              % [kg/s]
% S50
S50.sp = "";
S50.m_dot = S40.m_dot+S23.m_dot;% [kg/s]
S50.P = 387.25;                 % [bar]
S50.T = 833.33;                 % [K]
S50.rho = 18.93;                % [Kg/m^3]

% K45
K45.type = "burner";
K45.sp0 = {S40.sp, S23.sp, "H2O","H2O2","HO2","O","OH"};
c = S40.m_dot*1000/HGSsingle(char(S40.sp),"Mm");
d = S23.m_dot*1000/HGSsingle(char(S23.sp),"Mm");
K45.n0 = [c, d, 0, 0, 0, 0, 0];
K45.Tout = S50.T;               % [K]
K45.Pout = S50.P;               % [bar]
[S50.sp,S50.n,~] = HGSeq(K45.sp0,K45.n0,K45.Tout,K45.Pout);


%% After K41 turbine: S51

% K41
K41.type = 'turbine';
K41.etais = 0.780;
K41.Wref = -21.77e3;

% S51
S51.sp = "H2";
S51.m_dot = 33.5;              % [kg/s]
S51.P = 251.43;                  % [bar]
S51.Tref = 760.9;                % [K]
S51.rho=13.46;                  % [Kg/m^3]

% [S51.T, K41.W] = turbine(char(S50.sp), S50.P, S50.T, S51.P, S50.m_dot, K41.etais);
% K41.W_relErr = relativeError(K41.Wref,K41.W);   % Percentage %%%% ME DA MAL
% S51.T_relErr = relativeError(S51.Tref,S51.T);   % Percentage

%K28
K28.DeltaP=1.074;
K28.W=93.13e3;

%S87

S87.sp = "H2";
S87.m_dot = 28.88;              % [kg/s]
S87.P = 463.32;                  % [bar]
S87.T = 59.1;                % [K]
S87.rho=78.58;                  % [Kg/m^3]

%S36

S36.sp = "H2";
S36.m_dot = 28.88;              % [kg/s]
S36.Pref = 431.40;                  % [bar]
S36.Tref = 257.8;                % [K]
S36.rho=30.97;                  % [Kg/m^3]

[S36.T, S36.P] = heatexanger(S87.sp, S87.P, S87.T, S87.m_dot,K28.W,K28.DeltaP);


%% After mixer K48 (only composition): S54

% S54
S54.sp = "";
S54.n = [];
S54.m_dot = 33.97;              % [kg/s]
S54.P = 248.21;                 % [bar]
S54.Tref = 748.2;               % [K]
S54.rho = 13.39;                % [kg/m^3]
S54.V_dot = S54.m_dot/S54.rho;  % [m^3/s]
% S53
S53.sp = S50.sp;
S53.n = S50.n;
S53.m_dot = 33.50;              % [kg/s]
S53.P = 248.21;                 % [bar]
S53.Tref = 759.5;               % [K]
S53.rho = 13.31;                % [kg/m^3]
S53.V_dot = S53.m_dot/S53.rho;  % [m^3/s]
% S71
S71.sp = "H2";
S71.m_dot = 0.47;               % [kg/s]
S71.n = S71.m_dot*1000/HGSsingle(char(S71.sp),'Mm');  % mol/s
S71.P = 248.21;                 % [bar]
S71.Tref = 244.8;               % [K]
S71.rho = 21.76;                % [kg/m^3]
S71.V_dot = S71.m_dot/S71.rho;  % [m^3/s]
% K48
K48.sp0 = [S53.sp, S71.sp];
K48.n0 = [S53.n, S71.n];
K48.flag = [ones(1,length(S53.n)), 2*ones(1,length(S71.n))];

[K48.sp, ~, idx] = unique(K48.sp0);
K48.n = accumarray(idx, K48.n0(:))';

S54.sp = K48.sp;
S54.n = K48.n;

%% After Mixer K50: S60!!

S57.sp = S59.sp;
S57.n = S59.n;

S77.m_dot = 12.75;      % [kg/s]
S79.sp = S71.sp;
S79.n = S77.m_dot*1000/HGSsingle(char(S79.sp),'Mm');  % mol/s;

S19.sp = S18.sp;
S19.n = S18.m_dot*1000/HGSsingle(char(S18.sp),'Mm');  % mol/s;

S52.sp = S54.sp;
S52.n = S54.n;

K50.sp0 = [S57.sp, S79.sp, S19.sp, S52.sp];
K50.n0 = [S57.n, S79.n, S19.n, S52.n];
[K50.sp, ~, idx] = unique(K50.sp0);
K50.n = accumarray(idx, K50.n0(:))';

S60.sp = K50.sp;
S60.n = K50.n;
S62.Tref = 3613;
S62.P = 225.10;
S60.sp = cellstr(S60.sp);
[S62.sp,S62.n,~] = HGSeq(char(S60.sp),S60.n,S62.Tref,S62.P);

S62.sp = string(S62.sp);
% S62.n = S62.n;
S63.Tref = 3683.6;
S63.P = 219.70;
S62.sp = cellstr(S62.sp);
[S63.sp,S63.n,~] = HGSeq(char(S62.sp),S62.n,S63.Tref,S63.P);

%% Nozzle

S86.P= 0.19243;     % [bar]

% Calculate the mass of the gas after combustion
S63.Mm = HGSprop(S63.sp, S63.n, S63.Tref, S63.P, 'Mm'); % g/mol
total_mol = sum(S63.n);
total_mass = total_mol * S63.Mm /1000; % kg/s

% Considering adiabatic process
S63.H = HGSprop(S63.sp, S63.n, S63.Tref, S63.P, 'H'); % kJ 
S63.h = S63.H / (76.61+12.75+388.13+33.97); % kJ/kg

K52.Q = 47.77e3;    % [kW]
K53.Q = 93.13e3;    % [kW]
K52.q = 47.77e3/(76.61+12.75+388.13+33.97);    % [kW]
K53.q = 93.13e3/(76.61+12.75+388.13+33.97);    % [kW]

[~, S68.v, S68.a, S68.T, S68.n, S68.Mm] = throat_nozzle(S86.P, S63.h, K52.q+K53.q, S63.sp, S63.n, S63.Tref, S63.P);
S68.M = S68.v/S68.a;

S68.Tref = 1139.3;      % [K]
S68.rho = 0.02874;      % [kg/m^3]
S68.vref = 4351.2;      % [m/s]
S68.Mref = 4.734;

S68.v_relErr = relativeError(S68.vref, S68.v);
S68.M_relErr = relativeError(S68.Mref, S68.M);
S68.T_relErr = relativeError(S68.Tref, S68.T);
