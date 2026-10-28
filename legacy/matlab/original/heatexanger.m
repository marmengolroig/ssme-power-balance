function [T_out, P_out] = heatexanger(sp, P_in, T_in, m_dot, Power_dot, deltaP)

    % 1. Calcular entalpía entrada [kJ/kg]
    h_in = NFP(sp, 'h_pt', P_in, T_in);
    
    % 2. Primer Principio (Balance de Energía)
    % Si el fluido se calienta (refrigera tobera), Power_dot es POSITIVO.
    h_out = h_in + (Power_dot / m_dot);
    
    % 3. Calcular presión salida (Pérdida de carga)
    P_out = P_in*(2-deltaP);
    
    % 4. Encontrar temperatura de salida dado el nuevo estado (P, h)
    T_out = NFP(sp, 't_hp', h_out, P_out);
    
end