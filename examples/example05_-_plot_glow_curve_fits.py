# import gcpy module
import gcpy

# we need numpy for array transformations to display the background
import numpy as np

# we will use pandas for the further analysis
import pandas as pd

# we will plot the transformed curve
import matplotlib.pyplot as plt

# load the current working directory
path2data = '.'
measurement_db = gcpy.gcdb.readDir(path2data)

# path where to put results
output_path = "output_-_example05"

# convert to pandas DataFrame
measurement_df = pd.DataFrame(measurement_db.all())

# define analysis function
def analysis(data):
    print("Processing curve %s/%s"%(data.name+1, len(measurement_df)))
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
    name = data.name
    data = pd.concat([pd.Series(x) for x in [data, gc_params, Treco_params, gcFit_params]])
    data.name = name

    # prepare the plot, first get a styled figure
    fig = gcpy.gcplot.getStyledFigure()

    plt.plot(data['gcfit_T'], data['gcfit_nPhotons'], '.', label='Measurement')
    plt.plot(data['gcfit_T'], data['gcfit_gcd'], 'k-', label='Glow curve fit')
    for peak in [2,3,4,5]:
        plt.plot(data['gcfit_T'], data['gcfit_gcd_peak%s'%peak], linestyle='--', label='Glow peaks' if peak == 2 else "__nolabel__")
    plt.plot(data['gcfit_T'], data['gcfit_gcd_bg'], 'k:', label='Background fit')

    plt.xlabel('$T$ in K')
    plt.ylabel('$N$ in $\\mathrm{\\frac{1}{2.5\\,K}}$')
    plt.legend(loc=2, bbox_to_anchor=(0.01, 0.92))
    plt.savefig(output_path+'/curve_%s.png'%data.name)

    # return the data entry
    return data

# set the "print" plot style
gcpy.gcplot.setPlotStyle('print')

# apply the analysis to your data
measurement_df = measurement_df.apply(analysis, axis=1)
