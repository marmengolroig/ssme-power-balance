function [deltah_HGSNFP] = getDeltah(P)
%GETDELTAH gives the enthalpy increment of HGS with respect to NFP. That
%is: H_NFP + deltaH = H_HGS
%   Detailed explanation goes here

T_HGS_vec = linspace(200, 1500, 1000);
h_HGS_vec = zeros(1, length(T_HGS_vec));
for i=1:1:length(T_HGS_vec) 
    h_HGS_vec(i) = HGSsingle('H2', 'h', T_HGS_vec(i), P)*1000;              % kJ/kmol
    h_HGS_vec_kg(i) = h_HGS_vec(i)/HGSsingle('H2', 'Mm', T_HGS_vec(i), P);  % kJ/kg
end

T_NFP_vec = linspace(60, 800, 1000);
h_NFP_vec = zeros(1, length(T_HGS_vec));
for i=1:1:length(T_HGS_vec)
    h_NFP_vec(i) = NFP('H2', 'h_pt', P, T_NFP_vec(i));                      % kJ/kg
end

% A point in the linear region of both curves is selected
T_sample = 675; % K
h_sample_HGS = interp1(T_HGS_vec, h_HGS_vec_kg, T_sample);
h_sample_NFP = interp1(T_NFP_vec, h_NFP_vec, T_sample);
deltah_HGSNFP = h_sample_HGS - h_sample_NFP; % That is, h_HGS = h_NFP + deltah_HGSNFP. kJ/kg

end

