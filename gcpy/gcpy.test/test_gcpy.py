import unittest

import gcpy
import json

singleFilePath_1 = './test_data/single_files/20190319_162420_7.json'
singleFilePath_2 = './test_data/single_files/20190319_162444_8.json'

class GCDBTest(unittest.TestCase):      

    def test_singleFileImport2Memory(self):
        db = gcpy.gcdb.loadFile(singleFilePath_1)
        print(db)
        self.assertEqual(db, json.load(open(singleFilePath_1)))

    def test2(self):
        self.assertEqual(4, 4)