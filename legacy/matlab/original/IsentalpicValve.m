function [T_out, P_out, rho_out] = IsentalpicValve(sp, P_in, T_in, deltaP)

    P_out = P_in*(2-deltaP);
    h_in = NFP(sp, 'h_pt', P_in, T_in);
    h_out = h_in;
    T_out = NFP(sp, 't_hp', h_out, P_out);
    rho_out = NFP(sp, 'r_pt', P_out, T_out);

end