import os, sys, time
sys.path.append('..')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from gcpy import gcdb, gcana

import time

N = 10
res = {
    'entries': [],
    'import': [],
    'gcParam': [],
    'Treco': [],
    'gcFit': [],
    # 'plots': []
}

for i in range(N):
    print("Run ", (i+1), " / ", N)
    t0 = time.time()
    db = gcdb.newDB()
    path2testData = '../tests/test_data/single_files'
    for k in range(10*(i+1)):
        gcdb.readDir(path2testData, db=db)
        
    t1 = t0-time.time()
    res['import'].append(t1)
    res['entries'].append(len(db))

    t0 = time.time()
    gcana.update(db, gcana.calcGCparams('time_sec', 'PhCount'))
    t1 = t0-time.time()
    res['gcParam'].append(t1)

    t0 = time.time()
    gcana.update(db, gcana.calcTreco('time_sec', 'PhCount', peaks=3))
    t1 = t0-time.time()
    res['Treco'].append(t1)

    t0 = time.time()
    gcana.update(db, gcana.gcFit('Treco_T', 'PhCount'), njobs=12)
    t1 = t0-time.time()
    res['gcFit'].append(t1)

    del db

    # t0 = time.time()
    # for doc in db:
    #     plt.plot(doc['gcfit_T'], doc['gcfit_nPhotons'], '.', label='Measurement')
    #     plt.plot(doc['gcfit_T'], doc['gcfit_gcd'], '-', label='Fit result')
    #     for peak in range(2,5+1):
    #         plt.plot(doc['gcfit_T'], doc['gcfit_gcd_peak%s'%peak], '--', label='Peak %s'%(peak))
    #     plt.plot(doc['gcfit_T'], doc['gcfit_gcd_bg'], ':', label='bg')

    #     plt.xlabel('$T$ in K')
    #     plt.ylabel('$N$ in $\\frac{1}{\\mathrm{5\,ms}}$')
    #     plt.legend(loc='best')
    #     plt.savefig('plot%s.png'%doc.doc_id)
    #     plt.clf()
    # t1 = t0-time.time()
    # res['plots'].append(t1)
    
    export = pd.DataFrame(res)
    print(export)

    export.to_csv('full_run_res_multi.csv')