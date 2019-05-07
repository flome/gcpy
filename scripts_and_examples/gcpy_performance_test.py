
import os, sys, time
sys.path.append('..')

import pandas as pd
from gcpy import gcdb 


path2testData = '../gcpy/gcpy.test/test_data'

db = gcdb.newDB()

def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size

def test_cycle():
    results = {}
    
    # import new files
    t0 = time.time()
    data = gcdb.readDir(path2testData + '/test_nested_dir', depth=2, db = db)
    dt = time.time()-t0
    results["entries"] = len(data)
    results["import_speed"] = dt
    results["memory_usage"] = get_size(data)

    # store with and without compression
    t0 = time.time()
    gcdb.store(data, "storage_noCompression.json", compress=False)
    dt = time.time()-t0
    results["write_speed_raw"] = dt

    t0 = time.time()
    gcdb.store(data, "storage_withCompression", compress=True)
    dt = time.time()-t0
    results["write_speed_compressed"] = dt

    # read with and without compression
    t0 = time.time()
    newDB = gcdb.load("storage_noCompression.json")
    dt = time.time()-t0
    results["open_speed_raw"] = dt

    t0 = time.time()
    newDB = gcdb.load("storage_withCompression")
    dt = time.time()-t0
    results["open_speed_compressed"] = dt

    # compare file sizes
    results["file_size_raw"] = os.stat('storage_noCompression.json').st_size 
    results["file_size_compressed"] = os.stat('storage_withCompression').st_size 

    # results["storage_size"] = os.stat("localstorage.json").st_size

    os.remove('storage_noCompression.json')
    os.remove('storage_withCompression')
    del data
    return pd.DataFrame(results, index=[0])

anaData = pd.DataFrame()
for i in range(100):
    print("Cycle: ", i+1)
    anaData = anaData.append(test_cycle(), ignore_index=True)

    # protect results from being overwritten accidently
    if os.path.isfile('test_results.csv'):
        raise OSError("Results file already exists! For data protection choose another file name or delete the file explicitely")
    anaData.to_csv('test_results.csv')


