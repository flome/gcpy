import os, sys, time
sys.path.append('..')

import pandas as pd
import numpy as np
from gcpy import gcdb, gcana

from tinydb import where
import matplotlib.pyplot as plt


path2testData = '../gcpy/gcpy.test/test_data'
db = gcdb.newDB()

N = 15

entries = np.zeros(N)
resROI = np.zeros(N)
resTreco = np.zeros(N)
resGCFit = np.zeros(N)

# for i in range(N):
#     print("Run: ", str(i+1), "/", N)
#     gcdb.readDir(path2testData + '/test_nested_dir', depth=2, db=db)
#     entries[i] = len(db)
#     t0 = time.time()
         
#     db.update(gcana.calcRoI('time_sec', 'PhCount'))
#     resROI[i] = time.time()-t0

#     t0 = time.time() 
#     db.update(gcana.calcTreco('time_sec', 'PhCount', peaks=3))
#     resTreco[i] = time.time()-t0


# data = pd.DataFrame({'entries': entries,'RoI': resROI, 'Treco': resTreco})
# data.to_csv('reco_speed_comp.csv')

import multiprocessing as mlp

def process(doc_id):
    
    gcana.calcRoI('time_sec', 'PhCount')(db._storage.memory['_default'][doc_id])
    gcana.calcTreco('time_sec', 'PhCount', peaks=3)(db._storage.memory['_default'][doc_id])

def process_init(syncList):
    process.syncList = syncList

manager = mlp.Manager()


res_multiprocess = np.zeros(N)
db = gcdb.newDB()

for i in range(N):
    print("Run: ", str(i+1), "/", N)
    gcdb.readDir(path2testData + '/test_nested_dir', depth=2, db=db)
    entries[i] = len(db)
    t0 = time.time()

    # syncList = manager.dict(db.storage.memory)
    pool = mlp.Pool(3)#, process_init, [syncList])
    pool.map(process, [x+1 for x in range(len(db))])
    pool.close()
    pool.join()
    # db.write_back(syncList)
    
    res_multiprocess[i] = time.time()-t0

    data = pd.DataFrame({'entries': entries,'multiprocess': res_multiprocess})
    data.to_csv('reco_multiprocess_comp.csv')
# for entry in data:
#     plt.plot(entry['time_sec'], entry['PhCount'])
#     plt.plot([entry['prefit_t%s'%i] for i in [3,4,5]], [entry['prefit_I%s'%i] for i in [3,4,5]], 'ro')
#     plt.show()


