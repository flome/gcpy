"""
    GCpy module for glow curve simulation.
    Author: Florian Mentzel (florian.mentzel@tu-dortmund.de)
    Creation: 2019/05/05
"""

from . import utils
import pandas as pd
import numpy as np
import os, json

functions_D = {
    'Tm2': utils.linear,
    'Tm3': utils.linear,
    'Tm4': utils.linear,
    'Tm5': utils.linear,
    'E2': utils.linear,
    'E3': utils.linear,
    'E4': utils.linear,
    'E5': utils.linear,
    'Im2': utils.linear,
    'Im3': utils.linear,
    'Im4': utils.linear,
    'Im5': utils.linear,
    'T0': utils.linear,
    'alpha': utils.linear
}

functions_t = {
    'Tm2': utils.quad,
    'Tm3': utils.quad,
    'Tm4': utils.quad,
    'Tm5': utils.quad,
    'E2': utils.exponential_peak_3,
    'E3': utils.exponential,
    'E4': utils.exponential,
    'E5': utils.exponential,
    'Im2': utils.exponentialIm2,
    'Im3': utils.exponential_peak_3,
    'Im4': utils.exponential_peak_2,
    'Im5': utils.linear,
    'T0': utils.quad,
    'alpha': utils.quad
}

functions_tpre = {
    'Tm2': utils.quad,
    'Tm3': utils.quad,
    'Tm4': utils.quad,
    'Tm5': utils.quad,
    'E2': utils.quad,
    'E3': utils.quad,
    'E4': utils.quad,
    'E5': utils.quad,
    'Im2': utils.exponential_tpre_peak2,
    'Im3': utils.quad,
    'Im4': utils.quad,
    'Im5': utils.quad,
}

functions_params = {
    utils.linear: ['a', 'b'],
    utils.quad: ['a', 'b', 'c'],
    utils.exponential: ['a', 'b', 'c'],
    utils.exponential_peak_2: ['a', 'b', 'c'],
    utils.exponential_2sum: ['a', 'b', 'c', 'd'],
    utils.exponential_peak_3: ['a', 'b', 'c', 'd'],
    utils.exponentialIm2: ['a', 'b', 'c', 'd'],
    utils.exponential_tpre_peak2: ['a', 'b', 'c', 'd']
    }

Tg = 573
start_time = 0
end_time = 20
start_T = 300
end_T = 570

step_default = {
    'time': 0.01,
    'temperature': 2.5
}

sim_parameters = {
    'dose': 1,
    'dt_post': 1,
    'dt_pre': 0,
    'signal_noise': True,
}

empirical_parameters = json.load(open(os.path.join(os.path.dirname(__file__), 'lib', 'simulation_parameters.json')))
def getParams(which=None):
    if which is None:
        return empirical_parameters
    else:
        return empirical_parameters[which]
 

def computeKinetics(sim_settings=sim_parameters, sim_parameters=empirical_parameters):
    """
    Internal function for glow curve simulation. Computes the kinetic parameters for given dose and fading time from the parameter pickle.
    """
    
    if sim_settings['dt_post'] == 0:
        sim_settings['dt_post'] = 1/60
        print('WARNING: fading time must be greater zero, set to 1 second')

    kinetic_parameters = {}
    for key in functions_D.keys():
        
        doseFunction = functions_D[key]
        doseParams = list(val for val in sim_parameters['dose'][key].values() if val is not None)[::2]

        fadingFunction = functions_t[key]
        fadingParams = list(val for val in sim_parameters['dt_post'][key].values() if val is not None)[::2]

        doseMean = doseFunction(sim_settings['dose'], *doseParams)
        if fadingFunction(sim_settings['dt_pre']*24, *fadingParams) > 1e-5:
            fadingMean = fadingFunction(sim_settings['dt_post']+sim_settings['dt_pre']*24, *fadingParams)/fadingFunction(sim_settings['dt_pre']*24, *fadingParams)
        else:
            fadingMean = 1
        value = doseMean*fadingMean    
        kinetic_parameters[key] = value

    for key in functions_tpre.keys():
        preIrrad_Function = functions_tpre[key]
        preIrrad_Params = list(val for val in sim_parameters['dt_pre'][key].values() if val is not None) [::2]
        
        preIrrad_Mean = preIrrad_Function(sim_settings['dt_pre'], *preIrrad_Params)
        kinetic_parameters[key] *= preIrrad_Mean
    
    return kinetic_parameters



def genCurve(kinetic_parameters, time_col, photon_col):
        """
        Internal method for glow curve simulation. Generates the curve DataFrame.
        """
        result = {}
        start = start_time
        stop = end_time
        step = step_default['time']
     
        t = np.linspace(start, stop, int((stop-start)/step))
        T = utils.exponentialHeating(t, kinetic_parameters['T0'], kinetic_parameters['alpha'])
      
        result[time_col] = t
        result['sim_T'] = T
        
        lower = T[:-1].copy()
        upper = T[1:].copy()

        I = np.zeros((4,len(t)))
        function = utils.ckitis2006
        
        for peak in [0,1,2,3]:          
            peak_I = function(np.append((upper+lower)/2, upper[-1]), kinetic_parameters['Tm%s'%(peak+2)], kinetic_parameters['Im%s'%(peak+2)], kinetic_parameters['E%s'%(peak+2)])*np.append((upper-lower), 0)
            I[peak] = np.where(peak_I<0, 0, peak_I)
            
        # bg = utils.backgroundFunction(np.append((upper+lower)/2, upper[-1]), kinetic_parameters['a'],  kinetic_parameters['b'],  kinetic_parameters['c'],  kinetic_parameters['c'])*np.append((upper-lower), 0)
        # bg = np.where(bg<0, 0, bg)
        tPhotons = I.sum(axis=0)
       
        scaler = 1
        scaler = step_default['temperature']
        y = (np.sum(I, axis=0))*scaler

        # result['sim_bg'] = bg*scaler
        result['sim_PhCount'] = tPhotons*scaler
        for peak in [2,3,4,5]:
            result['sim_Phcount_peak%s'%peak] = I[peak-2]*scaler


        ### handle signal noise setting
        if sim_parameters['signal_noise']:
            y = np.array(list(map(lambda x: np.random.poisson(lam=x), y)))

        result['PhCount'] = y
        return result


def generate(sim_params=None, kinetic_params=None, time_col='time_sec', photon_col='PhCount'):
       
        if sim_params:
            sim_parameters.update(sim_params)

        kinetic_parameters = computeKinetics()   
        if kinetic_params:
            kinetic_parameters.update(kinetic_params)    

        curve = genCurve(kinetic_parameters, time_col, photon_col)
        return curve
