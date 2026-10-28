function [T_out] = mixer_multispecies(sp, n0, P_out, P_in1, P_in2, T_in1, T_in2, fl)
% MIXER_MULTISPECIES Mixes two multi-species flows to thermal equilibrium.

    if P_in1 ~= P_in2
        error('Flows enter at different pressures in the mixer.')
    end

    % Pre-allocate arrays for speed
    h_specific = zeros(1, length(sp));
    m_dot = zeros(1, length(sp));
    H_dot_in = zeros(1, length(sp));

    % --- 1. Calculate Inlet Enthalpies and Mass Flows ---
    for i = 1:length(sp)
        % Calculate specific enthalpy based on flow source (fl)
        if fl(i) == 1
            if T_in1 >= 800
                % High Temp Logic
                h_specificHGS_mol = HGSsingle(char(sp(i)), 'h', T_in1, P_in1) * 1000; % kJ/kmol
                h_specificHGS = h_specificHGS_mol / HGSsingle(char(sp(i)), 'Mm');     % kJ/kg
                h_specific(i) = h_specificHGS - getDeltah(P_in1);
            else
                % Normal Temp Logic
                h_specific(i) = NFP(string(sp(i)), 'h_pt', P_in1, T_in1);   % kJ/kg
            end
        elseif fl(i) == 2
            h_specific(i) = NFP(sp(i), 'h_pt', P_in2, T_in2);   % kJ/kg
        end

        % Calculate Mass Flow (kg/s) assuming n0 is molar flow
        m_dot(i) = n0(i) * HGSsingle(char(sp(i)), 'Mm') / 1000;
        
        % Calculate Enthalpy Rate (kW)
        H_dot_in(i) = m_dot(i) * h_specific(i); 
    end

    H_dot_total_in = sum(H_dot_in);

    % --- 2. Calculate Robust Initial Guess (T_guess) ---
    % Weighted average based on mass flow of each stream
    m_dot_stream1 = sum(m_dot(fl == 1));
    m_dot_stream2 = sum(m_dot(fl == 2));
    m_dot_total   = sum(m_dot);

    if m_dot_total > 0
        % Mass-weighted average (Assume approx constant Cp for guess)
        T_guess = (m_dot_stream1 * T_in1 + m_dot_stream2 * T_in2) / m_dot_total;
    else
        % Fallback if mass flow is zero (prevents NaN)
        T_guess = (T_in1 + T_in2) / 2;
    end
    h_target = H_dot_total_in / sum(m_dot);

    


    % --- 3. Solve for Outlet Temperature ---
    
    % Define the error function: (Total H_out at T) - (Total H_in)
    % Uses the helper function defined below
    balance_error_func = @(T) calculate_total_H_out(T, sp, m_dot, P_out) - H_dot_total_in;

    options = optimset('Display','off');
    
    % Solve using the weighted guess
    T_out = fzero(balance_error_func, T_guess, options);

end

function H_total = calculate_total_H_out(T, sp, m_dot, P_out)

    H_total = 0;

    for k = 1:length(sp)

        try
            % Try NFP first (stable species)
            h_k = NFP(sp(k), 'h_pt', P_out, T);

        catch
            % Fallback to HGS for radicals / atoms
            h_mol = HGSsingle(char(sp(k)), 'h', T, P_out) * 1000; % kJ/kmol
            Mm    = HGSsingle(char(sp(k)), 'Mm');                % kg/kmol
            h_k   = h_mol / Mm - getDeltah(P_out);         % kJ/kg
        end

        H_total = H_total + m_dot(k) * h_k;
    end
end
