### import depdencencies

# json handling
import json
# os operations like file lists
import os
# tiny db content for data storage
from tinydb import TinyDB
from tinydb.storages import MemoryStorage 


## internal function to get a data base
def _getDB(dbStorageString = None, mode="overwrite"):
    # if no storage string is passed, save in memory
    if dbStorageString:
        if not os.path.dirname(dbStorageString):
            dbStorageString = os.path.join(".", dbStorageString)
        # check for write permissions in target dir
        if os.access(os.path.dirname(dbStorageString), os.W_OK):
            db = TinyDB(dbStorageString)
            if os.path.isfile(dbStorageString) and mode is "overwrite":
                db.purge()
            return db

        else:
            raise OSError("Cannot access specified storage location")
    else:
        return TinyDB(storage=MemoryStorage)


def loadFile(file2load, dbStorageString = None, mode="overwrite"):

    db = _getDB(dbStorageString, mode)
    with open(file2load, 'r') as file:
        data2import = json.load(file)
        db.insert(data2import)
    return db

def loadDirectory(dir2load, dbStorageString = None):
    pass

def importDB(db2open, dbStorageString = None):
    pass

def dumpDB(path2save):
    pass


if __name__ == "__main__":
  print("This is a module for handling glow curve analysis with python.")
  exit