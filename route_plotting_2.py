import os
from gpx_converter import Converter
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import LineString
import shapely.ops as so
from shapely.ops import unary_union

#  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
#  .venv\scripts\activate

GPX_DIRECTORY = 'Activities/Test Activities'

#%% Union of all routes

routes = []
routes_dilated = []

for gpx_file in os.listdir(GPX_DIRECTORY):
    df = Converter(input_file=os.path.join(GPX_DIRECTORY, gpx_file)).gpx_to_dataframe()
    longitude_latitude_tuples = [tuple(x) for x in df[["longitude", "latitude"]].values]

    line = LineString(longitude_latitude_tuples)
    dilated = line.buffer(0.0001)

    routes.append(line)
    routes_dilated.append(dilated)
#%%

route_unions = unary_union(routes_dilated)
if route_unions.type == 'MultiPolygon':
    for geom in route_unions.geoms:
        xo, yo = geom.exterior.xy
        plt.plot(xo, yo, "b")
        for interior in geom.interiors:
            xi,yi = interior.xy
            plt.plot(xi, yi, "b")
else: 
    xo, yo = route_unions.exterior.xy
    plt.plot(xo, yo, "b")
    for interior in route_unions.interiors:
        xi,yi = interior.xy
        plt.plot(xi, yi, "b")

plt.show()

# Next step is to install and use the package 'centerlines'. Issue is that I am having trouble installing it, the site where I can get the whl file from for gdal is timing out. 
# Same site I got shapely from, so it should be working... Just not at the moment. 
# https://www.lfd.uci.edu/~gohlke/pythonlibs/#gdal 
# I need version cp310 win64. 
# https://stackoverflow.com/questions/43587960/gdal-installation-error-using-pip
# https://gis.stackexchange.com/questions/210586/attempting-to-install-pip-package-produces-gdalversion-is-not-defined-error




# Next step... Find areas of the union that are only in one polygon.
# trace the line that is on the borders of those and the rest?

# Or... trace the lines and then also trace the midlines within a certain tolerance?
# then use normals to the midlines to bisect the regions?

# probably realistically the next step is to go back to test regions for now, 
# plot them all with some alpha along with the routes. See what sort of operations
# need to be done. 

# Or hey what if I just took the entire polygon and made cells within it and then
# tailor the cell size so that it captures common routes but also separates nearby
# but parallel ones... and then count how many lines pass through each cell?

# https://stackoverflow.com/questions/25656120/how-to-check-if-two-gps-routes-are-equals
# https://stackoverflow.com/questions/68348779/given-a-polygon-line-in-it-find-position-on-line-where-to-split-the-polygon-w
# 