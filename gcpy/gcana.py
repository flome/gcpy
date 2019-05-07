"""
    GCpy module for glow curve analysis.
    Author: Florian Mentzel (florian.mentzel@tu-dortmund.de)
    Creation: 2019/05/05
"""

### import depdencencies
# unit tests
import unittest

# json handling
import json

# os operations like file lists
import os

# pandas for result presentation
import pandas as pd

# needed for curve smoothing
from scipy import signal

# numerical operations
import numpy as np

from . import utils
from scipy.optimize import curve_fit


def calcRoI(x, y, iterations = 2):
    """
    Compute the RoI for given x and y
    
    Parameters
    ---------
    x
        string or list or array. x-axis for the data, generally the time axis for glow curve analysis. If a string is passed, a callable is returned

    y
        string or list or array. y-axis for the data, generally the photon counts for glow curve analysis. If a string is passed, a callable is returned

    iterations
        The RoI is determined iteratively. Good results have been found with 2 iterations (default)

    Returns
    ---------
    dict
        dictionary containing the results of the RoI calculation

    """
    
    # special case: only column names are passed. In that case, a new callable is returned using those columns if called with a data set
    if isinstance(x, str):
        return lambda data: calcRoI(data[x], data[y]) if isinstance(data, pd.DataFrame)  else data.update(calcRoI(data[x], data[y]))

    if not isinstance(x, np.ndarray):
        x = np.array(x)
    if not isinstance(y, np.ndarray):
        y = np.array(y)
        
    # window size for the curve finder and correction for even numbers (can't be handled)
    window = int(len(x)/3)
    if np.mod(window,2)==0:
        window += 1

    # using a Savitzky-Golay filter to strongly smoothe the curve and find the peak area
    smoothed = signal.savgol_filter(y, window , 4, deriv = 0)
    startPoint = smoothed[x > 1].max()

    # get index of start value, first [0] gives array of index, second [0] returns int value, otherwise it would be overwritten as arrays are not copied
    startIndex = np.where(smoothed == startPoint)[0][0]

    # search for ROI
    leftSide = startIndex
    meanVal = smoothed.mean()
    while (smoothed[leftSide] > meanVal and leftSide > 0):
        leftSide -= 1

    rightSide = startIndex
    while (smoothed[rightSide] > meanVal and rightSide < (len(x)-1)):
        rightSide += 1


    for i in range(iterations):
        # refine ROI 
        meanValLeft = smoothed[x < x[leftSide]].mean()
        while (smoothed[leftSide] > meanValLeft and leftSide > 0):
            leftSide -= 1

        meanValRight = smoothed[x > x[rightSide]].mean()    
        while (smoothed[rightSide] > meanValRight and rightSide < (len(x)-1)):
            rightSide += 1

    result = {
            "RoI_low": leftSide,
            "RoI_high": rightSide,
            }
    return result


