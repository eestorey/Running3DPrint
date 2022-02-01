import os
from gpx_converter import Converter
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import LineString
import shapely.ops as so
from shapely.ops import unary_union


#%% Union of all routes

routes = []
routes_dilated = []

for gpx_file in os.listdir('Activities/Activities Checked Renamed'):
    df = Converter(input_file=os.path.join('Activities/Activities Checked Renamed', gpx_file)).gpx_to_dataframe()
    longitude_latitude_tuples = [tuple(x) for x in df[["longitude", "latitude"]].values]

    line = LineString(longitude_latitude_tuples)
    dilated = line.buffer(0.0001)

    routes.append(line)
    routes_dilated.append(dilated)

route_unions = unary_union(routes_dilated)
for geom in route_unions.geoms:
    xo, yo = geom.exterior.xy
    plt.fill(xo, yo, "b")
    for interior in geom.interiors:
        xi,yi = interior.xy
        plt.fill(xi, yi, "w")

plt.show()