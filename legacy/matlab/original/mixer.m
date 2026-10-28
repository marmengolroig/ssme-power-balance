function [T_out] = mixer(sp,P_out,P_in1,P_in2,T_in1,T_in2,m_dot1,m_dot2)
% MIXER Summary of this function goes here
%   Detailed explanation goes here
% Check for mixers
if P_in1 ~= P_in2
    error('Flows enter at different pressures in the mixer.')
end
% Enthalpies in (normalized for NFP)
h_specific_in1 = NFP(sp(1), 'h_pt', P_in1, T_in1); 
H_dot_in1 = m_dot1 * h_specific_in1;
    
h_specific_in2 = NFP(sp(2), 'h_pt', P_in2, T_in2);
H_dot_in2 = m_dot2 * h_specific_in2;

H_dot_total_in = H_dot_in1 + H_dot_in2;
balance_error = @(T) (m_dot1 * NFP(sp(1), 'h_pt', P_out, T) + m_dot2 * NFP(sp(2), 'h_pt', P_out, T)) - H_dot_total_in;
T_guess = (m_dot1 * T_in1 + m_dot2 * T_in2) / (m_dot1 + m_dot2);

options = optimset('Display','off');
T_out = fzero(balance_error, T_guess, options);

end
