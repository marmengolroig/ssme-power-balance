%% ==========================================
%% LÍNEA DE OXIDANTE (LOX)
%% ==========================================

clear;
close all;
clc

addpath('C:\Users\Toni\Desktop\MASTER\Q3\COHETES AVANZADA\HGS');
addpath('C:\Users\Toni\Desktop\MASTER\Q3\COHETES AVANZADA\INIST');

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

%% ME SALTO EL BURNER K 40 POR QUE NO TENGO NI IDEA DE COMO HACERLO

% S50
S50.sp = "H2";
S50.m_dot = 33.5;              % [kg/s]
S50.P = 387.25;                  % [bar]
S50.T = 833.33;                % [K]
S50.rho=18.93;                  % [Kg/m^3]

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

[S51.T, K41.W] = turbine(S50.sp, S50.P, S50.T, S51.P, S50.m_dot, K41.etais);
K41.W_relErr = relativeError(K41.Wref,K41.W);   % Percentage %%%% ME DA MAL
S51.T_relErr = relativeError(S51.Tref,S51.T);   % Percentage

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


