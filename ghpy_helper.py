__author__ = "Lucas Becker"
__version__ = "1.0"

import Rhino.Geometry as rg
import Rhino.RhinoDoc as rhActiveDoc
import ghpythonlib.components as ghcomp
import collections

TOLER = rhActiveDoc.ActiveDoc.ModelAbsoluteTolerance

# --------------------------------------------------------------------------- #
""" A collection of helper functions to use in Grasshopper Python. """
# PEP 8 and 257 compliant (mostly).

def get_midpt(line):
    """ Return the point at the center of a line. """
    # TODO: overload so it can be used with polylines as well
    pt_start = line.PointAtStart
    pt_end = line.PointAtEnd
    return rg.Point3d((pt_end[0] + pt_start[0])/2, (pt_end[1] + pt_start[1])/2, (pt_end[2] + pt_start[2])/2)


def map_value_to_crv_domain(value, crv):
    """ Map a certain value to the domain of the input curve. """
    crvlen = crv.GetLength()
    dom1 = ghcomp.ConstructDomain(0, crvlen)
    dom2 = ghcomp.ConstructDomain(0, 1)
    return ghcomp.RemapNumbers(value, dom1, dom2).mapped


def isect_plane_brep(plane, brep):
    """ Return the first intersection curve of a BREP and a plane. """
    return  rg.Intersect.Intersection.BrepPlane(brep, plane, TOLER)[1][0]


def isect_curve_plane(crv, plane):
    """ Return the intersection points of the input curve and plane. """
    isects = rg.Intersect.Intersection.CurvePlane(crv, plane, TOLER)
    pts = []
    for i in isects:
        pts.append(i.PointA)
    return pts


def split_srf_by_crv(srf, crv):
    """ Split a surface with one curve. """
    srfb = srf.ToBrep()
    faces_ = srfb.Faces[0]
    splits = faces_.Split([crv], TOLER).Faces
    split_return = []
    for s in splits:
        split_return.append(s.DuplicateFace(False))
    return split_return


def split_srf_by_mult_crv(srf,crvs):
    """ Split a surface with multiple curves. """
    srfb = srf.ToBrep()
    faces_ = srfb.Faces[0]
    splits = faces_.Split(crvs,TOLER).Faces
    split_return = []
    for s in splits:
        split_return.append(s.DuplicateFace(False))
    return split_return


def frange(x, y, step_=1.0):
    """ Create a 'range' with floating steps. """
    i = 0.0
    x = float(x)  # Make sure it's not int
    x_base = x
    epsilon = step_ * 0.5
    yield x  # yield always first value
    while x + epsilon < y:
        i += 1.0
        x = x_base + i * step_
        yield x


def flatten(list_):
    """ Flatten a list where not every subitem is actually an iterable.
        An example input would be: [1,2,[4,5]]
        The result is: [1,2,3,4,5]
    """
    for litem in list_:
        if isinstance(litem, collections.Iterable) and not isinstance(litem, basestring): # Py2.7
            for sub in flatten(litem):
                yield sub
        else:
            yield litem


def clamp(val, min_=0.0, max_=1.0):
    """ Clamp a value between an upper and lower bound. """
    return min_ if val < min_ else max_ if val > max_ else val
