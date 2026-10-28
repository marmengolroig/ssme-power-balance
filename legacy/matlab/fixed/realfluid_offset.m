function off = realfluid_offset(fluid)
%REALFLUID_OFFSET Enthalpy offset [kJ/kg] from the NFP (NIST) scale to the HGS (NASA) scale.
%   h_HGS = h_NFP + realfluid_offset(fluid),  fluid = 'H2' | 'pH2' | 'O2'
%
%   Replaces getDeltah.m - FIX(4). The original matched HGS and NFP at 675 K *and at the
%   stream pressure* (e.g. 248 bar), where H2 is not an ideal gas (~200 kJ/kg error), and then
%   applied that H2 offset to H2O, OH, O, ... Here the offset is taken in the ideal-gas limit
%   (300 K, 0.01 bar), separately for each fluid. Para-H2 is tied to normal H2 through the
%   ortho->para conversion enthalpy of the saturated liquid at the normal boiling point
%   (527 kJ/kg), because the HGS 'H2' polynomial describes normal hydrogen.

    persistent cache
    if isempty(cache)
        cache = struct();
    end
    key = matlab.lang.makeValidName(fluid);
    if isfield(cache, key)
        off = cache.(key);
        return
    end
    Ta = 300;     % K
    Pa = 0.01;    % bar
    switch fluid
        case {'H2', 'O2'}
            off = HGSsingle(fluid, 'h', Ta, Pa) / HGSsingle(fluid, 'Mm') * 1000 ...
                  - NFP(fluid, 'h_pt', Pa, Ta);
        case 'pH2'
            off = realfluid_offset('H2') + NFP('H2', 'hl_p', 1.01325) ...
                  - NFP('pH2', 'hl_p', 1.01325) - 527.0;
        otherwise
            error('realfluid_offset: unknown fluid %s', fluid);
    end
    cache.(key) = off;
end
