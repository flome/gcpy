"""
    GCpy module for glow curve analysis.
    Author: Florian Mentzel (florian.mentzel@tu-dortmund.de)
    Creation: 2019/05/05
"""

### import depdencencies
# unit tests
import unittest

import time

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
from numba import jit

from . import utils
from scipy.optimize import curve_fit
import uncertainties as unc
from uncertainties import unumpy as unp

import multiprocessing

import gc


def worker(doc, func):
    func(doc)
    return doc

def update(data, func, njobs=-1):
    """
    Use a function to update given data using one or more threads 
    
    Parameters
    ---------
    data
        data to apply function to
    
    func
        function to be applied

    njobs
        integer (default=-1). If -1, all available processors are used, otherwise the specified number of workers is launched
    
    Returns
    ----------
    The function updates the data and does not return data

    """ 
    pool = multiprocessing.Pool(processes=njobs if njobs != -1 else multiprocessing.cpu_count()-1)

    if isinstance(data, dict):
        docs = [data]
    elif isinstance(data, list):
        docs = data
    else:
        docs = data.all()

    results = [pool.apply_async(worker, args=(doc, func)) for doc in docs]
    docs = None

    results = [result.get() for result in results]
    if isinstance(data, dict):
        return results[0]
    elif isinstance(data, list):
        return results
    else:
        data.write_back(results)
        return

def stripArrays(data, exclude=None):
    """
    Deletes array entries except excluded ones to save memory
    
    Parameters
    ---------
    data
        data base or list of documents
    exclude
        list of array names to keep
    
    Returns
    ---------
    
    data
        input data minus entries which had arrays

    """ 

    if isinstance(data, dict):
        docs = [data]
    elif isinstance(data, list):
        docs = data
    else:
        raise AttributeError("Invalid input type: ", data.dtype)

    for doc in docs:
        keys2del = []
        for key in doc:
            if isinstance(doc[key], (np.ndarray, list)):
                keys2del.append(key)

        for key in keys2del:
            del doc[key]
    
    if isinstance(data, dict):
        return docs[0]
    elif isinstance(data, list):
        return docs


def getTable(db, asDataFrame=True):
    """
    Returns a table of data from the data base. 
    
    Parameters
    ---------
    db
        data base or list of documents to get the parameters from
    
    Returns
    ---------
    
    data
        pandas DataFrame

    """ 

    if asDataFrame:
        # if it is a list, some form of querying has happend, else get all documents
        if not isinstance(db, list):
            db = db.all()

        results = pd.DataFrame(db)

    else: 
        results = db.storage.memory

    return results


