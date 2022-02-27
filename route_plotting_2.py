# from pickle import TRUE
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import LineString, Polygon, MultiLineString, LinearRing
from shapely.ops import unary_union, split, linemerge, polygonize

# Self-made function import let's see if this works.
import es_gpx
import es_intersects

def plot_xy(geom, color):
    """ Make it quicker on the fly to plot things """
    x,y = geom.xy
    plt.plot(x, y, color)


#  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
#  .venv\scripts\activate

GPX_DIRECTORY = 'Activities/Test Activities'
OFFSET_DISTANCE = 0.0001 # this has to be calculated. want each line to be at least 2 nozzle widths wide.
INTERPOLATION_DISTANCE = OFFSET_DISTANCE * 2/3

[routes, route_unions_dilated, route_unions_eroded] = es_gpx.import_dilate(GPX_DIRECTORY, OFFSET_DISTANCE, True)

if route_unions_dilated.type == 'MultiPolygon':
    for geom in route_unions_dilated.geoms:
        es_gpx.plot_exterior(geom, "lightgrey")

        for interior in geom.interiors:
            es_gpx.plot_interior(interior, "lightgrey")
else:
    es_gpx.plot_exterior(route_unions_dilated, "lightgrey")

    for interior in route_unions_dilated.interiors:
        es_gpx.plot_interior(interior, "white")

    merged_centerline = es_gpx.cl_merge(route_unions_eroded, INTERPOLATION_DISTANCE)
    [cl_extents, cl_lengths] = es_gpx.cl_lengths_extents(merged_centerline)

# Filter out lines whose extents are not both in the common_points list.
# These are branches. Delete branches with length < SHORT_LINE_CUTOFF.
SHORT_LINE_CUTOFF = OFFSET_DISTANCE / 2
[common_points, uncommon_points] = es_gpx.commonality(cl_extents)
lines_to_keep_merged = es_gpx.remove_shortest_branches(merged_centerline, SHORT_LINE_CUTOFF, uncommon_points)

merged_line_extents = []
for line in lines_to_keep_merged:
    x, y = line.xy
    plt.plot(x, y, linewidth=3)

    merged_line_extents.append((x[0], y[0]))
    merged_line_extents.append((x[-1], y[-1]))

# recalculate the common points
[common_points, uncommon_points] = es_gpx.commonality(merged_line_extents, True)

list_of_all_points_in_dilated = np.array(route_unions_dilated.exterior.coords)
for hole in route_unions_dilated.interiors :
    coords = np.array(hole.coords)
    list_of_all_points_in_dilated = np.append(list_of_all_points_in_dilated, coords, axis=0)

plt.plot(*zip(*list_of_all_points_in_dilated),'.b')

# find the closest N values in list_of_all_points_in_dilated. Get the direction of the vector (from the common_point)
# and discard points whose values are within some pre-set angle from each other.
# or look in the difference vector and find N local minima.
list_of_intersection_rings = []
MINIMUM_ANGLE = 360/16 # this number is not set at all just eyeballing.
MAX_INTERSECTION_DISTANCE = (4*OFFSET_DISTANCE)**2

for pt in common_points:

    intersection_boundary = es_intersects.locate_boundary(pt, list_of_all_points_in_dilated, MAX_INTERSECTION_DISTANCE)
    bi_coords = intersection_boundary[ :, 0:2 ]
    if bi_coords.shape[0] > 2 :

        [bi_vectors, bi_angles] = es_intersects.vectors_angles(intersection_boundary[ :, 2:4])
        [sorted_coords, sorted_deltas] = es_intersects.coordinate_deltas(bi_coords, bi_angles)

        # Next step is to identify if any sorted_deltas are below the cutoff.
        while min(abs(sorted_deltas)) < MINIMUM_ANGLE:
            # identify points below nearest-angle threshold. Delete the furthest one.
            [sorted_coords, sorted_angles, sorted_magnitude] = es_intersects.sort_by_angle(bi_coords, bi_angles, bi_vectors)
            mask = es_intersects.mask_for_small_angles(sorted_angles, sorted_deltas, MINIMUM_ANGLE)
            idx_furthest = np.argwhere(sorted_magnitude == max(sorted_magnitude[mask]))

            sorted_coords = np.delete(sorted_coords, idx_furthest, 0)
            sorted_angles = np.delete(sorted_angles, idx_furthest, 0)
            [sorted_coords, sorted_deltas] = es_intersects.coordinate_deltas(sorted_coords, sorted_angles)

        sorted_intersection_boundary_ring = LinearRing(sorted_coords)
        list_of_intersection_rings.append(sorted_intersection_boundary_ring)
        # plot_xy(sorted_intersection_boundary_ring.coords, 'r')

list_of_intersection_polys = []
for ring in list_of_intersection_rings:
    ring_poly = Polygon(ring)
    list_of_intersection_polys.append(ring_poly)

intersection_polys_union = unary_union(list_of_intersection_polys)

list_of_all_intersection_boundaries = []
for geom in intersection_polys_union.geoms:
    segments = list(map(LineString, zip(geom.exterior.coords[:-1], geom.exterior.coords[1:])))
    for segment in segments:
        list_of_all_intersection_boundaries.append(segment)
        # plot_xy(segment.coords, 'magenta')

# Filter list_of_all_intersection_boundaries for those that cross lines_to_keep_merged
boundaries_to_keep = []
for boundary in list_of_all_intersection_boundaries:
    if lines_to_keep_merged.crosses(boundary):
        boundaries_to_keep.append(boundary)
        plot_xy(boundary.coords, 'lime')


# next step is to segment the outer boundary region according to the lines in boundaries_to_keep
# route_unions_dilated is a polygon object

boundary_segments = boundaries_to_keep
boundary_segments.append(route_unions_dilated.boundary)
boundary_limits = unary_union(boundary_segments)
boundary_limits = linemerge(boundary_limits)

split_boundaries = list(polygonize(boundary_limits))
for boundary in split_boundaries:
    es_gpx.plot_exterior(boundary, 'red')


plt.show()




# below this is shitballing and ideas. 




# https://stackoverflow.com/questions/68348779/given-a-polygon-line-in-it-find-position-on-line-where-to-split-the-polygon-w

# count overlapping polygon regions? 
# https://stackoverflow.com/questions/66341143/count-overlapping-features-using-geopandas

# separate different 'streets'
# https://gis.stackexchange.com/questions/98087/split-lines-at-intersection-of-other-lines
# this is what i WANT https://community.esri.com/t5/python-questions/split-road-edge-polygon-at-intersections/td-p/20031

# https://www.youtube.com/watch?v=t6gGrv3vRoM 
# I am going to have to find a way to deal with turnbacks.

