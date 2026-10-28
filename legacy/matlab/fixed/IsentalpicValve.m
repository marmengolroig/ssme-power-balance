function [T_out, P_out, rho_out] = IsentalpicValve(sp, P_in, T_in, PR)
%ISENTALPICVALVE Isenthalpic throttling of a pure real fluid (INIST/NFP).
%   [T_out, P_out, rho_out] = IsentalpicValve(sp, P_in, T_in, PR)
%   sp   : NFP fluid name ('pH2', 'H2', 'O2')
%   P_in : inlet pressure [bar],  T_in: inlet temperature [K]
%   PR   : pressure ratio P_in/P_out (> 1)
%
%   FIX(2): the original used P_out = P_in*(2-deltaP), a first-order approximation of
%   P_in/PR that is wrong for large losses (e.g. 356 instead of 387 bar after K61+K20).

    if PR <= 0
        error('IsentalpicValve: the pressure ratio must be positive');
    end
    P_out = P_in / PR;
    h_in  = NFP(sp, 'h_pt', P_in, T_in);
    T_out = NFP(sp, 't_hp', h_in, P_out);
    check_single_phase(T_out, sp, 'IsentalpicValve');
    rho_out = NFP(sp, 'r_pt', P_out, T_out);
end
