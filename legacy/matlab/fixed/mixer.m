function [T_out] = mixer(sp, P_out, P_in1, P_in2, T_in1, T_in2, m_dot1, m_dot2)
%MIXER Adiabatic mixing of two streams of the SAME pure real fluid (INIST/NFP).
%   T_out = mixer(sp, P_out, P_in1, P_in2, T_in1, T_in2, m_dot1, m_dot2)
%   sp: fluid name ('pH2' or 'O2'), or a 2-element cellstr/string array of identical names.
%
%   FIX(12): the original indexed sp(1)/sp(2). With two char inputs, ['O2','O2'] = 'O2O2'
%   and sp(1) = 'O'. Pressures were compared with exact floating-point equality.

    if iscell(sp) || (isstring(sp) && numel(sp) > 1)
        sp = cellstr(sp);
        if ~all(strcmp(sp, sp{1}))
            error('mixer: both streams must be the same fluid');
        end
        sp = sp{1};
    end
    sp = char(sp);
    if abs(P_in1 - P_in2) > 1e-6 * max(P_in1, P_in2)
        warning('mixer: inlet pressures differ (%.3f vs %.3f bar)', P_in1, P_in2);
    end
    H_in  = m_dot1 * NFP(sp, 'h_pt', P_in1, T_in1) + m_dot2 * NFP(sp, 'h_pt', P_in2, T_in2);  % kW
    h_out = H_in / (m_dot1 + m_dot2);
    T_out = NFP(sp, 't_hp', h_out, P_out);
    check_single_phase(T_out, sp, 'mixer');
end