def calcGCparams(x, y):
    """
    Compute standard parameters directly from the glow curve
    
    Parameters
    ---------
    x
        string or list or array. x-axis for the data, generally the time axis for glow curve analysis. If a string is passed, a callable is returned

    y
        string or list or array. y-axis for the data, generally the photon counts for glow curve analysis. If a string is passed, a callable is returned

    Returns
    ---------
    dict
        dictionary containing the results

    """

    if isinstance(x, str):
        return calcGCparamsWrapper(x, y)
        #return lambda data: calcGCparams(data[x], data[y]) if isinstance(data, pd.DataFrame)  else data.update(calcGCparams(data[x], data[y]))

    results = {}
    x = np.array(x)
    y = np.array(y)
   
    #### Curve data #####
    nphotonMean = y.mean()
    nphotonMax = y.max()
    tMax = x[y == y.max()]
    results['gc_Ntot'] = np.sum(y)
    results['gc_Nmean'] = nphotonMean
    results['gc_Nmax'] = nphotonMax
    results['gc_tmax'] = tMax[0]

    #### RoI #######
    # calculate TU ROI
    roi = calcRoI(x, y)
    RoI_low_TU = x[roi['RoI_low']]
    RoI_up_TU = x[roi['RoI_high']]
    results['gc_timeRoI_low'] = RoI_low_TU
    results['gc_timeRoI_high'] = RoI_up_TU
    results['gc_timeRoI_length'] =RoI_up_TU-RoI_low_TU

    #### calc sig and bg counts #####
    results['gc_tBinSize'] = x[1] - x[0]
    bgROI = np.sum(y[x > RoI_up_TU])
    bgROI += np.sum(y[x < RoI_low_TU])
    integral = np.sum(y[x < RoI_up_TU])
    integral -= np.sum(y[x < RoI_low_TU])
    results['gc_NtRoI'] = integral

    # add results to data frame
    results['gc_Nbg_m'] = (np.mean(y[x > RoI_up_TU])-np.mean(y[x < RoI_low_TU]))/(RoI_up_TU-RoI_low_TU)
    results['gc_Nbg_b'] = np.mean(y[x < RoI_low_TU])-results['gc_Nbg_m']*RoI_low_TU
    results['gc_Nbg'] = bgROI + (RoI_up_TU-RoI_low_TU)/results['gc_tBinSize']*(np.mean(y[x > RoI_up_TU])+0.5*np.mean(y[x < RoI_low_TU]))
    results['gc_Nsig'] = results['gc_Ntot'] - results['gc_Nbg']

    #### calculate cumulated sums ######
    RoI_photons = y[x < RoI_up_TU]
    tCumSum = x[x < RoI_up_TU]
    RoI_photons = RoI_photons[tCumSum > RoI_low_TU]
    tCumSum = x[x > RoI_low_TU]

    photonCumSum = RoI_photons.cumsum()
    results['gc_t_nphotonFirstQuarter'] = tCumSum[np.where(photonCumSum <= 0.25*photonCumSum[-1])[0].max()]
    results['gc_t_nphotonSecondQuarter'] = tCumSum[np.where(photonCumSum <= 0.50*photonCumSum[-1])[0].max()]
    results['gc_t_nphotonThirdQuarter'] = tCumSum[np.where(photonCumSum <= 0.75*photonCumSum[-1])[0].max()]

    return results

