function [T_out, W] = pump(sp, P_in, T_in, P_out, m_dot, eta)
%PUMP Adiabatic pump with isentropic efficiency (pure real fluid, INIST/NFP).
%   [T_out, W] = pump(sp, P_in, T_in, P_out, m_dot, eta)
%   sp: NFP fluid name ('pH2', 'O2'); P [bar]; T [K]; m_dot [kg/s]; eta [-]
%   W : power absorbed by the fluid [kW] (positive)
%
%   h2s = h(P_out, s_in);  h2 = h_in + (h2s - h_in)/eta;  W = m_dot*(h2 - h_in)

    h_in  = NFP(sp, 'h_pt', P_in, T_in);
    s_in  = NFP(sp, 's_pt', P_in, T_in);
    T_outs = NFP(sp, 't_ps', P_out, s_in);
    check_single_phase(T_outs, sp, 'pump');
    h_outs = NFP(sp, 'h_pt', P_out, T_outs);
    h_out  = h_in + (h_outs - h_in) / eta;
    W      = m_dot * (h_out - h_in);
    T_out  = NFP(sp, 't_hp', h_out, P_out);
    check_single_phase(T_out, sp, 'pump');
end
