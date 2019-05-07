import unittest, os, json
from gcpy import gcdb

singleFilePath_1 = os.path.join(os.path.dirname(__file__),'test_data/single_files/20190319_162420_7.json')
singleFilePath_2 = os.path.join(os.path.dirname(__file__), 'test_data/single_files/20190319_162444_8.json')
testdirPath = os.path.join(os.path.dirname(__file__), 'test_data/test_nested_dir')
testdbString = 'test_db.json'
testStorageString = "test_storage"

class GCDBTest(unittest.TestCase):  

    def test_store_open(self):
        print("Test storage and opening of data base")
        db = gcdb.readDir(testdirPath, depth=3)
        gcdb.store(db, testStorageString)
        newDB = gcdb.load(testStorageString)
        self.assertEqual(db.all(), newDB.all())
        os.remove(testStorageString)
        print("--> OK")    

    def test_dirImport(self):
        print("Test import of a nested directory with varying depth")
        db = gcdb.readDir(testdirPath, depth=1)
        self.assertEqual(len(db), 1)
        db = gcdb.readDir(testdirPath, depth=2)
        self.assertEqual(len(db), 5)
        db = gcdb.readDir(testdirPath, depth=3)
        self.assertEqual(len(db), 6)
        print("--> OK")

    def test_singleFileImport2Memory(self):
        print("Loading a single data point into memory data base")
        # load the specified file using the function
        db = gcdb.readFiles(singleFilePath_1)
        # compare whether it actually maches the imported file as json structure
        with open(singleFilePath_1) as testFile:
            data2compare = json.load(testFile)
            data2compare.update({'filename': singleFilePath_1})
            self.assertEqual(db.get(doc_id=1), data2compare)
            print("--> OK")

    def test_singleFileImport2Json(self):
        print("Loading a single data point into json storage data base")
        db = gcdb.readFiles(singleFilePath_1, store = testdbString)
        with open(testdbString) as dbFile:
            # compare whether the loaded document matches the stored document
            self.assertEqual(gcdb.readFiles(singleFilePath_1).get(doc_id=1), json.load(dbFile)['_default']['1'])
            db.close()
            os.remove(testdbString)
            print("--> OK")

    def test_singleFileImportList(self):
        print("Loading a list of single files")
        db = gcdb.readFiles([singleFilePath_1, singleFilePath_2])
        # compare whether the loaded document matches the document in the data base
        self.assertEqual(gcdb.readFiles(singleFilePath_2).get(doc_id=1), db.get(doc_id=2))
        db.close() # not really needed as not writing to file
        print("--> OK")

    def test_singleFileImportOverwrite(self):
        print("Loading two data points into json storage data base with overwrite mode")
        db = gcdb.readFiles(singleFilePath_1, store = testdbString)
        db.close()
        db = gcdb.readFiles(singleFilePath_2, store = testdbString)

        # compare whether the loaded document matches the stored document
        self.assertTrue(len(db) == 1)
        self.assertEqual(db.get(doc_id=1), gcdb.readFiles(singleFilePath_2).get(doc_id=1))
        db.close()
        os.remove(testdbString)
        print("--> OK")

    def test_singleFileImportAppend(self):
        print("Loading two data points into json storage data base with append mode")
        db = gcdb.readFiles(singleFilePath_1, store = testdbString)
        db.close()
        db = gcdb.readFiles(singleFilePath_2, store = testdbString, mode = "append")

        # compare whether the loaded document matches the stored document
        self.assertTrue(len(db) == 2)
        self.assertEqual(db.get(doc_id=2), gcdb.readFiles(singleFilePath_2).get(doc_id=1))
        db.close()
        os.remove(testdbString)
        print("--> OK")

    def test_singleFileImportPassingDB(self):
        print("Loading a second data point into an existing data base")
        db = gcdb.readFiles(singleFilePath_1, store = testdbString)
        db = gcdb.readFiles(singleFilePath_2, db = db)

        # compare whether the loaded document matches the stored document
        self.assertTrue(len(db) == 2)
        self.assertEqual(db.get(doc_id=2), gcdb.readFiles(singleFilePath_2).get(doc_id=1))
        db.close()
        os.remove(testdbString)
        print("--> OK")            

if __name__ == '__main__':
    unittest.main()