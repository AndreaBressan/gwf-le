# -*- coding: utf-8 -*-
"""
Created on Thu Aug 25 15:58:01 2022

@author: Leonardo
"""
# import numpy as np


def circle_line_segment_intersection(circle_center, circle_radius, pt1, pt2, full_line=False, tangent_tol=1e-9):
    """ Find the points at which a circle intersects a line-segment.  This can happen at 0, 1, or 2 points.

    :param circle_center: The (x, y) location of the circle center
    :param circle_radius: The radius of the circle
    :param pt1: The (x, y) location of the first point of the segment
    :param pt2: The (x, y) location of the second point of the segment
    :param full_line: True to find intersections along full line - not just in the segment.  False will just return intersections within the segment.
    :param tangent_tol: Numerical tolerance at which we decide the intersections are close enough to consider it a tangent
    :return Sequence[Tuple[float, float]]: A list of length 0, 1, or 2, where each element is a point at which the circle intercepts a line segment.

    Note: We follow: http://mathworld.wolfram.com/Circle-LineIntersection.html
    """

    (p1x, p1y), (p2x, p2y), (cx, cy) = pt1, pt2, circle_center
    (x1, y1), (x2, y2) = (p1x - cx, p1y - cy), (p2x - cx, p2y - cy)
    dx, dy = (x2 - x1), (y2 - y1)
    dr = (dx ** 2 + dy ** 2)**.5
    big_d = x1 * y2 - x2 * y1
    discriminant = circle_radius ** 2 * dr ** 2 - big_d ** 2

    if discriminant < 0:  # No intersection between circle and line
        return []
    else:  # There may be 0, 1, or 2 intersections with the segment
        intersections = [
            (cx + (big_d * dy + sign * (-1 if dy < 0 else 1) * dx * discriminant**.5) / dr ** 2,
             cy + (-big_d * dx + sign * abs(dy) * discriminant**.5) / dr ** 2)
            for sign in ((1, -1) if dy < 0 else (-1, 1))]  # This makes sure the order along the segment is correct
        if not full_line:  # If only considering the segment, filter out intersections that do not fall within the segment
            fraction_along_segment = [(xi - p1x) / dx if abs(dx) > abs(dy) else (yi - p1y) / dy for xi, yi in intersections]
            intersections = [pt for pt, frac in zip(intersections, fraction_along_segment) if 0 <= frac <= 1]
        if len(intersections) == 2 and abs(discriminant) <= tangent_tol:  # If line is tangent to circle, return just one point (as both intersections have same location)
            return [intersections[0]]
        else:
            return intersections
#------------------------------------------------------------------------------#

# SlopeHeigth = 5
# SlopeAngle = 60

# Xlft = [ -3 * SlopeHeigth , 0 ]
# Xrht = [  3 * SlopeHeigth , SlopeHeigth ]
# A = [ 0 , 0 ]
# B = [ SlopeHeigth / np.tan(np.radians(SlopeAngle)) , SlopeHeigth ]

# circle_center = [ -2.9684815220758916 ,  6.525105849101829]
# circle_radius = 7.0864445255757476
# pt1 = [2.88 , 5]
# pt2 = [15 , 5]
# res_crest = circle_line_segment_intersection(circle_center, circle_radius, pt1, pt2, full_line=True, tangent_tol=1e-9)

    
# res_crest_f = []
# if res_crest == []:
#     res_crest_f = [[0 , 0] , [0 , 0]]
# else:
#     res_crest_f = [(pt1[0] , pt1[1]) , res_crest[1]]
    
# crest_limit = [ pt1[0] , max(res_crest_f[1][0] , pt1[0]) ]