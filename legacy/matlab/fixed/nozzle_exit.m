function [T_e, v, a, M, n_e, Mm] = nozzle_exit(SP, n0, T0, P0, P_exit, Q_loss, Fro_Shift)
%NOZZLE_EXIT Isentropic expansion from the chamber to the nozzle exit (HGS).
%   [T_e, v, a, M, n_e, Mm] = nozzle_exit(SP, n0, T0, P0, P_exit, Q_loss, Fro_Shift)
%   SP, n0  : chamber species and molar flows [mol/s] (equilibrium composition)
%   T0, P0  : chamber temperature [K] and pressure [bar]
%   Q_loss  : heat removed by the nozzle coolant [kW] (K53 only: FIX(9))
%   Fro_Shift: 'Shifting' (default) or 'Frozen'
%
%   Replaces throat_nozzle.m (which computed the exit, not the throat, subtracted K52+K53,
%   divided by a hard-coded mass flow and left outputs unassigned when HGS failed).

    if nargin < 7
        Fro_Shift = 'Shifting';
    end
    m   = sum(n0) * HGSprop(SP, n0, T0, P0, 'Mm') / 1000;          % kg/s
    H0  = HGSprop(SP, n0, T0, P0, 'H');                             % kW
    [T_e, ~, n_e, ~, flag] = HGSisentropic(SP, n0, T0, P0, Fro_Shift, 'P', P_exit);
    if flag ~= 1
        error('nozzle_exit: HGSisentropic failed (flag = %d)', flag);
    end
    H_e = HGSprop(SP, n_e, T_e, P_exit, 'H');
    dh  = (H0 - H_e - Q_loss) / m;                                   % kJ/kg
    v   = sqrt(2 * 1000 * max(dh, 0));
    a   = HGSprop(SP, n_e, T_e, P_exit, 'a');                        % frozen sound speed
    M   = v / a;
    Mm  = HGSprop(SP, n_e, T_e, P_exit, 'Mm');
end
