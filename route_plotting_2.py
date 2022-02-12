import os
from gpx_converter import Converter
import matplotlib.pyplot as plt
import numpy as np
# import shapely.geometry 
from shapely.geometry import LineString, Polygon, MultiLineString
import shapely.ops as so
from shapely.ops import snap
from shapely.ops import unary_union
from shapely import geometry, ops
from centerline.geometry import Centerline

#  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
#  .venv\scripts\activate

GPX_DIRECTORY = 'Activities/Test Activities'
OFFSET_DISTANCE = 0.0001 # this has to be calculated based on the canvas size and minimum nozzle. want each line to be at least 2 nozzle widths wide. 
INTERPOLATION_DISTANCE = OFFSET_DISTANCE * 2/3

routes = []
routes_dilated = []
routes_eroded = []

for gpx_file in os.listdir(GPX_DIRECTORY):
    df = Converter(input_file=os.path.join(GPX_DIRECTORY, gpx_file)).gpx_to_dataframe()
    longitude_latitude_tuples = [tuple(x) for x in df[["longitude", "latitude"]].values]

    line = LineString(longitude_latitude_tuples)
    xl, yl = line.xy
    plt.plot(xl, yl, 'gray')

    dilated = line.buffer(OFFSET_DISTANCE)

    routes.append(line)
    routes_dilated.append(dilated)

route_unions_dilated = unary_union(routes_dilated)
route_unions_eroded = route_unions_dilated.buffer(-0.75*OFFSET_DISTANCE)

if route_unions_dilated.type == 'MultiPolygon':
    for geom in route_unions_dilated.geoms:
        xo, yo = geom.exterior.xy
        # plt.plot(xo, yo, "cornflowerblue")
        for interior in geom.interiors:
            xi,yi = interior.xy
            plt.plot(xi, yi, "cornflowerblue")
else:
    xo, yo = route_unions_dilated.exterior.xy
    plt.fill(xo, yo, "cornflowerblue")

    xo, yo = route_unions_eroded.exterior.xy
    plt.fill(xo, yo, "white")

    for interior in route_unions_eroded.interiors:
        xi,yi = interior.xy
        plt.fill(xi, yi, "cornflowerblue")

    for interior in route_unions_dilated.interiors:
        xi,yi = interior.xy
        plt.fill(xi, yi, "white")

    centerline = Centerline(route_unions_eroded, interpolation_distance=INTERPOLATION_DISTANCE)

    # for cl_segment in list(centerline.geoms):
    #     xs, ys = cl_segment.xy
    #     plt.plot(xs, ys, linewidth=5) # make it thicker too

    # this didn't work very well at all. 
    # result = snap(routes[0], centerline, OFFSET_DISTANCE)
    # xi, yi = result.xy
    # plt.plot(xi, yi, 'lime')

    merged_centerline = ops.linemerge(centerline)
    for ml_segment in list(merged_centerline.geoms):
        xl, yl = ml_segment.xy
        plt.plot(xl, yl, linewidth=5)

    

plt.show()


# What I have now is a bunch of 'branches' that are their own linestrings. 
# I think the next point is to gather a list of all coordinates in all the 
# linestrings and determine which ones are a member of more than one. 
# Those are the intersection points. 

# From those intersection points, determine the 'closest' coordinate points on the boundary layer
# by looking radially. (find diff btwn point, vector, look for min)

# get the coordinates. for the first 'intersection', plot the difference vector.








# below this is shitballing and ideas. 



# Next step is to use the package 'centerlines'. 
# then use normals to the midlines to bisect the regions?

# Or hey what if I just took the entire polygon and made cells within it and then
# tailor the cell size so that it captures common routes but also separates nearby
# but parallel ones... and then count how many lines pass through each cell?

# https://stackoverflow.com/questions/25656120/how-to-check-if-two-gps-routes-are-equals
# https://stackoverflow.com/questions/68348779/given-a-polygon-line-in-it-find-position-on-line-where-to-split-the-polygon-w


# count overlapping polygon regions? 
# https://stackoverflow.com/questions/66341143/count-overlapping-features-using-geopandas

# separate different 'streets'
# https://gis.stackexchange.com/questions/98087/split-lines-at-intersection-of-other-lines
# this is what i WANT https://community.esri.com/t5/python-questions/split-road-edge-polygon-at-intersections/td-p/20031

# what if... I count overlapping polygon regions and then work incrementally. first find regions where overlapping count == 1. 
# but make sure it's not picking out little slivers. Must have a "width" approximately twice the offset distance... 

# i guess a few options are to use shapely snapping or shapely shared paths or shapely split. 
# All 3 are located around https://shapely.readthedocs.io/en/stable/manual.html#shapely.ops.snap


# https://www.youtube.com/watch?v=t6gGrv3vRoM 

