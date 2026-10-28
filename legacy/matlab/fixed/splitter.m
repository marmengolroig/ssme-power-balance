function [m_dot1, m_dot2] = splitter(m_dot0, m_dot1)
%SPLITTER Mass balance of a two-way flow splitter: m_dot2 = m_dot0 - m_dot1.
    if m_dot1 < 0 || m_dot1 > m_dot0
        error('splitter: branch flow %.3f outside [0, %.3f] kg/s', m_dot1, m_dot0);
    end
    m_dot2 = m_dot0 - m_dot1;
end
