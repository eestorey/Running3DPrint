# from pickle import TRUE
from pickle import FALSE, TRUE
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import LineString, Polygon, MultiLineString, LinearRing
from shapely.ops import unary_union, split, linemerge, polygonize

# Self-made function import let's see if this works.
import es_gpx
import es_intersects

def plot_xy(geom, color):
    """ Make it quicker on the fly to plot things """
    x,y = geom.xy
    plt.plot(x, y, color)


#  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process; .venv\scripts\activate

GPX_DIRECTORY = 'Activities/Richmond Hill'
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

# Find and delete short branches with length < SHORT_LINE_CUTOFF.
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

list_of_all_points_in_dilated = np.unique(list_of_all_points_in_dilated, axis=0)
plt.plot(*zip(*list_of_all_points_in_dilated),'.b')

# find the closest N values in list_of_all_points_in_dilated. Get the direction of the vector (from the common_point)
# and discard points whose values are within some pre-set angle from each other.
# or look in the difference vector and find N local minima.
list_of_intersection_rings = []
MINIMUM_ANGLE = 360/10 # this number is not set at all just eyeballing.
MAX_INTERSECTION_DISTANCE = 2*OFFSET_DISTANCE

for pt in common_points:

    intersection_df = es_intersects.locate_boundary(pt, list_of_all_points_in_dilated, MAX_INTERSECTION_DISTANCE)
    while min(intersection_df['delta_angle_f'].values) < MINIMUM_ANGLE:
        # identify points below nearest-angle threshold. Delete the furthest one.
        intersection_df = es_intersects.drop_below_minima(intersection_df, MINIMUM_ANGLE)
        intersection_df = es_intersects.get_delta_angles(intersection_df)

    if intersection_df.shape[0] <= 2 :
        # plot it if it is a line, in green, so I can spot it.
        plt.plot(intersection_df.boundary_pt_x.values, 
                 intersection_df.boundary_pt_y.values, 'lime')
    else :
        # if there are more than 2 coordinates here (ie it's not a line)
        sorted_coords = intersection_df[['boundary_pt_x','boundary_pt_y']].values
        sorted_intersection_boundary_ring = LinearRing(sorted_coords)
        list_of_intersection_rings.append(sorted_intersection_boundary_ring)
        plot_xy(sorted_intersection_boundary_ring.coords, 'r')

list_of_intersection_polys = []
for ring in list_of_intersection_rings:
    ring_poly = Polygon(ring)
    list_of_intersection_polys.append(ring_poly)

intersection_polys_union = unary_union(list_of_intersection_polys)

corrected_poly_unions = []
dilated_coord_set = set([tuple(x) for x in list_of_all_points_in_dilated])

for poly in intersection_polys_union :
    # find points that are in common beetween each intersection and the boundary.
    # make a new poly 

    # THIS WORKS BUT HOLY HELL NEEDS TO BE CLEANED UP

    coords = set(poly.exterior.coords)
    coord_intersect = coords.intersection(dilated_coord_set)

    centroid = np.mean(list(coord_intersect), axis=0)
    df = pd.DataFrame(np.c_[list(coord_intersect), list(coord_intersect) - centroid], 
                      columns = ['bp_x', 'bp_y', 'dx', 'dy'])
    df = df.assign(angle = np.arctan2(df.dx, df.dy) * 180 / np.pi).sort_values(by=['angle'])

    coords = list([tuple(x) for x in df[['bp_x','bp_y']].values])
    corrected_poly_unions.append(Polygon(coords))

list_of_all_intersection_boundaries = []
for poly in corrected_poly_unions:
    segments = list(map(LineString, zip(poly.exterior.coords[:-1], poly.exterior.coords[1:])))
    for segment in segments:
        list_of_all_intersection_boundaries.append(segment)
        # plot_xy(segment.coords, 'magenta')

boundaries_to_keep = [b for b in list_of_all_intersection_boundaries if lines_to_keep_merged.crosses(b)]
for b in boundaries_to_keep : plot_xy(b, 'magenta')

# I think what I am trying to do here is to find the points in common with intersection lines that
# cross a centerline
boundary_segments = boundaries_to_keep.copy()
boundary_segments.append(route_unions_dilated.boundary)
boundary_limits = unary_union(boundary_segments)
boundary_limits = linemerge(boundary_limits)

split_boundaries = list(polygonize(boundary_limits))
for b in split_boundaries : 
    x,y = b.exterior.xy
    plt.fill(x,y)

# ESSENTIALLY DONE UP TO HERE... THE REGIONS ARE MOSTLY BEING SEPARATED OKAY, NEED TO ASSIGN
# HEIGHTS AND ALSO REMOVE THE ONES THAT ARE 'INTERIORS' (WILL NOT BE COINCIDENT WITH ANY OF THE 
# INTERSECTION BOUNDARIES).

routes_linemerge = linemerge(routes)
number_crossings = [es_intersects.gpx_crossings(routes_linemerge, boundary) for boundary in boundaries_to_keep]
extents_crossings = np.c_[boundaries_to_keep, number_crossings]

# next step... assign heights to each of split boundaries. Will need to determine if it is 
# a simple line segment or an intersection... simple line segments will be coincident with
# 2 lines in boundaries_to_keep. 

wtf_route_polys = [poly for poly in split_boundaries if es_intersects.n_endpoints(poly, boundaries_to_keep) == 0]
simple_route_polys = [poly for poly in split_boundaries if 1 <= es_intersects.n_endpoints(poly, boundaries_to_keep) <= 2]
compound_route_polys = [poly for poly in split_boundaries if es_intersects.n_endpoints(poly, boundaries_to_keep) > 2]


for r in simple_route_polys : 
    es_gpx.plot_exterior(r, 'red')
    for i in r.interiors :
        es_gpx.plot_interior(i, 'white')

for r in compound_route_polys : es_gpx.plot_exterior(r, 'darkred')

plt.show()

# next step... how to actually check THIS poly boundary contains THAT boundary_crossing 
# and so that means height at endpoint is WHATEVER. 

# also... how do i go from poly to stl?


# below this is shitballing and ideas. 




# https://stackoverflow.com/questions/68348779/given-a-polygon-line-in-it-find-position-on-line-where-to-split-the-polygon-w

# count overlapping polygon regions? 
# https://stackoverflow.com/questions/66341143/count-overlapping-features-using-geopandas

# separate different 'streets'
# https://gis.stackexchange.com/questions/98087/split-lines-at-intersection-of-other-lines
# this is what i WANT https://community.esri.com/t5/python-questions/split-road-edge-polygon-at-intersections/td-p/20031

# https://www.youtube.com/watch?v=t6gGrv3vRoM 
# I am going to have to find a way to deal with turnbacks.

