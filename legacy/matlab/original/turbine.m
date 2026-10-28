function [T_out, W] = turbine(sp, P_in, T_in, P_out, m_dot, eta)
%UNTITLED Summary of this function goes here

%% INTRODUCTION WITH EXPLANATION IS NEEDED!!!!!!


h_in = NFP(char(sp), 'h_pt', P_in, T_in);
% In an isentropic process
s_in = NFP(char(sp), 's_pt', P_in, T_in);
s_outs = s_in;
T_outs = NFP(char(sp), 't_ps', P_out, s_outs);
% Applying isentropic efficiency
h_outs = NFP(char(sp), 'h_pt', P_out, T_outs);
h_out = (h_outs-h_in)*eta + h_in;

W = m_dot*(h_out-h_in);
T_out = NFP(char(sp), 't_hp', h_out, P_out);
end

