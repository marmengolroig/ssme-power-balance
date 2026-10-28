function check_single_phase(T, sp, caller)
%CHECK_SINGLE_PHASE Guard against NFP's two-phase return value.
%   NFP(...,'t_hp',...) and NFP(...,'t_ps',...) return [quality, Tsat] (two numbers) when the
%   state falls inside the liquid-vapour dome. The original code would silently use that
%   vector as a temperature (FIX(11)).
    if numel(T) ~= 1
        error('%s: %s state is two-phase (quality = %.4f, Tsat = %.3f K)', caller, sp, T(1), T(2));
    end
end
