function T_out = mixer_gas(SP, n, H_in, P_out, T_bracket)
%MIXER_GAS Adiabatic mixing into an ideal-gas mixture with frozen composition (HGS).
%   T_out = mixer_gas(SP, n, H_in, P_out, T_bracket)
%   n    : total molar flows of the mixed stream [mol/s] (sum of the inlets, SP order)
%   H_in : total inlet enthalpy flow on the HGS scale [kW] (real-fluid inlets included with
%          realfluid_to_gas, so the liquid/real-gas enthalpy is accounted for)
%
%   Replaces mixer_multispecies.m / mixer_multispecies2.m - FIX(4): those mixed NFP and HGS
%   reference states species by species (try NFP, fall back to HGS), which made H(T)
%   discontinuous and inconsistent, and recomputed getDeltah (2000 property calls) inside
%   every fzero iteration.

    if nargin < 5
        T_bracket = [300, 3000];
    end
    f = @(T) HGSprop(SP, n, T, P_out, 'H') - H_in;
    T_out = fzero(f, T_bracket);
end
