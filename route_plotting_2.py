from pickle import TRUE
import matplotlib.pyplot as plt
import numpy as np
# import shapely.geometry 
from shapely.geometry import LineString, Polygon, MultiLineString, LinearRing
import shapely.ops as so
from shapely.ops import snap
from shapely.ops import unary_union
from shapely import geometry, ops
from scipy.signal import argrelextrema

# Self-made function import let's see if this works. 
import es_gpx

#  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
#  .venv\scripts\activate

GPX_DIRECTORY = 'Activities/Test Activities'
OFFSET_DISTANCE = 0.0001 # this has to be calculated based on the canvas size and minimum nozzle. want each line to be at least 2 nozzle widths wide. 
INTERPOLATION_DISTANCE = OFFSET_DISTANCE * 2/3

[routes, route_unions_dilated, route_unions_eroded] = es_gpx.import_dilate(GPX_DIRECTORY, OFFSET_DISTANCE, True)

if route_unions_dilated.type == 'MultiPolygon':
    for geom in route_unions_dilated.geoms:
        es_gpx.plot_exterior(geom, "cornflowerblue")

        for interior in geom.interiors:
            es_gpx.plot_interior(interior, "cornflowerblue")
else:
    es_gpx.plot_exterior(route_unions_dilated, "cornflowerblue")
    es_gpx.plot_exterior(route_unions_eroded, "white")

    for interior in route_unions_eroded.interiors:
        es_gpx.plot_interior(interior, "cornflowerblue")

    for interior in route_unions_dilated.interiors:
        es_gpx.plot_interior(interior, "white")

    merged_centerline = es_gpx.cl_merge(route_unions_eroded, INTERPOLATION_DISTANCE)
    [cl_extents, cl_lengths] = es_gpx.cl_lengths_extents(merged_centerline)

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

# find the closest N values in list_of_all_points_in_dilated. Get the direction of the vector (from the common_point) 
# and discard points whose values are within some pre-set angle from each other. 
# or look in the difference vector and find N local minima. 
list_of_intersection_rings = []
MINIMUM_ANGLE = 360/16

for pt in common_points:
    boundary_distance = list_of_all_points_in_dilated - pt
    boundary_distance_absolute = np.sum(boundary_distance*boundary_distance, axis=1)

    # aggregate 3 arrays, filter based on condition. 
    point_array = np.c_[list_of_all_points_in_dilated, boundary_distance, boundary_distance_absolute]
    closest_point_array = point_array[ point_array[:,4] < (4*OFFSET_DISTANCE)**2 ]

    # get the indices of local minima
    local_min = argrelextrema(closest_point_array[:,4], np.less)[0]
    intersection_boundary = closest_point_array[ local_min, : ]
    intersection_boundary_coords = intersection_boundary[ :, 0:2 ]

    if intersection_boundary_coords.shape[0] > 2 :
        intersection_boundary_ring = LinearRing(intersection_boundary_coords)

        bnd_int_vectors = intersection_boundary[ :, 2:4]
        bnd_int_angles = np.arctan2(bnd_int_vectors[:,0], bnd_int_vectors[:,1]) * 180 / np.pi
        boundary_coords_sorted = intersection_boundary_coords[np.argsort(bnd_int_angles), :]

        bnd_int_angles_sorted = np.sort(bnd_int_angles)
        bnd_int_angles_sorted_deltas = np.diff(np.append(bnd_int_angles_sorted, bnd_int_angles_sorted[0]+360))

        # Next step is to identify if any bnd_int_angles_sorted_deltas are below the cutoff. 
        if min(abs(bnd_int_angles_sorted_deltas)) < MINIMUM_ANGLE:
            # minimum angle is not really set... just eyeballing. 

            # identify which points are below the threshold. Return the closest one. But what if I have multiple clusters? Eliminate them one at a time?
            # If I have multiple clusters, look for groups of true. IE if abs(bnd_int_angles_sorted_deltas) < 360/16 --> [F T T F F F F T T T F] then I will need to do 2 clusters.
            # abs(bnd_int_angles_sorted_deltas) < 360/16 returns TRUE for the difference to the next index up. IE if it returns true in [1] then it is indices [1:2] that need to be checked. 

            # Sort the vectors pointing to the intersection and find their magnitudes.
            bnd_int_vectors_sorted = bnd_int_vectors[np.argsort(bnd_int_angles), :]
            bnd_int_vectors_sorted_magnitude = np.linalg.norm(bnd_int_vectors_sorted, axis = 1)

            # Sort the angles and deltas in reverse order as well to capture both indices that are within MINIMUM_ANGLE from each other
            bnd_int_angles_sorted_reverse = bnd_int_angles_sorted[::-1]
            bnd_int_angles_sorted_reverse_deltas = np.diff(np.append(bnd_int_angles_sorted_reverse, bnd_int_angles_sorted_reverse[0]+360))

            # Get logical mask vectors
            mask_forward = abs(bnd_int_angles_sorted_deltas) < MINIMUM_ANGLE
            mask_backward = abs(bnd_int_angles_sorted_reverse_deltas[::-1]) < MINIMUM_ANGLE
            mask = np.logical_or(mask_forward, mask_backward)

            # Use the mask to find index of maximum magnitude that is within MINIMUM_ANGLE from another. 
            idx_furthest = np.argwhere(bnd_int_vectors_sorted_magnitude == max(bnd_int_vectors_sorted_magnitude[mask]))

            # Remove the index from the boundary array. Then re-create the angles and deltas 
            boundary_coords_sorted = np.delete(boundary_coords_sorted, idx_furthest, 0)
            # bnd_int_angles_sorted = np.delete(bnd_int_angles_sorted, idx_furthest, 0)
            # bnd_int_angles_sorted_deltas = np.delete(bnd_int_angles_sorted_deltas, idx_furthest, 0)

        sorted_intersection_boundary_ring = LinearRing(boundary_coords_sorted)

        list_of_intersection_rings.append(sorted_intersection_boundary_ring)
        x, y = sorted_intersection_boundary_ring.xy
        plt.plot(x, y, 'r')



        # so what needs to happen is store all the linearrings and look for common points? or areas that overlap? then union of the points, make a new linearring in cw order.
        # If it's weird going around corners or whatever that's okay, because I am only going to be concerned with the segments that cross a centerline. 


plt.show()












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