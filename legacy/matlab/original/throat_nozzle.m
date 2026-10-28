function [err, v, a, T_static, n, Mm] = throat_nozzle(P_static, h_0, q_loss, sp, n_in, T_in, P_in)
    % Isentropic T
    [T_static, ~, n, ~, flag] = HGSisentropic(sp, n_in, T_in, P_in, 'Shifting', 'P', P_static);
    if flag ~= 1
        err = NaN; v=0; a=0; return;
    end

    H = HGSprop(sp, n, T_static, P_static, 'H'); % kJ
    Mm = HGSprop(sp, n, T_static, P_static, 'Mm'); % g/mol
    m_tot= sum(n)*Mm/1000; % kg
    h = H / m_tot; % kJ/kg
 
    % v = sqrt(2 * (h0 - h) * 1000)
    delta_h = (h_0 - q_loss - h) * 1000; 
        
    if delta_h < 0
        v = 0; 
    else
        v = sqrt(2 * delta_h);
    end
        
    % Sound velocity
    a = HGSprop(sp, n, T_static, P_static, 'a');

    % If M=1, err=0
    err = v - a;
end