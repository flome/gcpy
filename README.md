
# gcpy
University project: glow curve analysis software for exponential heating.
For questions and support please contact the maintainer Florian Mentzel (florian.mentzel@tu-dortmund.de).

## Compatibility
Attention: Tested with Ubuntu 16.04 and CentOS7, might fail on other platforms, especially fails probably with Windows.

## Install

You can download this repository and install it using
```
git clone https://github.com/flome/gcpy
cd gcpy
pip install .
```
You can use gcpy in your project by importing it with
```
import gcpy
```

## Usage

### Load data
To load data from a directory, you can call 

```
path2data = PUT_YOUR_DIRECTORY_PATH_HERE
measurement_db = gcpy.gcdb.readDir(path2data)
```
To append new data to an existing data base, you can pass the object in the form
```
measurement_db = gcpy.gcdb.readDir('ANOTHER_DIRECTORY_YOU_WANT_TO_IMPORT', db = measurement_db)
```

### Glow curve analysis

There are predefined functions to compute glow curve parameters like the netto photon counts
```
db.update(gcpy.gcana.calcGCparams('time_sec', 'PhCount'))
```
to perform the temperature reconstruction (please note that you need to specify the number of peaks here!)
```
db.update(gcpy.gcana.calcTreco('time_sec', 'PhCount', peaks=3))
```
and the glow curve deconvolution
```
db.update(gcpy.gcana.gcFit('time_sec', 'PhCount'))
```
They update the documents within the database automatically.


### Analysis in pandas

You can access a list of all documents (measurements) with
```
list_of_all_meas = db.all()
```
You can use this to create e.g. a pandas DataFrame
```
import pandas as pd
df = pd.DataFrame(list_of_all_meas)
```
to perform further analysis tasks.


## Legacy support

In version 0.1.1, TXT files from the Prototype II can be converted to json. The Prototype II is data in the format
```
KEY VALUE
KEY VALUE
[BEGIN TABLENAME]
table content
[END TABLENAME]
```
or
```
KEY=VALUE
KEY=VALUE
[BEGIN TABLENAME]
table content
[END TABLENAME]
```
If a line does not contain a key-value pair but only one value, it will be named ```UNKNOWN_i``` where ```i``` is a increasing index for values without label. You may replace them later on in your analysis.
To import a folder containing measurements in legacy format, you can call 
```
db = gcpy.gcdb.newDB()
db.insert_multiple(gcdb.prototypeIItoJson(dirPath))
```
From here you can continue as described above.

