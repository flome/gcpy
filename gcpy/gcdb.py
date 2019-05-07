"""
    GCpy module to handle glow curve data.
    Author: Florian Mentzel (florian.mentzel@tu-dortmund.de)
    Creation: 2019/05/05
"""

### import depdencencies
# unit tests
import unittest

# json handling
import json

# os operations like file lists
import os

# tiny db content for data storage
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

# compression tools for saving disk space
import pickle, gzip, bz2, sys, resource

def newDB(store = None, mode="overwrite"):
    """
    Internal function that handles the creation of a TinyDB instance for gc data handling.
    
    Parameters
    ---------
    store
        Either string or None (default). If string, sets the file used for TinyDB file storage. If None, the data base is run in-memory.
    mode
        "append" or "overwrite"(default). If a file storage is set, this flag can be used to either append to the existing file store or to whipe it before adding new data (overwrite).

    Returns
    ---------
    db
        TinyDB instance

    """

    # if no storage string is passed, save in memory
    if store:
        # to check for writing permissions, a parent directory needs to be available
        # if none is, assume local file in current working directory
        if not os.path.dirname(store):
            store = os.path.join(".", store)

        # check for write permissions in target dir
        if os.access(os.path.dirname(store), os.W_OK):
            # get a new TinyDB instance with the target file as file storage
            db = TinyDB(store)

            # in overwrite mode, delete all data points in data base
            if os.path.isfile(store) and mode is "overwrite":
                db.purge()
            return db

        else:
            raise OSError("Cannot access specified storage location")
    else:
        # if no store is passed, use the in-memory version
        return TinyDB(storage=MemoryStorage)

def readFiles(files2load, db = None, store = None, mode="overwrite"):
    """
    Function to import single measurement files or a list of measurements.
    
    Parameters
    ---------
    files2load
        Either string or list. Imports the given measurement files.
    db
        TinyDB instance or None (default). If a db instance is passed, the new entries are added to it. If db is None, a new instance is created using the 'store' and 'mode' parameters. 
    store
        Either string or None (default). Only used if db is None. If string, sets the file used for TinyDB file storage. If None, the data base is run in-memory.
    mode
        "append" or "overwrite"(default). Only used if db is None. If a file storage is set, this flag can be used to either append to the existing file store or to whipe it before adding new data (overwrite).

    Returns
    ---------
    db
        TinyDB instance containing the loaded files
    """

    # get a fresh tinydb instance and insert the jsonified file
    if db is None:
        db = newDB(store, mode)
    if not isinstance(files2load, list):
        files2load = [files2load]

    for file2load in files2load:
        with open(file2load, 'r') as ioWrapper2import:
            data2import = json.load(ioWrapper2import)
            data2import.update({'filename': file2load})
            db.insert(data2import)
    return db

def readDir(dir2load, depth = None, db = None, store = None, mode="overwrite"):
    """
    Function to import a directory of measurements.

    Example
    ---------
    Simple directory import into memory
        >>> from gcpy import gcdb
        >>> db = gcdb.readDir('./pathToDir')

    Simple appending to an existing data base
        >>> gcdb.readDir('./pathToDir', db = existingDB)
    
    Parameters
    ---------
    dir2load
        String that contains the path to the directory to be imported.
    depth
        Either integer or None (default). If specified as integer, it can be used to limit the depth of subdirectories which are imported. None corresponds to 'import all levels', 1 corresponds to 'import root directory only'
    db
        TinyDB instance or None (default). If a db instance is passed, the new entries are added to it. If db is None, a new instance is created using the 'store' and 'mode' parameters. 
    store
        Either string or None (default). Only used if db is None. If string, sets the file used for TinyDB file storage. If None, the data base is run in-memory.
    mode
        "append" or "overwrite"(default). Only used if db is None. If a file storage is set, this flag can be used to either append to the existing file store or to whipe it before adding new data (overwrite).

    Returns
    ---------
    db
        TinyDB instance containing the loaded files
    """
    if db is None:
        db = newDB(store, mode)
    level = 0
    for root, dirs, files in os.walk(dir2load):
        readFiles([os.path.join(root, file) for file in files if file.endswith('.json')], db = db)
        level += 1
        if level == depth:
            del dirs[:]
    return db


def load(db2open):
    """
    Load a stored glow curve data base
    
    Parameters
    ---------
    db2open
        Path to the data base file
    
    Returns
    ---------
    db
        TinyDB instance

    """
    if db2open.endswith(".json"):
        return newDB(db2open, mode="append")
    else:
        with bz2.BZ2File(db2open) as file2load:
            db_data = pickle.load(file2load)
            db = newDB()
            db.storage.memory = db_data
        return db

