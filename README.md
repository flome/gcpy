
# gcpy
University project: glow curve analysis software for exponential heating.
For questions and support please contact the maintainer Florian Mentzel (florian.mentzel@tu-dortmund.de).

## Compatibility
Attention: Tested with Ubuntu 16.04 and CentOS7, might fail on other platforms, especially fails probably with Windows.

## Install

You can download this repository and install it using
```
git clone https://github.com/flome/gcpy
pip install gcpy
```

If you use a python installation that is hosted by an administrator and not by you, you can install the package locally just for our user account:
```
pip install --user gcpy
```

You can use gcpy in your project by importing it with
```
import gcpy
```

### Editable installation - contributing

If you want to edit the gcpy source code, install it with 
```
pip install -e .
```
which will keep the files locally and changes on the source will be active immediately. 
If you want to contribute, please contact one of the current contributors.

## Usage

Simple examples to get started are provided in the ```examples``` folder.

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

You can access a list of all documents (measurements) with
```
list_of_measurements = measurement_db.all()
```
which you can use to create e.g. a pandas DataFrame
```
import pandas as pd
measurements_dataframe = pd.DataFrame(list_of_all_meas)
```
to perform further analysis tasks.


### Glow curve analysis

There are predefined functions to compute glow curve parameters like the netto photon counts
```
measurement_db.update(gcpy.gcana.calcGCparams('time_sec', 'PhCount'))
```
to perform the temperature reconstruction (please note that you need to specify the number of peaks here!)
```
measurement_db.update(gcpy.gcana.calcTreco('time_sec', 'PhCount', peaks=3))
```
and the glow curve deconvolution (note the difference in the x-Axis!)
```
measurement_db.update(gcpy.gcana.gcFit('Treco_T', 'PhCount'))
```
They update the documents within the database automatically.

### Glow curve plots and data analysis (e.g. in pandas)

You can create and save glow curve plots:
```
import matplotlib.pyplot as plt
for measurement in measurement_db:
  plt.plot(measurement['time_sec'], measurement['PhCount'], label='Measurement')
  plt.xlabel('$t$ in s')
  plt.ylabel('$N$ in $\\mathrm{\\frac{1}{5\\,ms}}$)
  plt.legend(loc='upper right')
  plt.savefig('gc_plot_file_%s.pdf'%measurement['filename']) 
  # this saves each plot with its individual filename
  plt.clf()
```


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
measurement_db = gcpy.gcdb.newDB()
measurement_db.insert_multiple(gcpy.gcdb.prototypeIItoJson(dirPath))
```
From here you can continue as described above.

