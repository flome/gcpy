# gcpy
University project: glow curve analysis software for exponential heating

## Install

You can download this repository and install it using
```
git clone https://github.com/flome/gcpy
cd gcpy
pip install .
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

To append new data to an existing data base, you can pass the object in the form
data = gcpy.gcdb.readDir('second_dir', db = data)

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
db.update(Treco('time_sec', 'PhCount', peaks=3))
```

Glow curve deconvolution

```
db.update(gcFit('time_sec', 'PhCount'))
```
