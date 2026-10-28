function [relErr] = relativeError(refVal,compVal)
%RELATIVEERROR Summary of this function goes here
%   Gives relative error in %
relErr = (compVal-refVal)*100/refVal;
end

