%% Run the corrected MATLAB model and export its results for the Python cross-check.
%
%   >> cd legacy/matlab/fixed
%   >> export_results
%
% Writes legacy/matlab/results/matlab_results.json. Commit that file: tests/test_matlab_crosscheck.py
% then compares every value with the Python port (code-to-code verification of the port).

main;   % defines struct R

R.matlab_version = version;
R.generated = datestr(now, 'yyyy-mm-dd HH:MM:SS');
here = fileparts(mfilename('fullpath'));
outdir = fullfile(here, '..', 'results');
if ~exist(outdir, 'dir'), mkdir(outdir); end
fid = fopen(fullfile(outdir, 'matlab_results.json'), 'w');
fprintf(fid, '%s', jsonencode(R));
fclose(fid);
fprintf('\nResults written to %s\n', fullfile(outdir, 'matlab_results.json'));
