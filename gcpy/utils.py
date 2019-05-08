"""
	GCpy module containing useful functions.
	Author: Florian Mentzel (florian.mentzel@tu-dortmund.de)
	Creation: 2019/05/05
"""

import numpy as np
import math
from sys import platform
from numba import jit

peakTemps = np.array([441.36, 483.11, 512.1, 537.02])

if platform in ["linux", "linux2", "darwin","darwin2"]:
	if platform[0] == "l":
		path2lib = '/lib/kitis2006.so'
	else:
		path2lib = '/lib/kitis2006_mac.so'

	try:
		import ctypes
		import os
		_cfunc = ctypes.CDLL(os.path.dirname(__file__) + path2lib)
		_cfunc.kitis2006.argtypes = (ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double))
		_cfunc.kitis2006.restype = ctypes.POINTER(ctypes.c_double)
	except:
		_cfunc = None
		print('C boosted functions are not available')
else:
	_cfunc = None
	print("Some features like C boosted functions are only available on Linux and Mac OS systems.")


def gaussian(x, mu, sigma, I):
	y = I*np.exp(-(x-mu)**2/2/sigma**2)
	return y
	
# definition of a thee peak gaussian function with constant background
@jit(nopython=True)
def gaussianMultiPeak3(t, dx2, dx3, x4, sig2, dsig3, dsig4, I2, I3, I4, c):
	x3 = x4-dx3
	x2 = x3-dx2
	sig3 = sig2+dsig3
	sig4 = sig3+dsig4
	I = I2*np.exp(-(t-x2)*(t-x2)/(2*sig2*sig2))
	I += I3*np.exp(-(t-x3)*(t-x3)/(2*sig3*sig3))
	I += I4*np.exp(-(t-x4)*(t-x4)/(2*sig4*sig4))
	I += c

	return I

# definition of a four peak gaussian function with constant background
@jit(nopython=True)
def gaussianMultiPeak4(t, dx1, dx2, dx3, x4, sig1, dsig2, dsig3, dsig4, I1, I2, I3, I4, c):
	x3 = x4-dx3
	x2 = x3-dx2
	x1 = x2-dx1
	sig2 = sig1+dsig2
	sig3 = sig2+dsig3
	sig4 = sig3+dsig4
	I = I1*np.exp(-(t-x1)*(t-x1)/(2*sig1*sig1))
	I += I2*np.exp(-(t-x2)*(t-x2)/(2*sig2*sig2))
	I += I3*np.exp(-(t-x3)*(t-x3)/(2*sig3*sig3))
	I += I4*np.exp(-(t-x4)*(t-x4)/(2*sig4*sig4))
	I += c

	return I

def rebinHistRescale(x_old,y_old,x_new=[],rebinFactor=0):
	if len(x_new) > 0:        
		indices = np.digitize(x_old,x_new)
		y_rebin = np.append([0],[y_old[indices == i].sum()/(x_new[i]-x_new[i-1]) for i in range(1, len(x_new))])
	return y_rebin

def calcRedChisq(yTrue, yFit, sigmaTrue, dof=1.):
	sigmaTrue[np.where(sigmaTrue==0)] = np.sqrt(yFit[np.where(sigmaTrue==0)])
	return np.sum(np.power((np.array(yTrue)-np.array(yFit)),2)/np.power(sigmaTrue,2))/dof

# define exponential heating function
@jit(nopython=True)
def exponentialHeating(t, T0, alpha, Tg = 573.15):
	T = Tg-(Tg-T0)*np.exp(-alpha*t)
	return T

def kitis1998(T, Tm, Im, E):
	k = 8.61733e-05 ; #Boltzmann constant k_B[eV/K]
	arg = E*(T-Tm)/(k*T*Tm);		
	
	return Im*np.exp(1.+arg-(T/Tm)**2*np.exp(arg)*(1.-2*k*T/E)-2*k*Tm/E)

