function [T_out, W] = turbine(sp, P_in, T_in, P_out, m_dot, eta)
%TURBINE Adiabatic turbine for a PURE real fluid (INIST/NFP), e.g. LPOT (LOX) or LPFT (H2).
%   [T_out, W] = turbine(sp, P_in, T_in, P_out, m_dot, eta)
%   W: power delivered by the fluid [kW] (negative)
%
%   For preburner gas (H2/H2O mixture) use turbine_mix.m instead: FIX(5).

    if ~(ischar(sp) || (isstring(sp) && isscalar(sp)))
        error('turbine: sp must be a single fluid name; use turbine_mix for gas mixtures');
    end
    sp = char(sp);
    h_in  = NFP(sp, 'h_pt', P_in, T_in);
    s_in  = NFP(sp, 's_pt', P_in, T_in);
    T_outs = NFP(sp, 't_ps', P_out, s_in);
    check_single_phase(T_outs, sp, 'turbine');
    h_outs = NFP(sp, 'h_pt', P_out, T_outs);
    h_out  = h_in + eta * (h_outs - h_in);
    W      = m_dot * (h_out - h_in);
    T_out  = NFP(sp, 't_hp', h_out, P_out);
    check_single_phase(T_out, sp, 'turbine');
end
