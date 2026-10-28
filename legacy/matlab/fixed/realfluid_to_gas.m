function [n, H] = realfluid_to_gas(SP, fluid, m_dot, P, T)
%REALFLUID_TO_GAS Express a pure real-fluid stream as moles of an HGS species list.
%   [n, H] = realfluid_to_gas(SP, fluid, m_dot, P, T)
%   SP    : cellstr of HGS species (e.g. {'H2','O2','H2O','H','O','OH','HO2','H2O2'})
%   fluid : NFP name 'pH2' | 'H2' | 'O2'
%   n     : molar flows [mol/s], same order as SP
%   H     : enthalpy flow on the HGS scale [kW], including the real-fluid (liquid) enthalpy

    hgsname = fluid;
    if strcmp(fluid, 'pH2')
        hgsname = 'H2';
    end
    n = zeros(1, numel(SP));
    k = find(strcmp(SP, hgsname));
    if isempty(k)
        error('realfluid_to_gas: %s is not in the species list', hgsname);
    end
    n(k) = m_dot * 1000 / HGSsingle(hgsname, 'Mm');                            % mol/s
    H = m_dot * (NFP(fluid, 'h_pt', P, T) + realfluid_offset(fluid));          % kW
end
