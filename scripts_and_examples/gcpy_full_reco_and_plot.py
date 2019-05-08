import os, sys, time
sys.path.append('..')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from gcpy import gcdb, gcana

path2testData = '../tests/test_data/single_files'
db = gcdb.readDir(path2testData)
db.update(gcana.calcTreco('time_sec', 'PhCount', peaks=3))
db.update(gcana.gcFit('Treco_T', 'PhCount'))

print(db.all())