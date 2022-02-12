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
    x, y = line.xy
    plt.plot(x, y, 'gray')

    dilated = line.buffer(OFFSET_DISTANCE)

    routes.append(line)
    routes_dilated.append(dilated)

route_unions_dilated = unary_union(routes_dilated)
route_unions_eroded = route_unions_dilated.buffer(-0.75*OFFSET_DISTANCE)

if route_unions_dilated.type == 'MultiPolygon':
    for geom in route_unions_dilated.geoms:
        x, y = geom.exterior.xy
        # plt.plot(x, y, "cornflowerblue")
        for interior in geom.interiors:
            xi,yi = interior.xy
            plt.plot(xi, yi, "cornflowerblue")
else:
    x, y = route_unions_dilated.exterior.xy
    plt.fill(x, y, "cornflowerblue")

    x, y = route_unions_eroded.exterior.xy
    plt.fill(x, y, "white")

    for interior in route_unions_eroded.interiors:
        xi,yi = interior.xy
        plt.fill(xi, yi, "cornflowerblue")

    for interior in route_unions_dilated.interiors:
        xi,yi = interior.xy
        plt.fill(xi, yi, "white")

    centerline = Centerline(route_unions_eroded, interpolation_distance=INTERPOLATION_DISTANCE)

    merged_centerline = ops.linemerge(centerline)
    line_extents = []
    line_lengths = []
    for ml_segment in list(merged_centerline.geoms):
        x, y = ml_segment.xy

        line_extents.append((x[0], y[0]))
        line_extents.append((x[-1], y[-1]))
        line_lengths.append(ml_segment.length)

# Once have all the line segment, filter out the ones whose extents are not both in the common_points list. 
# These are the branches. From the branches, delete ones with length < SHORT_LINE_CUTOFF.

SHORT_LINE_CUTOFF = OFFSET_DISTANCE / 2
lines_under_length = [line for line in list(merged_centerline.geoms) if line.length < SHORT_LINE_CUTOFF]

common_points = list(set([pt for pt in line_extents if line_extents.count(pt) > 1]))
uncommon_points = list(set([pt for pt in line_extents if line_extents.count(pt) == 1]))

lines_short_branches = []
for line in lines_under_length:
    x, y = line.xy

    if ((x[0], y[0]) in uncommon_points) or ((x[-1], y[-1]) in uncommon_points) :
        lines_short_branches.append(line)

lines_to_keep = [line for line in list(merged_centerline.geoms) if line not in lines_short_branches]
lines_to_keep_merged = ops.linemerge(lines_to_keep)

merged_line_extents = []
for line in lines_to_keep_merged:
    x, y = line.xy
    plt.plot(x, y, linewidth=3)

    merged_line_extents.append((x[0], y[0]))
    merged_line_extents.append((x[-1], y[-1]))

# recalculate the common points
common_points = list(set([pt for pt in merged_line_extents if merged_line_extents.count(pt) > 1]))
plt.plot(*zip(*common_points),'ob')

list_of_all_points_in_dilated = np.array(route_unions_dilated.exterior.coords)

for hole in route_unions_dilated.interiors :
    coords = np.array(hole.coords)
    list_of_all_points_in_dilated = np.append(list_of_all_points_in_dilated, coords, axis=0)

plt.plot(*zip(*list_of_all_points_in_dilated),'.b')


# what if i did... find me the closest from each exterior/interior. Only consider the closest N interiors though. Must have distance lower than some value. 
# for exterior and each interior, return nearest point. If distance to point < VALUE, keep, otherwise, throw it away. 



# common_intersection points, determine the 'closest' coordinate points on the boundary
# by looking radially. (find diff btwn point, vector, look for min)

# get the coordinates. for the first 'intersection', plot the difference vector.
















# below this is shitballing and ideas. 



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

# I am going to have to find a way to deal with turnbacks.