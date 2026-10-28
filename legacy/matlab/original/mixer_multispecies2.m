function T_out = mixer_multispecies2(sp, n0, P_out, P_in1, P_in2, T_in1, T_in2, fl)
% MIXER_MULTISPECIES
% Mixes two multispecies flows at equal pressure to thermal equilibrium
% using a consistent enthalpy balance (NFP + HGS with reference correction)

    % --- Checks ---
    if P_in1 ~= P_in2
        error('Flows enter at different pressures in the mixer.')
    end

    sp = string(sp);   % enforce type consistency
    Ns = length(sp);

    % --- Preallocate ---
    h_in   = zeros(1, Ns);   % kJ/kg
    m_dot  = zeros(1, Ns);   % kg/s
    H_dot  = zeros(1, Ns);   % kW

    % ============================================================
    % 1. INLET ENTHALPY AND MASS FLOW
    % ============================================================

    for i = 1:Ns

        % --- Mass flow from molar flow ---
        Mm = HGSsingle(char(sp(i)), 'Mm');     % kg/kmol
        m_dot(i) = n0(i) * Mm / 1000;    % kg/s

        % --- Select inlet ---
        if fl(i) == 1
            T = T_in1;
            P = P_in1;
        else
            T = T_in2;
            P = P_in2;
        end

        % --- Enthalpy evaluation ---
        if T >= 800
            % High-temperature / radicals → HGS
            h_mol = HGSsingle(char(sp(i)), 'h', T, P) * 1000;  % kJ/kmol
            h_in(i) = h_mol / Mm - getDeltah(P);         % kJ/kg
        else
            % Low-temperature stable species → NFP
            h_in(i) = NFP(sp(i), 'h_pt', P, T);          % kJ/kg
        end

        % --- Enthalpy rate ---
        H_dot(i) = m_dot(i) * h_in(i);

    end

    H_dot_total_in = sum(H_dot);
    m_dot_total    = sum(m_dot);

    if m_dot_total <= 0
        error('Total mass flow is zero or negative.')
    end

    % ============================================================
    % 2. ENTHALPY-BASED INITIAL TEMPERATURE GUESS
    % ============================================================

    h_target = H_dot_total_in / m_dot_total;   % kJ/kg

    mix_h = @(T) total_enthalpy_out(T, sp, m_dot, P_out) / m_dot_total;

    % Wide but safe temperature bracket
    Tmin = 200;
    Tmax = 5000;

    T_guess = fzero(@(T) mix_h(T) - h_target, [Tmin Tmax]);

    % ============================================================
    % 3. FINAL ENERGY BALANCE SOLVE
    % ============================================================

    balance_error = @(T) total_enthalpy_out(T, sp, m_dot, P_out) ...
                         - H_dot_total_in;

    options = optimset('Display','off');
    T_out = fzero(balance_error, T_guess, options);

end


function H_total = total_enthalpy_out(T, sp, m_dot, P)

    H_total = 0;

    for k = 1:length(sp)

        try
            % Try NFP first (stable species)
            h_k = NFP(sp(k), 'h_pt', P, T);

        catch
            % Fallback to HGS (radicals, atoms, high T)
            Mm    = HGSsingle(char(sp(k)), 'Mm');
            h_mol = HGSsingle(char(sp(k)), 'h', T, P) * 1000;  % kJ/kmol
            h_k   = h_mol / Mm - getDeltah(P);           % kJ/kg
        end

        H_total = H_total + m_dot(k) * h_k;

    end
end