def store(db, path2save, compress=True):
    """
    Store a TinyDB instance. Can be compressed to save disk memory.
    
    Parameters
    ---------
    db
        TinyDB instance to be stored
    path2save
        Path (string) where to save the content of the data base. Use .json extension for plain text saving and any extension for compressed saving
    compress
        Boolean (default: True). If True, the data is saved in a compressed form. Reduces the disk usage significantly
    
    Returns
    ---------
    db
        TinyDB instance

    """
    if compress:
        # get the dict from the memory
        data2dump = db._storage.memory
        # open a bzip2 file with highest (default) compression rate
        with bz2.BZ2File(path2save, 'wb') as file2write:
            # use pickle to serialize and save a little more space
            pickle.dump(data2dump, file2write, protocol=pickle.HIGHEST_PROTOCOL)

    else:
        if not path2save.endswith(".json"):
            path2save+=".json"
        # simply store the string from memory
        with open(path2save, "w") as file2write:
            file2write.write(json.dumps(db.storage.memory))
    

if __name__ == "__main__":

    print("The execution of the module itself is designed to run the tests:")
    singleFilePath_1 = './gcpy.test/test_data/single_files/20190319_162420_7.json'
    singleFilePath_2 = './gcpy.test/test_data/single_files/20190319_162444_8.json'
    testdirPath = './gcpy.test/test_data/test_nested_dir'
    testdbString = 'test_db.json'
    testStorageString = "test_storage"

    class GCDBTest(unittest.TestCase):  

        def test_store_open(self):
            print("Test storage and opening of data base")
            db = readDir(testdirPath, depth=3)
            store(db, testStorageString)
            newDB = load(testStorageString)
            self.assertEqual(db.all(), newDB.all())
            os.remove(testStorageString)
            print("--> OK")    

        def test_dirImport(self):
            print("Test import of a nested directory with varying depth")
            db = readDir(testdirPath, depth=1)
            self.assertEqual(len(db), 1)
            db = readDir(testdirPath, depth=2)
            self.assertEqual(len(db), 5)
            db = readDir(testdirPath, depth=3)
            self.assertEqual(len(db), 6)
            print("--> OK")

        def test_singleFileImport2Memory(self):
            print("Loading a single data point into memory data base")
            # load the specified file using the function
            db = readFiles(singleFilePath_1)
            # compare whether it actually maches the imported file as json structure
            with open(singleFilePath_1) as testFile:
                data2compare = json.load(testFile)
                data2compare.update({'filename': singleFilePath_1})
                self.assertEqual(db.get(doc_id=1), data2compare)
                print("--> OK")

        def test_singleFileImport2Json(self):
            print("Loading a single data point into json storage data base")
            db = readFiles(singleFilePath_1, store = testdbString)
            with open(testdbString) as dbFile:
                # compare whether the loaded document matches the stored document
                self.assertEqual(readFiles(singleFilePath_1).get(doc_id=1), json.load(dbFile)['_default']['1'])
                db.close()
                os.remove(testdbString)
                print("--> OK")

        def test_singleFileImportList(self):
            print("Loading a list of single files")
            db = readFiles([singleFilePath_1, singleFilePath_2])
            # compare whether the loaded document matches the document in the data base
            self.assertEqual(readFiles(singleFilePath_2).get(doc_id=1), db.get(doc_id=2))
            db.close() # not really needed as not writing to file
            print("--> OK")

        def test_singleFileImportOverwrite(self):
            print("Loading two data points into json storage data base with overwrite mode")
            db = readFiles(singleFilePath_1, store = testdbString)
            db.close()
            db = readFiles(singleFilePath_2, store = testdbString)

            with open(testdbString) as dbFile:
                # compare whether the loaded document matches the stored document
                self.assertTrue(len(db) == 1)
                self.assertEqual(db.get(doc_id=1), readFiles(singleFilePath_2).get(doc_id=1))
                db.close()
                os.remove(testdbString)
                print("--> OK")

        def test_singleFileImportAppend(self):
            print("Loading two data points into json storage data base with append mode")
            db = readFiles(singleFilePath_1, store = testdbString)
            db.close()
            db = readFiles(singleFilePath_2, store = testdbString, mode = "append")

            with open(testdbString) as dbFile:
                # compare whether the loaded document matches the stored document
                self.assertTrue(len(db) == 2)
                self.assertEqual(db.get(doc_id=2), readFiles(singleFilePath_2).get(doc_id=1))
                db.close()
                os.remove(testdbString)
                print("--> OK")

        def test_singleFileImportPassingDB(self):
            print("Loading a second data point into an existing data base")
            db = readFiles(singleFilePath_1, store = testdbString)
            db = readFiles(singleFilePath_2, db = db)

            with open(testdbString) as dbFile:
                # compare whether the loaded document matches the stored document
                self.assertTrue(len(db) == 2)
                self.assertEqual(db.get(doc_id=2), readFiles(singleFilePath_2).get(doc_id=1))
                db.close()
                os.remove(testdbString)
                print("--> OK")            
    
    unittest.main()