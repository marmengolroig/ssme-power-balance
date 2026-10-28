function [relErr] = relativeError(refVal, compVal)
%RELATIVEERROR Relative error in percent: 100*(computed - reference)/|reference|.
    relErr = (compVal - refVal) * 100 / abs(refVal);
end
