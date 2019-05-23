# gcpy
University project: glow curve analysis software for exponential heating.
For questions and support please contact the maintainer Florian Mentzel (florian.mentzel@tu-dortmund.de).

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

## Load data

To load data, you can call either
```
data = gcpy.gcdb.readFiles([list_of_files])
```

or

```
data = gcpy.gcdb.readDir('path_to_dir')
```
This returns a [TinyDB](https://tinydb.readthedocs.io/en/latest/) database instance. Refer to their documentation for information about the usage.
To access the list of entries, simply call

```
list_of_docs = data.all()
```
which returns a list containing the data points in the form of python dictionaries. For analysis, you can either use those or transform it to a [pandas DataFrame](https://pandas.pydata.org/) by calling
```
import pandas as pd
df = pd.DataFrame(list_of_docs)
```

To append new data to an existing data base, you can pass the object in the form
```
data = gcpy.gcdb.readDir('second_dir', db = data)
```

## Glow curve analysis

Functions and operations can be applied to the data base using either
```
data.update(callable)
```
or
```
gcpy.gcana.update(database, callable, njobs)
```
for parallel processing.

Predefined functions can be called with the string names of the x- and y- axis for the analysis
Some may require additional parameters like the number of peaks.
Computation of basic GC parameters: 

```
db.update(calcGCparams('time_sec', 'PhCount'))
```

Temperature reconstruction

```
db.update(calcTreco('time_sec', 'PhCount', peaks=3))
```

Glow curve deconvolution

```
db.update(gcFit('time_sec', 'PhCount'))
```

You can also directly use the analysis functions on a document in the form of a dictionary using
```
doc_new_entries = calcGCparams(doc['X_axis'], doc['Y_axis'])
doc.update(doc_new_entries)
```
