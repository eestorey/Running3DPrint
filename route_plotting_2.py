import os
from gpx_converter import Converter
import matplotlib.pyplot as plt
import numpy as np
# import shapely.geometry 
from shapely.geometry import LineString, Polygon, MultiLineString
import shapely.ops as so
from shapely.ops import unary_union
from centerline.geometry import Centerline

#  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
#  .venv\scripts\activate

GPX_DIRECTORY = 'Activities/Test Activities'

routes = []
routes_dilated = []

for gpx_file in os.listdir(GPX_DIRECTORY):
    df = Converter(input_file=os.path.join(GPX_DIRECTORY, gpx_file)).gpx_to_dataframe()
    longitude_latitude_tuples = [tuple(x) for x in df[["longitude", "latitude"]].values]

    line = LineString(longitude_latitude_tuples)
    dilated = line.buffer(0.0001)

    routes.append(line)
    routes_dilated.append(dilated)

route_unions = unary_union(routes_dilated)
if route_unions.type == 'MultiPolygon':
    for geom in route_unions.geoms:
        xo, yo = geom.exterior.xy
        plt.plot(xo, yo, "cornflowerblue")
        for interior in geom.interiors:
            xi,yi = interior.xy
            plt.plot(xi, yi, "cornflowerblue")
else:
    xo, yo = route_unions.exterior.xy
    plt.plot(xo, yo, "cornflowerblue")
    for interior in route_unions.interiors:
        xi,yi = interior.xy
        plt.plot(xi, yi, "cornflowerblue")

    centerline = Centerline(route_unions, interpolation_distance=0.00007)
    for cl_segment in list(centerline.geoms):
        xs, ys = cl_segment.xy
        plt.plot(xs, ys, 'r')

plt.show()

# Next step is to use the package 'centerlines'. 
# then use normals to the midlines to bisect the regions?

# Or hey what if I just took the entire polygon and made cells within it and then
# tailor the cell size so that it captures common routes but also separates nearby
# but parallel ones... and then count how many lines pass through each cell?

# https://stackoverflow.com/questions/25656120/how-to-check-if-two-gps-routes-are-equals
# https://stackoverflow.com/questions/68348779/given-a-polygon-line-in-it-find-position-on-line-where-to-split-the-polygon-w


# count overlapping polygon regions? 
# https://stackoverflow.com/questions/66341143/count-overlapping-features-using-geopandas