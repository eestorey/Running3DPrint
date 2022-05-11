import numpy as np
import pandas as pd
from scipy.signal import argrelmin
from shapely.ops import linemerge

# Functions to find and split the polygon around intersection points. 



def locate_boundary(pt, boundary_pts, threshold):
    """ Pick out the nearest local minima from the distanced to all boundary pts """

    # calculate vector to boundary and distance
    distance_xy = boundary_pts - pt
    distance_xy_absolute = np.sum(distance_xy*distance_xy, axis = 1)**0.5

    # put values in df, filter by distance
    df = pd.DataFrame(np.c_[boundary_pts, distance_xy, distance_xy_absolute],
                      columns = ['boundary_pt_x', 'boundary_pt_y', 'delta_x', 'delta_y', 'distance'])
    df_below = df[ df.distance<threshold ]

    while df_below.shape[0] < 50 :
        threshold *= 1.5
        df_below = df[ df.distance<threshold ]

    df = df_below

    # calculate and add vector angles plus delta angle placeholder. sort by angle.
    distance_xy = df[['delta_x','delta_y']].values
    angles = np.arctan2(distance_xy[:,0], distance_xy[:,1]) * 180 / np.pi
    df = df.assign(angle=angles, 
                   delta_angle_f=0, 
                   delta_angle_b=0).sort_values(by=['angle'])

    local_min = argrelmin(df.distance.values, mode='wrap', order=3)[0]
    df = df.iloc[local_min]

    # filter out any points which are uncharacteristically far away.
    if df.shape[0] > 3 :
        sigma_disance = np.median(df.distance.values) + 1*np.std(df.distance.values)
        df = df[ df.distance<sigma_disance ]

    if df.shape[0] == 0 :
        print(df)
    else :
        df = get_delta_angles(df)

    return df

def get_delta_angles(df):
    """ Recalculates the difference between adjacent angles, forward and backwards """
    angle_f = df.angle.values
    angle_b = angle_f[::-1]

    df = df.assign(delta_angle_f = np.diff(np.append(angle_f, angle_f[0]+360)), 
                   delta_angle_b = abs(np.diff(np.append(angle_b, angle_b[0]-360)))[::-1])
    return df

def drop_below_minima(df, minima) :
    """ get row indexes of df where delta_angle_f or _b is < min """
    f = (df.delta_angle_f < minima).values
    b = (df.delta_angle_b < minima).values
    
    df_below_min = df.iloc[f|b]
    idx = df_below_min[ df_below_min.distance == max(df_below_min.distance) ].index[0]

    return df.drop(index=idx)

def gpx_crossings(gpx_paths, boundary_extent):
    """ How many times was the boundary of an intersection crossed by gpx paths? """

    crossings = boundary_extent.intersection(gpx_paths)
    if crossings.type == 'Point':
        return 1
    elif crossings.type == 'MultiPoint':
        return len(list(crossings.geoms))
    else: 
        return crossings

def n_endpoints(poly, boundaries):
    """ go away """
    temp = poly.exterior.intersection(linemerge(boundaries))
    if temp.type == 'LineString':
        return 1
    elif temp.type == 'MultiLineString':
        return len(list(temp.geoms))
    else:
        return 0