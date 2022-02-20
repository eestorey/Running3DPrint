# GPX route plotting, offsetting, and centerline functions. 

import os
from gpx_converter import Converter
import matplotlib.pyplot as plt
from shapely import ops
from shapely.geometry import LineString
from shapely.ops import unary_union
from centerline.geometry import Centerline


def import_dilate(file_directory, offset_distance, plotting = False):
    """ Load, unite, and dilate gpx files """

    routes = []
    routes_dilated = []

    for gpx_file in os.listdir(file_directory):
        df = Converter(input_file=os.path.join(file_directory, gpx_file)).gpx_to_dataframe()
        longitude_latitude_tuples = [tuple(x) for x in df[["longitude", "latitude"]].values]

        line = LineString(longitude_latitude_tuples)

        if plotting:
            x, y = line.xy
            plt.plot(x, y, 'gray')

        dilated = line.buffer(offset_distance)

        routes.append(line)
        routes_dilated.append(dilated)

    route_unions_dilated = unary_union(routes_dilated)
    route_unions_eroded = route_unions_dilated.buffer(-0.75*offset_distance)  

    return [routes, route_unions_dilated, route_unions_eroded]


def plot_exterior(region, color):
    """ Plot the exterior of a Polygon region """
    x, y = region.exterior.xy
    plt.fill(x, y, color)


def plot_interior(interior, color):
    """ Plot the interior of a polygon region """
    x, y = interior.xy
    plt.fill(x, y, color)

def cl_merge(region, interp_distance):
    """ calculate centerlines and merge them """
    centerline = Centerline(region, interpolation_distance=interp_distance)
    merged_centerline = ops.linemerge(centerline)

    return merged_centerline

def cl_lengths_extents(centerline):
    """ calculate length and store endpoints of all line segments in centerline """

    line_extents = []
    line_lengths = []

    for ml_segment in list(centerline.geoms):
        x, y = ml_segment.xy

        line_extents.append((x[0], y[0]))
        line_extents.append((x[-1], y[-1]))
        line_lengths.append(ml_segment.length)

    return (line_extents, line_lengths)