class calcGCparamsWrapper(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __call__(self, data):
        return data.update(calcGCparams(data[self.x], data[self.y]))


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

    x = np.array(x)
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
        return calcTrecoWrapper(x, y, peaks)
        # return lambda data: calcTreco(data[x], data[y], peaks) if isinstance(data, pd.DataFrame)  else data.update(calcTreco(data[x], data[y], peaks))

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
            nSmoothing = int(105)
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
                            0, tPhotons.max()/2, tPhotons.max()/3,
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
        results["Treco_performed"] = True
    except Exception as e:
        Warning('Error in temperature reconstruction!')
        results["Treco_error"] = True
        return results
    
    # write the params and errors to the curve
    results['Treco_redChi2'] = chi
    if len(peakIndices) > 3:
        param_offset = 1
    else:
        param_offset = 0

    # write peak positions
    results['Treco_t5'] = params[2 + param_offset]
    results['Treco_t5_std_dev'] = np.sqrt(cov[2 + param_offset, 2 + param_offset])
    results['Treco_t4'] = results['Treco_t5']-params[1 + param_offset]
    results['Treco_t4_std_dev'] = np.sqrt(results['Treco_t5_std_dev']**2 + np.sqrt(cov[1 + param_offset , 1 + param_offset])**2)
    results['Treco_t3'] = results['Treco_t4']-params[param_offset]
    results['Treco_t3_std_dev'] = np.sqrt(results['Treco_t4_std_dev']**2 + np.sqrt(cov[param_offset, param_offset])**2)

    # write sigmas
    results['Treco_sigma3'] = params[3 + 2*param_offset]
    
    results['Treco_sigma3_std_dev'] = np.sqrt(cov[3 + 2*param_offset, 3 + 2*param_offset])
    results['Treco_sigma4'] = results['Treco_sigma3'] + params[1 + 3 + 2*param_offset]
    results['Treco_sigma4_std_dev'] = np.sqrt(results['Treco_sigma3_std_dev']**2 + np.sqrt(cov[1 + 3 + 2*param_offset , 1 + 3 + 2*param_offset])**2)
    results['Treco_sigma5'] = results['Treco_sigma4'] + params[2 + 3 + 2*param_offset]
    results['Treco_sigma5_std_dev'] = np.sqrt(results['Treco_sigma4_std_dev']**2 + np.sqrt(cov[2 + 3 + 2*param_offset, 2 + 3 + 2*param_offset])**2)
    
    # write heights
    results['Treco_I5'] = params[2 + 6 + 3*param_offset]
    results['Treco_I5_std_dev'] = np.sqrt(cov[2 + 6 + 3*param_offset, 2 + 6 + 3*param_offset])
    results['Treco_I4'] = params[1 + 6 + 3*param_offset]
    results['Treco_I4_std_dev'] = np.sqrt(cov[1 + 6 + 3*param_offset , 1 + 6 + 3*param_offset])
    results['Treco_I3'] = params[6 + 3*param_offset]
    results['Treco_I3_std_dev'] = np.sqrt(cov[6 + 3*param_offset, 6 + 3*param_offset])

    # write background
    results['Treco_bg'] = params[9 + 3*param_offset]
    results['Treco_bg_std_dev'] = np.sqrt(cov[9 + 3*param_offset, 9 + 3*param_offset])

    # additional entries for 4 peaks
    if len(peakIndices) > 3:
        results['Treco_t2'] = results['Treco_t3'] - params[0]
        results['Treco_t2_std_dev'] = np.sqrt(results['Treco_t3_std_dev']**2 + np.sqrt(cov[0, 0])**2)

        results['Treco_sigma2'] = params[4]
        results['Treco_sigma2_std_dev'] = np.sqrt(cov[4, 4])

        results['Treco_sigma3'] =  results['Treco_sigma3'] + params[4]
        results['Treco_sigma3_std_dev'] = np.sqrt(results['Treco_sigma3_std_dev']**2 + np.sqrt(cov[4, 4])**2)
        results['Treco_sigma4'] =  results['Treco_sigma4'] + params[4]
        results['Treco_sigma4_std_dev'] = np.sqrt(results['Treco_sigma4_std_dev']**2 + np.sqrt(cov[4, 4])**2)
        results['Treco_sigma5'] =  results['Treco_sigma5'] + params[4]
        results['Treco_sigma5_std_dev'] = np.sqrt(results['Treco_sigma5_std_dev']**2 + np.sqrt(cov[4, 4])**2)

        results['Treco_I2'] = params[8]
        results['Treco_I2_std_dev'] = np.sqrt(cov[8,8])
    
    
    # define known peak temperatures
    peakTemperatures = utils.peakTemps
    peakTimes = np.array([results['Treco_t3'], results['Treco_t4'], results['Treco_t5']])
    if len(peakIndices) <= 3:
        peakTemperatures = peakTemperatures[1:]
    else:
        peakTimes = np.insert(peakTimes, 0, results['Treco_t2'])


    # fit with given data'preheat_performed' in TrecoInfo.columns and results['preheat_performed'] == 1:
    try:
        TfitParams, TfitCov = curve_fit(exponentialHeatingWrapper(), peakTimes, peakTemperatures)
    except (ValueError, RuntimeError):
        Warning("Error during temperature reconstruction: temperature array creation")
        results["Treco_error"] = True
        return results

    # write data to dataFrame
    results['Treco_T0'] = TfitParams[0]
    results['Treco_T0_std_dev'] = np.sqrt(TfitCov[0, 0])
    results['Treco_alpha'] = TfitParams[1]
    results['Treco_alpha_std_dev'] = np.sqrt(TfitCov[1, 1])

    results["Treco_T"] = utils.exponentialHeating(t, TfitParams[0], TfitParams[1])

    return results

class exponentialHeatingWrapper(object):
    def __init__(self):
        self.fitFunc = utils.exponentialHeating
    def __call__(self, x, y, z):
        return  self.fitFunc(x, y, z)


class calcTrecoWrapper(object):
    def __init__(self, x, y, peaks):
        self.x = x
        self.y = y
        self.peaks = peaks
    def __call__(self, data):
        return data.update(calcTreco(data[self.x], data[self.y], self.peaks))

@jit(nopython=False)
def fitmethod_kitis98(x, T1, T2, T3, T4, I1, I2, I3, I4, E1, E2, E3, E4 , A, B, C, D):
        I = 0
        I += utils.kitis1998(x, T1, I1, E1)
        I += utils.kitis1998(x, T2, I2, E2)
        I += utils.kitis1998(x, T3, I3, E3)
        I += utils.kitis1998(x, T4, I4, E4)
        bg = utils.backgroundFunction(x, A, B, C, D)
        bg = np.where(bg<0,0,bg)
        
        return I+bg

@jit(nopython=False)
def fitmethod_kitis06(x, T1, T2, T3, T4, I1, I2, I3, I4, E1, E2, E3, E4 , A, B, C, D):
    I = 0
    I += utils.ckitis2006(x, T1, I1, E1)
    I += utils.ckitis2006(x, T2, I2, E2)
    I += utils.ckitis2006(x, T3, I3, E3)
    I += utils.ckitis2006(x, T4, I4, E4)
    bg = utils.backgroundFunction(x, A, B, C, D)
    bg = np.where(bg<0,0,bg)
    
    return I+bg

## Glow curve fit
def gcFit(x, y):
    """
    Perform the glow curve deconvolution for a given glow curve.

    Parameters
    ----------

    x
        array-like or string. If array-like, used as x-axis of analysis, should be temperature array from Treco. If string, the call will return a callable to be applied to a data set containing that x column
    y
        array-like or string. If array-like, used as y-axis of analysis, typically photon counts of measurement. If string, the call will return a callable to be applied to a data set containing that y column
    
    Returns
    -------

    GCio object containing the fitted data.
    """

    if isinstance(x, str):
        return gcFitWrapper(x, y) #if isinstance(data, pd.DataFrame)  else data.update(gcFitWrapper(data[x], data[y]))
        # return lambda data: gcFit(data[x], data[y]) if isinstance(data, pd.DataFrame)  else data.update(gcFit(data[x], data[y]))

    results = {}
    T = np.array(x)
    tPhotons = np.array(y)

    ################################################################################################
    errors_kitis1998 = 0
    errors_kitis2006 = 0
    errors_red_chi2_greater_10 = 0

    binWidth = 2.5
        
    gcTemp = np.linspace(T.min(), T.max(), int((T.max()- T.min())/binWidth))
    gcPhotons = utils.rebinHistRescale(T , tPhotons, gcTemp)

    upperTCut = 580
    lowerTCut = 350

    indices = np.where([gcTemp>lowerTCut, gcTemp<upperTCut])
    indices = np.intersect1d(indices[1][np.where(indices[0] == 0)],indices[1][np.where(indices[0] == 1)])
    gcTemp = gcTemp[indices]
    gcPhotons = gcPhotons[indices]

    results["gcfit_T"] = gcTemp
    results["gcfit_nPhotons"] = gcPhotons

    # initialize start values
    startT = utils.peakTemps
    startE = np.array([1.25,1.55,1.46,2.4])
    startI = np.array([100,gcPhotons.max()/3,gcPhotons.max()/2,0.9*gcPhotons.max()])
    startBg = np.array([100,gcTemp.max()+1,1e-15,1e-2])
    p0 = np.concatenate((startT, startI, startE, startBg))
    
    bounds = ([startT[0]-10,startT[1]-10,startT[2]-10,startT[3]-10,
            0,0,0,0,0.5,1,1,1,0,gcTemp.max()+1,0,0.0], #minima
            [startT[0]+10,startT[1]+10,startT[2]+10,startT[3]+10,
            np.inf,np.inf,np.inf,np.inf,2.3,3.5,3.4,4.5,np.inf,580,10,.1] #maxima
            )

    # fit marker
    error = False
    prefitVals = None

    # actual fit
    t0 = time.time()
    
    try:
        params, cov = curve_fit(fitmethod_kitis98, gcTemp, gcPhotons, p0 = p0, 
                                bounds = bounds,
                                )
        prefitVals = params
    except Exception as e:
        results["gcfit_prefit_error"] = True

        Warning('Fit error kitis 98')
    
    if isinstance(prefitVals, np.ndarray):
        p0 = prefitVals

    try:
        params, cov = curve_fit(fitmethod_kitis06, gcTemp, gcPhotons, p0 = p0, 
                                bounds = bounds,
                                )
    except Exception as e:
        Warning('Fit error kitis 06')
        results["gcfit_error"] = True
        return results
    
    tcpu = round(1000*(time.time()-t0), 3)

    fitValues = params
    fitErrors = np.sqrt(np.diag(cov))

    I_pred = fitmethod_kitis06(gcTemp, *params)
    results["gcfit_gcd"] = I_pred
    chiSquare = utils.calcRedChisq(gcPhotons,I_pred,np.sqrt(gcPhotons),len(gcPhotons)-len(params))

    ####################### data extraction #################
    #########################################################
    results["gcfit_cpuTime"] = tcpu
    results["gcfit_redChi2"] = chiSquare
    Nsig =  0#unc.ufloat(0,0)
    
    for peak in range(4):
        results["gcfit_Tm%s"%(peak+2)] = fitValues[peak]
        results["gcfit_Tm%s_std_dev"%(peak+2)] = fitErrors[peak]

        results["gcfit_Im%s"%(peak+2)] = fitValues[peak+4]
        results["gcfit_Im%s_std_dev"%(peak+2)] = fitErrors[peak+4]

        results["gcfit_E%s"%(peak+2)] = fitValues[peak+8]
        results["gcfit_E%s_std_dev"%(peak+2)] = fitErrors[peak]+8
        
        peakI = utils.ckitis2006(gcTemp, fitValues[peak], fitValues[peak+4], fitValues[peak+8])
        results["gcfit_gcd_peak%s"%(peak+2)] = peakI

        N_peakI = peakI[1:]*np.diff(gcTemp)
        results["gcfit_N%s"%(peak+2)] = np.sum(N_peakI)
        Nsig += np.sum(N_peakI)
        
        results["gcfit_Nsig"] = Nsig

        uA = unc.ufloat(fitValues[-4], fitErrors[-4])
        uB = unc.ufloat(fitValues[-3], fitErrors[-3])
        uC = unc.ufloat(fitValues[-2], fitErrors[-2])
        uD = unc.ufloat(fitValues[-1], fitErrors[-1])
        uIbg = (uA/(uB-gcTemp)+uC * unp.exp((gcTemp-300)*uD))
        uIbg = np.where(unp.nominal_values(uIbg) < 0,0,uIbg) 

        # uNbg = (uA/(uB-gcTemp[1:])+uC * unp.exp((gcTemp[1:]-300)*uD))*np.diff(gcTemp)
        # uNbg = np.where(unp.nominal_values(uNbg) < 0,0,uNbg) 
        results["gcfit_gcd_bg"] = unp.nominal_values(uIbg)
        uNbg = uIbg[1:]*np.diff(gcTemp)

        results["gcfit_a"] = fitValues[-4]
        results["gcfit_a_std_dev"] = fitErrors[-4]
        results["gcfit_b"] = fitValues[-3]
        results["gcfit_b_std_dev"] = fitErrors[-3]
        results["gcfit_c"] = fitValues[-2]
        results["gcfit_c_std_dev"] = fitErrors[-2]
        results["gcfit_d"] = fitValues[-1]
        results["gcfit_d_std_dev"] = fitErrors[-1]
        
        try:
            results["gcfit_Nbg"] = np.sum(uNbg).nominal_value
            results["gcfit_Nbg_std_dev"] = np.sum(uNbg).std_dev
        
            results["gcfit_Ntot"] = (Nsig+np.sum(uNbg)).nominal_value
            results["gcfit_Ntot_std_dev"] = (Nsig+np.sum(uNbg)).std_dev

        except AttributeError:
            results["gcfit_Nbg"] = -1
            results["gcfit_Nbg_std_dev"] = -1
            results["gcfit_Ntot"] = -1
            results["gcfit_Ntot_std_dev"] = -1

    return results

class gcFitWrapper(object):
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __call__(self, data):
        return data.update(gcFit(data[self.x], data[self.y]))


if __name__ == "__main__":

    print("A module for glow curve analysis.")

    