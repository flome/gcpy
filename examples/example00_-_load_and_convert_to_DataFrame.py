# import gcpy module
import gcpy

# load the current working directory
path2data = '.'
measurement_db = gcpy.gcdb.readDir(path2data)

## for further analysis, you might want to use pandas and DataFrames 
import pandas as pd
measurements_dataframe = pd.DataFrame(measurement_db.all())

## inspect the new DataFrame
print('--------------------------------')
print('First entries:')
print('--------------------------------')

print(measurements_dataframe.head())

print('--------------------------------')
print('Stats of the columns:')
print('--------------------------------')

print(measurements_dataframe.describe())

print('\n\n --> you may want to re-write this example as jupyter notebook to have a better overview of your data\n')