def calcTreco(x, y, peaks = 3):
    """
    Perform the temperature reconstruction on an input data set either using a fixed or dynamic number of peaks.

    Parameters
    ----------

    x
        array-like or string. If array-like, used as x-axis of analysis, typically time domain of measurement. If string, the call will return a callable to be applied to a data set containing that x column
    y
        array-like or string. If array-like, used as y-axis of analysis, typically photon counts of measurement. If string, the call will return a callable to be applied to a data set containing that y column
    peaks
        None or integer (default=3). If passed, used as fixed number of peaks so be searched. Auto uses an experimental automatic peak detection algorithm.

    Returns
    -------

    dict
        dictionary containing the results of the Treco calculation
    """
    if isinstance(x, str):
        return lambda data: calcTreco(data[x], data[y], peaks) if isinstance(data, pd.DataFrame)  else data.update(calcTreco(data[x], data[y], peaks))

    results = {}
    t = np.array(x)
    tPhotons = np.array(y)

    try:
        roi = calcRoI(t, tPhotons, iterations=0)
        if (roi['RoI_low'] == 0 or roi['RoI_high'] == len(t)):
            Warning('RoI limit set to maximum or minimum value! Indicator for corrupted glow curve at {}'.format(gc_id))
        RoI_low = t[roi['RoI_low']]
        RoI_high = t[roi['RoI_high']] if roi['RoI_high'] < len(t)-1 else t[-2]
        RoI_len = (RoI_high - RoI_low)

        results['Treco_param_RoI_low'] = RoI_low
        results['Treco_param_RoI_high'] = RoI_high

        # assign time and counts within RoI, copy for not overwriting
        tRoI = np.array(t[(t>RoI_low) & (t<RoI_high)])
        tPhotonsRoI = np.array(tPhotons[(t>RoI_low) & (t<RoI_high)])
    except:
        Warning("Error during RoI detection for Treco!")
        results["Treco_error"] = True
        return results

    if not peaks:
        try:
            nSmoothing = int(81)
            if nSmoothing%2 == 0:
                nSmoothing += 1

            smoothedPhotons = signal.savgol_filter(tPhotons,nSmoothing,2)

            # the negative curvature is used as the minimums are easier to be found
            smoothedDeriv = -1*signal.savgol_filter(smoothedPhotons, nSmoothing, 2, deriv=2)

            # cut away the other half of the curve for easier peak detection
            smoothedDeriv[np.where(smoothedDeriv<0)]=0

            # actual peak detection
            peakIndices = peakutils.indexes(smoothedDeriv, thres=0.05*smoothedDeriv.max(), min_dist=(RoI_high-RoI_low)/(8*0.01))

            # cut away peaks outside ROI
            peakIndices = np.delete(peakIndices, np.where(t[peakIndices]>RoI_high))
            peakIndices = np.delete(peakIndices, np.where(t[peakIndices]<RoI_low))
        except:
            Warning("No peak number was specified but automatic detection was not successful")
            results['Treco_error'] = True
            return results

    else:
        peakIndices = np.zeros(peaks)

    if len(peakIndices) <= 3:
        # start values and limits for the three peak gaussian fit
        p0 = np.array([(RoI_high-RoI_low)/3, (RoI_high-RoI_low)/3, RoI_high,
                            RoI_len/6,0,0,
                            tPhotons.max(),tPhotons.max(),tPhotons.max(),
                            tPhotons[np.where(t>RoI_high)[0]].mean()
                            ])
        limitsLow=np.array([(RoI_high-RoI_low)/8,(RoI_high-RoI_low)/8,RoI_high-(RoI_high-RoI_low)/3,
                            0.1, 0, 0,
                            tPhotons.max()/3, tPhotons.max()/2, tPhotons.max()/3,
                            0
                            ])
        limitsHigh=np.array([(RoI_high-RoI_low)/2,(RoI_high-RoI_low)/3,RoI_high,
                            RoI_len/4, 0.2, 0.2,
                            np.inf, np.inf, np.inf,
                                np.inf
                            ])

        fitFunction = utils.gaussianMultiPeak3
    else:
        p0 = np.array([(RoI_high-RoI_low)/3, (RoI_high-RoI_low)/4, (RoI_high-RoI_low)/4, RoI_high,
                        RoI_len/8, 0, 0, 0,
                        0,tPhotons.max(),tPhotons.max(),tPhotons.max(),
                        tPhotons[np.where(t>RoI_high)[0]].mean()
                        ])
        limitsLow=np.array([(RoI_high-RoI_low)/8, (RoI_high-RoI_low)/8,(RoI_high-RoI_low)/8,RoI_high-(RoI_high-RoI_low)/4,
                            0.1, 0, 0, 0,
                            0,tPhotons.max()/4 ,tPhotons.max()/3, tPhotons.max()/3,
                            0
                            ])
        limitsHigh=np.array([(RoI_high-RoI_low)/3, (RoI_high-RoI_low)/3,(RoI_high-RoI_low)/3,RoI_high,
                            RoI_len/6, 0.2, 0.2, 0.2,
                            np.inf, np.inf, np.inf, np.inf,
                            np.inf
                            ])
        fitFunction = utils.gaussianMultiPeak4


    try:
        # try to use the determined peaks as start values except the given ones
        params, cov = curve_fit(
                fitFunction, 
                t, tPhotons, 
                p0 = p0, bounds=[limitsLow, limitsHigh],
            )
        chi = utils.calcRedChisq(tPhotons, fitFunction(t,*params), np.sqrt(tPhotons), len(tPhotons)-len(params))
        results["Treco"] = True
    except Exception as e:
        Warning('Error in temperature reconstruction!')
        results["Treco_error"] = True
        return results
    
    # write the params and errors to the curve
    results['Treco_param_redChi2'] = chi
    if len(peakIndices) > 3:
        param_offset = 1
    else:
        param_offset = 0

    # write peak positions
    results['Treco_param_t5'] = params[2 + param_offset]
    results['Treco_param_t5_std_dev'] = np.sqrt(cov[2 + param_offset, 2 + param_offset])
    results['Treco_param_t4'] = results['Treco_param_t5']-params[1 + param_offset]
    results['Treco_param_t4_std_dev'] = np.sqrt(results['Treco_param_t5_std_dev']**2 + np.sqrt(cov[1 + param_offset , 1 + param_offset])**2)
    results['Treco_param_t3'] = results['Treco_param_t4']-params[param_offset]
    results['Treco_param_t3_std_dev'] = np.sqrt(results['Treco_param_t4_std_dev']**2 + np.sqrt(cov[param_offset, param_offset])**2)

    # write sigmas
    results['Treco_param_sigma3'] = params[3 + 2*param_offset]
    
    results['Treco_param_sigma3_std_dev'] = np.sqrt(cov[3 + 2*param_offset, 3 + 2*param_offset])
    results['Treco_param_sigma4'] = results['Treco_param_sigma3'] + params[1 + 3 + 2*param_offset]
    results['Treco_param_sigma4_std_dev'] = np.sqrt(results['Treco_param_sigma3_std_dev']**2 + np.sqrt(cov[1 + 3 + 2*param_offset , 1 + 3 + 2*param_offset])**2)
    results['Treco_param_sigma5'] = results['Treco_param_sigma4'] + params[2 + 3 + 2*param_offset]
    results['Treco_param_sigma5_std_dev'] = np.sqrt(results['Treco_param_sigma4_std_dev']**2 + np.sqrt(cov[2 + 3 + 2*param_offset, 2 + 3 + 2*param_offset])**2)
    
    # write heights
    results['Treco_param_I5'] = params[2 + 6 + 3*param_offset]
    results['Treco_param_I5_std_dev'] = np.sqrt(cov[2 + 6 + 3*param_offset, 2 + 6 + 3*param_offset])
    results['Treco_param_I4'] = params[1 + 6 + 3*param_offset]
    results['Treco_param_I4_std_dev'] = np.sqrt(cov[1 + 6 + 3*param_offset , 1 + 6 + 3*param_offset])
    results['Treco_param_I3'] = params[6 + 3*param_offset]
    results['Treco_param_I3_std_dev'] = np.sqrt(cov[6 + 3*param_offset, 6 + 3*param_offset])

    # write background
    results['Treco_param_bg'] = params[9 + 3*param_offset]
    results['Treco_param_bg_std_dev'] = np.sqrt(cov[9 + 3*param_offset, 9 + 3*param_offset])

    # additional entries for 4 peaks
    if len(peakIndices) > 3:
        results['Treco_param_t2'] = results['Treco_param_t3'] - params[0]
        results['Treco_param_t2_std_dev'] = np.sqrt(results['Treco_param_t3_std_dev']**2 + np.sqrt(cov[0, 0])**2)

        results['Treco_param_sigma2'] = params[4]
        results['Treco_param_sigma2_std_dev'] = np.sqrt(cov[4, 4])

        results['Treco_param_sigma3'] =  results['Treco_param_sigma3'] + params[4]
        results['Treco_param_sigma3_std_dev'] = np.sqrt(results['Treco_param_sigma3_std_dev']**2 + np.sqrt(cov[4, 4])**2)
        results['Treco_param_sigma4'] =  results['Treco_param_sigma4'] + params[4]
        results['Treco_param_sigma4_std_dev'] = np.sqrt(results['Treco_param_sigma4_std_dev']**2 + np.sqrt(cov[4, 4])**2)
        results['Treco_param_sigma5'] =  results['Treco_param_sigma5'] + params[4]
        results['Treco_param_sigma5_std_dev'] = np.sqrt(results['Treco_param_sigma5_std_dev']**2 + np.sqrt(cov[4, 4])**2)

        results['Treco_param_I2'] = params[8]
        results['Treco_param_I2_std_dev'] = np.sqrt(cov[8,8])
    
    
    # define known peak temperatures
    peakTemperatures = utils.peakTemps
    peakTimes = np.array([results['Treco_param_t3'], results['Treco_param_t4'], results['Treco_param_t5']])
    if len(peakIndices) <= 3:
        peakTemperatures = peakTemperatures[1:]
    else:
        peakTimes = np.insert(peakTimes, 0, results['Treco_param_t2'])


    # fit with given data'preheat_performed' in TrecoInfo.columns and results['preheat_performed'] == 1:
    try:
        TfitParams, TfitCov = curve_fit(lambda x,y,z: utils.exponentialHeating(x,y,z), peakTimes, peakTemperatures)
    except (ValueError, RuntimeError):
        Warning("Error during temperature reconstruction: temperature array creation")
        results["Treco_error"] = True
        return results

    # write data to dataFrame
    results['Treco_param_T0'] = TfitParams[0]
    results['Treco_param_T0_std_dev'] = np.sqrt(TfitCov[0, 0])
    results['Treco_param_alpha'] = TfitParams[1]
    results['Treco_param_alpha_std_dev'] = np.sqrt(TfitCov[1, 1])

    results["Treco_T"] = utils.exponentialHeating(t, TfitParams[0], TfitParams[1])

    return results


if __name__ == "__main__":

    print("A module for glow curve analysis.")

    