import os
from gpx_converter import Converter
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import LineString


for gpx_file in os.listdir('test_files_for_plotting'):
    df = Converter(input_file=os.path.join('test_files_for_plotting', gpx_file)).gpx_to_dataframe()
    longitude_latitude_tuples = [tuple(x) for x in df[["longitude", "latitude"]].values]

    line = LineString(longitude_latitude_tuples)
    dilated = line.buffer(0.0001)
    xo,yo = dilated.exterior.xy
    plt.plot(xo, yo)

    for interior in dilated.interiors:
        xi,yi = interior.xy
        plt.plot(xi, yi)

plt.show()

# gpx_file = 'test.gpx'
# df = Converter(input_file=gpx_file).gpx_to_dataframe()
# longitude_latitude = df[["longitude", "latitude"]]
# longitude_latitude_tuples = [tuple(x) for x in longitude_latitude.values]

# line = LineString(longitude_latitude_tuples)
# dilated = line.buffer(0.00005)
# x,y = dilated.exterior.xy

# plt.plot(x, y)
# plt.show()
