# import gcpy module
import gcpy

# we need numpy for array transformations to display the background
import numpy as np

# we will use pandas for the further analysis
import pandas as pd

# load the current working directory
path2data = '.'
measurement_db = gcpy.gcdb.readDir(path2data)

# path where to put results
output_path = "output_-_example04"

# convert to pandas DataFrame
measurement_df = pd.DataFrame(measurement_db.all())

# define analysis function
def analysis(data):
    # the data input here will be every single row of the DataFrame. 
    # It will be in the form of a pandas Series

    # first compute the parameters directly derived from the glow curve
    gc_params = gcpy.gcana.calcGCparams(data['time_sec'], data['PhCount'])   

    # next, the temperature reconstruction is performed. If you need to determine whether to use 3 or 4 peaks, this
    # could be done here using the data object 
    Treco_params = gcpy.gcana.calcTreco(data['time_sec'], data['PhCount'], peaks=3)

    # for the glow curve fit, you need to pass results from the temperature reconstruction as the fit is performed
    # in the temperature space
    gcFit_params = gcpy.gcana.gcFit(Treco_params['Treco_T'], Treco_params['Treco_PhCount'])
    
    # The parameters are in the form of dictionaries. Build series from them and append them to your row
    for params in [gc_params, Treco_params, gcFit_params]:
        data.append(pd.Series(params))

    # return the data entry
    return data

# apply the analysis to your data
measurement_df = measurement_df.apply(analysis, axis=1)

# export to excel or csv if needed, otherwise you can continue with your analysis
# drop arrays as they cannot be exported if too long
meas_df_stripped = measurement_df.apply(gcpy.gcana.stripArrays, axis=0)
measurement_df.to_excel(output_path+'/fit_results.xls')