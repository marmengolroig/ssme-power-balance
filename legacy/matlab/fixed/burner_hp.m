function [T_out, n_out] = burner_hp(SP, n_in, H_in, P_out, Q_loss)
%BURNER_HP Adiabatic (or with heat loss) chemical-equilibrium combustor using HGS.
%   [T_out, n_out] = burner_hp(SP, n_in, H_in, P_out, Q_loss)
%   SP    : cellstr of HGS species (keep 'H' in the list: FIX(8))
%   n_in  : total inlet molar flows [mol/s] in SP order
%   H_in  : total inlet enthalpy flow on the HGS scale [kW]
%   Q_loss: heat removed from the gas [kW] (0 for adiabatic)
%
%   FIX(6): the original imposed the *reference* outlet temperature in HGSeq, so the burner
%   temperature was an input rather than a prediction.

    if nargin < 5
        Q_loss = 0;
    end
    [T_out, ~, n_out] = HGStp(SP, n_in, 'H', H_in - Q_loss, P_out);
end
