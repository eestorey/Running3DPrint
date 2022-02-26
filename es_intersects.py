import numpy as np
from scipy.signal import argrelmin

# Functions to find and split the polygon around intersection points. 



def locate_boundary(pt, boundary_pts, threshold):
    """ Pick out the nearest local minima from the distanced to all boundary pts """

    distance_to_all = boundary_pts - pt
    distance_to_all_absolute = np.sum(distance_to_all*distance_to_all, axis = 1)
 
    # aggregate 3 arrays, filter based on condition. 
    point_array = np.c_[boundary_pts, distance_to_all, distance_to_all_absolute]
    closest_point_array = point_array[ point_array[:,4] < threshold ]

    # get the indices of local minima
    local_min = argrelmin(closest_point_array[:,4], mode='wrap', order=2)[0]
    intersection_boundary = closest_point_array[ local_min, : ]

    return intersection_boundary

def vectors_angles(data_points):
    """ self explanatory """

    vectors = data_points
    angles = np.arctan2(vectors[:,0], vectors[:,1]) * 180 / np.pi

    # vectors_out = vectors[np.argsort(angles)]
    # angles_out = np.sort(angles)

    return (vectors, angles)

def sort_by_angle(coords, angles, vectors):
    """ self explanatory """

    coords_out = coords[np.argsort(angles), :]
    angles_out = np.sort(angles)
    vectors_out = vectors[np.argsort(angles)]
    magnitude_out = np.linalg.norm(vectors_out, axis = 1)

    return (coords_out, angles_out, magnitude_out)

def mask_for_small_angles(angles, deltas, min_angle):
    """ filters adjacent angles for ones that are within a close distance """

    reverse_angles = angles[::-1]
    reverse_deltas = np.diff(np.append(reverse_angles, reverse_angles[0]+360))

    mask_forward = abs(deltas) < min_angle
    mask_backward = abs(reverse_deltas[::-1]) < min_angle
    mask = np.logical_or(mask_forward, mask_backward)

    return mask


def delta_angles(angles):
    """ Gets derivative of the sorted angle vector to see if some angles are too close """

    sorted_angles = np.sort(angles)
    delta_angles_out = np.diff(np.append(sorted_angles, sorted_angles[0]+360))

    return delta_angles_out


def coordinate_deltas(coords, angles):
    """ Sorts and returns the coordinate points and their delta_angle to the next pt """

    coords_out = coords[np.argsort(angles), :]
    sorted_angles = np.sort(angles)
    delta_angles_out = np.diff(np.append(sorted_angles, sorted_angles[0]+360))

    return (coords_out, delta_angles_out)



