function [T_out, P_out] = heatexanger(sp, P_in, T_in, m_dot, Q_dot, PR)
%HEATEXANGER Heat addition to a pure real fluid with a pressure loss.
%   [T_out, P_out] = heatexanger(sp, P_in, T_in, m_dot, Q_dot, PR)
%   Q_dot : heat added to the fluid [kW] (positive = heating, e.g. regenerative cooling)
%   PR    : pressure ratio P_in/P_out (> 1)
%
%   FIX(2): P_out = P_in/PR instead of P_in*(2-PR).

    h_in  = NFP(sp, 'h_pt', P_in, T_in);           % kJ/kg
    h_out = h_in + Q_dot / m_dot;                   % first law
    P_out = P_in / PR;
    T_out = NFP(sp, 't_hp', h_out, P_out);
    check_single_phase(T_out, sp, 'heatexanger');
end