def ckitis2006(T, Tm, Im, E, Tg = 573.15):
	global _cfunc

	if(isinstance(T, np.ndarray)):
		T = T.tolist()
	if(isinstance(T, (float, int))):
		T = [T]

	lenT = len(T)
	par = [Tm, Im, E, Tg]

	array_typePar = ctypes.c_double * 4
	array_typeT = ctypes.c_double * lenT

	Ipointer = _cfunc.kitis2006(ctypes.c_int(lenT), array_typeT(*T), array_typePar(*par))

	I = np.array(Ipointer[0:lenT])

	return I

def backgroundFunction(x, a, b, c, d):
        return a/(b-x)+c*np.exp((x-300)*d)

@jit(nopython=True)
def factorial(n):
	return np.array([i+1 for i in range(n)]).prod()

@jit(nopython=True)
def kitis2006(T, Tm, Im, E, Tg = 573.15):

	TLintensity = -1*np.ones(len(T))
	k = 8.61733e-05 

	for i,Ti in enumerate(T):

			z = np.abs(E*(Ti-Tg)/(k*Ti*Tg))
			zm = np.abs(E*(Tm-Tg)/(k*Tm*Tg))

			if z > 10:

				Z_asa = 0.
				Zm_asa = 0.

				for n in range(int(z)+1):
					Z_asa += np.power(-1,n)*factorial(n)*np.power((k*Ti)/E,n)*(np.power(Tg/(Tg-Ti),n+1)-1)

				for n in range(int(zm)+1):
					Zm_asa += np.power(-1,n)*factorial(n)*np.power((k*Tm)/E,n)*(np.power(Tg/(Tg-Tm),n+1)-1)

				Z_asa += 0.5*np.power(-1,int(z)+1)*factorial(int(z)+1)*np.power((k*Ti)/E,int(z)+1)*(np.power(Tg/(Tg-Ti),int(z)+2)-1)
				Zm_asa += 0.5*np.power(-1,int(zm)+1)*factorial(int(zm)+1)*np.power((k*Tm)/E,int(zm)+1)*(np.power(Tg/(Tg-Tm),int(zm)+2)-1)

				TLintensity[i] = Im*np.exp(-1*E*(Tm-Ti)/(k*Ti*Tm) + (Tg-Tm)/Tm * (Zm_asa - Ti/Tm*np.exp(-1*E*(Tm-Ti)/(k*Ti*Tm))*Z_asa))
			
			else:

				Z1_csa = 0.5772156649 + np.log(np.abs(E/(k*Ti)*(Ti-Tg)/Tg))
				Z1m_csa = 0.5772156649 + np.log(np.abs(E/(k*Tm)*(Tm-Tg)/Tg))
				Z2_csa = 0.
				Z2m_csa = 0.

				for n in range(1,51):
					Z1_csa += np.power(E/(k*Ti)*(Ti-Tg)/Tg,n)/(n*factorial(n))
					Z1m_csa += np.power(E/(k*Tm)*(Tm-Tg)/Tg,n)/(n*factorial(n))

				for n in range(int(z)+1):
					Z2_csa += np.power(-1,n)*factorial(n)*np.power(k*Ti/E,n)
				for n in range(int(zm)+1):
					Z2m_csa += np.power(-1,n)*factorial(n)*np.power(k*Tm/E,n)

				Z2_csa += 0.5*np.power(-1,int(z)+1)*factorial(int(z)+1)*np.power(k*Ti/E,int(z)+1)
				Z2m_csa += 0.5*np.power(-1,int(zm)+1)*factorial(int(zm)+1)*np.power(k*Tm/E,int(zm)+1)
				
				TLintensity[i] = Im*np.exp(-1*E*(Tm-Ti)/(k*Ti*Tm) - E*(Tg-Tm)/(k*np.power(Tm,2)) * np.exp(E*(Tg-Tm)/(k*Tm*Tg))*(Z1m_csa-Z1_csa) - (Tg-Tm)/Tm *(Z2m_csa - Z2_csa*Ti/Tm * np.exp(-1*E*(Tm-Ti)/(k*Ti*Tm))))

	TLintensity[TLintensity > Im] = 0
	return TLintensity

