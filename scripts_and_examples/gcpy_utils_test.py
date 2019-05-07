import os, sys, time
sys.path.append('..')

import pandas as pd
import numpy as np
from gcpy import utils
import matplotlib.pyplot as plt

T = np.linspace(350, 570, int((570-350)/2))

N = 100
resC = np.zeros(N)
resNumba = np.zeros(N)
resNon = np.zeros(N)

for i in range(N):
    t0 = time.process_time()
    I = utils.ckitis2006(T, 450, 200, 1.6, Tg = 573.15)
    resC[i] = (time.process_time()-t0)

    t0 = time.process_time()
    I = utils.kitis2006(T, 450, 200, 1.6, Tg = 573.15)
    resNumba[i] = (time.process_time()-t0)

    t0 = time.process_time()
    I = utils.slow_kitis2006(T, 450, 200, 1.6, Tg = 573.15)
    resNon[i] = (time.process_time()-t0)


print(resC.mean(), '+/-', resC.std())
print(resNumba.mean(), '+/-', resNumba.std())
print(resNon.mean(), '+/-', resNon.std())

data = pd.DataFrame({'non_optimized': resNon, 'numba': resNumba, "ctype": resC})
data.to_csv('kitis_speed_comp.csv')