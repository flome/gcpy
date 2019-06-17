# import gcpy module
import gcpy

# we need numpy for array transformations to display the background
import numpy as np

# load the current working directory
path2data = '.'
measurement_db = gcpy.gcdb.readDir(path2data)

# compute glow curve parameters
measurement_db.update(gcpy.gcana.calcGCparams('time_sec', 'PhCount'))

# path where to put results
output_path = "output_-_example03"

# plot all curves and save them
import matplotlib.pyplot as plt
for measurement in measurement_db:

  gcpy.gcplot.setPlotStyle("print")
  fig = gcpy.gcplot.getStyledFigure()

  plt.plot(measurement['time_sec'], measurement['PhCount'], label='Measurement')

  ## include region of interest
  plt.axvline(measurement['gc_timeRoI_low'], linestyle=':', color='red', label='RoI')
  plt.axvline(measurement['gc_timeRoI_high'], linestyle=':', color='red')

  ## plot background
  counts_below_RoI = np.array(measurement['PhCount'])[measurement['time_sec'] < measurement['gc_timeRoI_low']]
  mean_counts_below_RoI = counts_below_RoI.mean()
  counts_above_RoI = np.array(measurement['PhCount'])[measurement['time_sec'] > measurement['gc_timeRoI_high']]
  mean_counts_above_RoI = counts_above_RoI.mean()

  ## straight line at mean counts below RoI
  plt.plot([0, measurement['gc_timeRoI_low']], [mean_counts_below_RoI, mean_counts_below_RoI], 'k--', label='bg')
  ## straight line at the mean counts above RoI
  plt.plot([measurement['gc_timeRoI_low'], measurement['gc_timeRoI_high']], [mean_counts_below_RoI, mean_counts_above_RoI], 'k--')
  # connect both lines
  plt.plot([measurement['gc_timeRoI_high'], measurement['time_sec'][-1]], [mean_counts_above_RoI, mean_counts_above_RoI], 'k--')

  plt.xlabel('$t$ in s')
  plt.ylabel('$N$ in $\\mathrm{\\frac{1}{5\\,ms}}$')
  plt.legend(loc='upper right', framealpha=0.9) # --> make legend background less see-through

  plt.grid()
  plt.savefig(output_path+'/%s.pdf'%measurement['filename'][:-5]) # [:-5] --> do not use the .json ending in filename 
  # this saves each plot with its individual ID
  plt.clf()
  
## next, we save the data from the measurements, but we do not want to export the arrays to save memory
measurement_db.update(gcpy.gcana.stripArrays)
import pandas as pd
measurements_dataframe = pd.DataFrame(measurement_db.all())
measurements_dataframe.to_excel(output_path+'/measurement_data.xls')

print("Done... The results have been written to:", output_path)