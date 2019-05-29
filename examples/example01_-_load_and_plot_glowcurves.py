# import gcpy module
import gcpy

# load the current working directory
path2data = '.'
measurement_db = gcpy.gcdb.readDir(path2data)

# path where to put results
output_path = "output_-_example01"

# plot all curves and save them
import matplotlib.pyplot as plt
for measurement in measurement_db:
  plt.plot(measurement['time_sec'], measurement['PhCount'], label='Measurement')
  plt.xlabel('$t$ in s')
  plt.ylabel('$N$ in $\\mathrm{\\frac{1}{5\\,ms}}$')
  plt.legend(loc='upper right')
  plt.savefig(output_path+'/%s.pdf'%measurement['filename'][:-5]) # [:-5] --> do not use the .json ending in filename 
  # this saves each plot with its individual ID
  plt.clf()

## next, we save the data from the measurements, but we do not want to export the arrays to save memory
measurement_db.update(gcpy.gcana.stripArrays)
import pandas as pd
measurements_dataframe = pd.DataFrame(measurement_db.all())
measurements_dataframe.to_excel(output_path+'/measurement_data.xls')

print("Done... The results have been written to:", output_path)