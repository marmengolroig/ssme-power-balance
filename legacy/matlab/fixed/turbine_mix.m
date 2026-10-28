function [T_out, W, eta_out] = turbine_mix(SP, n, P_in, T_in, P_out, eta, T_out_known)
%TURBINE_MIX Adiabatic turbine for an ideal-gas mixture with frozen composition (HGS).
%   [T_out, W] = turbine_mix(SP, n, P_in, T_in, P_out, eta)
%       outlet temperature and power [kW] for a given isentropic efficiency
%   [T_out, W, eta_out] = turbine_mix(SP, n, P_in, T_in, P_out, [], T_out_known)
%       power and implied efficiency between two known states
%
%   FIX(5): the HPOT K41 was computed as pure H2 with NFP (W ~80 % too large). The preburner
%   gas is ~45 % H2O by mass.

    S1  = HGSprop(SP, n, T_in, P_in, 'S');
    H1  = HGSprop(SP, n, T_in, P_in, 'H');
    T2s = fzero(@(T) HGSprop(SP, n, T, P_out, 'S') - S1, [300, T_in]);
    H2s = HGSprop(SP, n, T2s, P_out, 'H');
    if nargin < 7 || isempty(T_out_known)
        H2    = H1 + eta * (H2s - H1);
        T_out = fzero(@(T) HGSprop(SP, n, T, P_out, 'H') - H2, [300, T_in]);
        eta_out = eta;
    else
        T_out = T_out_known;
        H2    = HGSprop(SP, n, T_out, P_out, 'H');
        eta_out = (H2 - H1) / (H2s - H1);
    end
    W = H2 - H1;   % kW (n in mol/s, H in kJ/s); negative = delivered by the gas
end
