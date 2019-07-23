"""
    GCpy module to handle glow curve data.
    Author: Florian Mentzel (florian.mentzel@tu-dortmund.de)
    Creation: 2019/05/05
"""

### import depdencencies
# unit tests
import unittest

# json handling
import ujson as json

# os operations like file lists
import os

# tiny db content for data storage
from tinydb import TinyDB
from tinydb.storages import MemoryStorage

# compression tools for saving disk space
import pickle, gzip, bz2

# import for prototypeII support
import pandas as pd
import io

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


def loadReaderDBs(path):
    """
    Function to import current database format from json files to a dictionary
    
    Parameters
    ---------
    path
        Directory of the database json files

    Returns
    ---------
    database
        combined dictionary containing sub-dicts with the databases

    """
    files = os.listdir(path)
    database = {}
    for file in files:
        with open(os.path.join(path, file)) as sourcefile:
            data = json.load(sourcefile)
            name = file.split("_")[1].split(".")[0]
            database[name] = data
            print("imported db: %s"%name)
    return database



def prototypeIItoJson(files2import, delimiter="="):
    """
    Convenience function to convert data from old Prototype II TXT format to json.
    
    Parameters
    ---------
    files2import
        Directory, filename or list of files to import. Must end on 'TXT' or 'txt' to be imported

    Returns
    ---------
    docs
        list of json documents (python dictionaries) derived from the imported file(s)

    """

    docs = []
    if isinstance(files2import, list):
        for file in files2import:
            if file.endswith(".TXT") or file.endswith(".txt"):
                docs.append(_prototypeIItoJson(file, delimiter))
    elif os.path.isdir(files2import):
        for dirs, subdirs, files in os.walk(files2import):
            for file in files:
                if file.endswith(".TXT") or file.endswith(".txt"):
                    docs.append(_prototypeIItoJson(os.path.join(dirs, file), delimiter))
    elif os.path.isfile(files2import):
        docs.append(_prototypeIItoJson(files2import, delimiter))
    return docs

def _prototypeIItoJson(file, delimiter="="):
    """
    Internal helper function for prototypeIItoJson
    """
    doc = {'filename': os.path.basename(file), 'filedir': os.path.dirname(file)}
    unknown = 0

    with open(file, encoding='iso-8859-1') as fileStream:
        while(True):
            line = fileStream.readline()
            if line == "":
                break 

            if "[" in line and "]" in line and "BEGIN" in line:
                tableTitle = line[line.find('BEGIN')+len("BEGIN"):line.rfind(']')].strip()

                tableContent = ""
                while(True):
                    line = fileStream.readline()
                    if "[" in line and "]" in line and "END "+tableTitle in line:
                        break
                    
                    tableContent += line.replace(',', '.')
                
                if "INFO" in tableTitle:
                    for contentLine in tableContent.split('\n'):
                        itemTitle = contentLine[0:contentLine.find(delimiter)].strip()
                        itemContent = contentLine[contentLine.find(delimiter)+1:].strip()
                        doc[itemTitle] = itemContent
                else:
                    tableContent = pd.read_csv(io.StringIO(tableContent), delimiter="\t")
                    for key in tableContent:
                        
                        try:
                            doc[key] = [x.item() for x in tableContent[key].values]
                        except:
                            doc[key] = [x for x in tableContent[key].values]
                    
            elif delimiter in line:
                itemTitle = line[0:line.find(delimiter)+1].strip()
                itemContent = line[line.find(delimiter)+1:].strip()
                doc[itemTitle] = itemContent

            else:
                doc["UNKNOWN_%s"%unknown] = line.strip()
                unknown += 1

    return doc


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

    data2import = []
    for i, file2load in enumerate(files2load):
        with open(file2load, 'r') as ioWrapper2import:
            
            data2import.append({'filename': os.path.basename(file2load), 'filedir': os.path.dirname(file2load)})
            data2import[-1].update(json.load(ioWrapper2import))
    
    db.insert_multiple(data2import)
    return db

def readDir(dir2load, asDataFrame=False, depth = None, db = None, store = None, mode="overwrite"):
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
    asDataFrame
        If True, returns pandas DataFrame from database
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

    if not os.path.isdir(dir2load):
        raise AttributeError("Directory is not accessible. Maybe incorrect name?")
    if db is None:
        db = newDB(store, mode)
    level = 0

    files_found = 0
    files2import = []
    for root, dirs, files in os.walk(dir2load):
        files2import.extend([os.path.join(root, file) for file in files if file.endswith('.json')])
        files_found += len(files2import)
        level += 1
        if level == depth:
            del dirs[:]
    readFiles(files2import, db = db)

    print(">> Imported %s glow curve files."%files_found)
    if asDataFrame:
        return pd.DataFrame(db.all())
    else:
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

    print("This module can be used for glow curve data handling.")
    
