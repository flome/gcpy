# import gcpy module
import gcpy

# load the current working directory
path2data = '.'
measurement_db = gcpy.gcdb.readDir(path2data)

# compute glow curve parameters
measurement_db.update(gcpy.gcana.calcGCparams('time_sec', 'PhCount'))

# perform temperature reconstruction with 3 peaks
measurement_db.update(gcpy.gcana.calcTreco('time_sec', 'PhCount', peaks=3))

# perform glow curve deconvolution fit
measurement_db.update(gcpy.gcana.gcFit('time_sec', 'PhCount'))

# plot all curves and save them
import matplotlib.pyplot as plt
for measurement in measurement_db:
  plt.plot(measurement['time_sec'], measurement['PhCount'], label='Measurement')
  plt.xlabel('$t$ in s')
  plt.ylabel('$N$ in $\\mathrm{\\frac{1}{5\\,ms}}$')
  plt.legend(loc='upper right')
  plt.savefig('gc_plot_file_%s.pdf'%measurement['filename']) 
  # this saves each plot with its individual filename
  plt.clf()
  
# delete arrays from data base and save as table
measurement_db.update(gcana.strip_arrays)
import pandas as pd
measurements_dataframe = pd.DataFrame(measurement_db.all())
measurements_dataframe.to_excel('Results.xls')
