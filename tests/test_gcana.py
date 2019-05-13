import unittest, os
import numpy as np
import pandas as pd
from gcpy import gcana, gcdb

path2testData = os.path.join(os.path.dirname(__file__), 'test_data/single_files')
RoI_keys = ['RoI_low', 'RoI_high']
TReco_keys = ['Treco_T']
gcFit_keys = ['gcfit_Ntot']
GCparam_keys = ['gc_t_nphotonThirdQuarter']

class GCanaTest(unittest.TestCase):

    def test_updateRoIKeys(self):
        print("Testing functionality of RoI detection")
        data = {'x': np.linspace(-5,5), 'y': np.exp(-(np.linspace(-5,5))**2)}
        gcana.calcRoI('x', 'y')(data)
        self.assertTrue(all([key in data.keys() for key in ["RoI_low", "RoI_high"]]))

        data = pd.DataFrame({'x': np.linspace(-5,5), 'y': np.exp(-(np.linspace(-5,5))**2)})
        self.assertTrue(all([key in gcana.calcRoI('x', 'y')(data) for key in ["RoI_low", "RoI_high"]]))

        self.assertTrue(all([key in gcana.calcRoI(data['x'], data['y']) for key in ["RoI_low", "RoI_high"]]))
        print("--> OK")

    def test_calcRoI(self):
        print("Testing insertion of RoI keys to data base")
        db = gcdb.readDir(path2testData)
        print(os.listdir(path2testData))
        db.update(gcana.calcRoI('time_sec', 'PhCount'))
        print("DOC: ", db.get(doc_id=1))
        self.assertTrue(all([key in db.get(doc_id=1).keys() for key in RoI_keys]))
        print("--> OK")

    def test_calcGCparams(self):
        print("Testing insertion of GC param keys to data base")
        db = gcdb.readDir(path2testData)
        db.update(gcana.calcGCparams('time_sec', 'PhCount'))
        ref_doc = db.get(doc_id=1)
        self.assertTrue(all([(key in db.get(doc_id=1).keys()) and (db.get(doc_id=1)[key] is not None) for key in GCparam_keys]))
        self.assertTrue(
            all(
                [
                    ref_doc['gc_Nsig'] < ref_doc['gc_Ntot'],
                    ref_doc['gc_timeRoI_low'] < ref_doc['gc_t_nphotonFirstQuarter'],
                    ref_doc['gc_t_nphotonFirstQuarter'] < ref_doc['gc_t_nphotonThirdQuarter'],
                    ref_doc['gc_t_nphotonThirdQuarter'] < ref_doc['gc_timeRoI_high']
                ]
            )
        )
        print('--> OK')

    def test_Treco(self):
        print("Testing insertion of Treco keys to data base")
        db = gcdb.readDir(path2testData)
        db.update(gcana.calcTreco('time_sec', 'PhCount', peaks=3))
        self.assertTrue(all([(key in db.get(doc_id=1).keys()) and (db.get(doc_id=1)[key] is not None) for key in TReco_keys]))
        print("--> OK")

    def test_gcFit(self):
        print("Testing insertion of Treco keys to data base")
        db = gcdb.readDir(path2testData)
        db.update(gcana.calcTreco('time_sec', 'PhCount', peaks=3))
        db.update(gcana.gcFit('Treco_T', 'PhCount'))
        self.assertTrue(all([(key in db.get(doc_id=1).keys()) and (db.get(doc_id=1)[key] is not None) for key in gcFit_keys]))
        print("--> OK")

    def test_getTable(self):
        print("Test flattening to DataFrame")
        db = gcdb.readDir(path2testData)
        db.update(gcana.calcGCparams('time_sec', 'PhCount'))
        results = gcana.getTable(db)
        self.assertTrue(all([key in results.columns for key in GCparam_keys]))

if __name__ == '__main__':
    unittest.main()