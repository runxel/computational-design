# -----------------------------------------------------------
# Exercise 06a: Islamic Surface Paneling
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
#
# TODO:
#     * angles 22.5° and 45° are making problems
#     * implement more pattern
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2018-12-11"

# Python Component I/Os
# +====+====== IN ===========++===== OUT =====+
# │f   │  Size               ││  _baseTiling  │
# │int │  Ex                 ││  _iStarPatIn  │
# │int │  Ey                 ││  _iStarPatOut │
# │f   │  contactAngle       ││  _verbose     │
# +----+---------------------++---------------+


# IMPORTS
import Rhino.Geometry as rg
import Rhino.RhinoMath as rm
import ghpythonlib.components as ghcomp
import ghpythonlib.treehelpers as th
import math


if Ex < 1 or Ey < 1:
    raise ValueError("Ex and Ey have to be at least 1.")

radiusOct = Size/2
# calculate side length of an octogon
sl = 2* radiusOct * (math.sqrt(2)-1)
# calc the leg of triangle with sl as hypotenuse
kath = math.sqrt((sl/2)**2 *2)


# -----------------------------------------------------------
def shift(l, n):
    """ Shift a list grasshopper style. """
    n = n % len(l)
    head = l[:n]
    l[:n] = []
    l.extend(head)
    return l

def tiling(radius, nx, ny):
    """ Provides base tiling geometry, namely closed touching polygons.
        Tiling Notation: {4,8²}
        (Holes in this structure are not allowed.)
    """
    # octogons first
    sidecount = 8 # octogon
    octogons, rectangles = [], []

    lastPt = rg.Point3d(0,0,0) # our starting point
    for j in range(1, ny+1): ###### OCTOGONS
        temp = []
        for i in range(nx):
            plane = rg.Plane(lastPt, rg.Vector3d.ZAxis)
            circumCircle = rg.Circle(plane, radius)
            temp.append(rg.Polyline.CreateCircumscribedPolygon(circumCircle, sidecount).ToPolylineCurve())
            lastPt.X += (2*sl + 2*kath) # gap in x direction
        octogons.append(temp)

        if j % 2: # modulus, every second row
            lastPt.X = sl + kath
            lastPt.Y += sl + kath
        else:
            lastPt.X = 0
            lastPt.Y += sl + kath

    lastPt = rg.Point3d(sl+kath,0,0) # our starting point
    for j in range(1, ny+1): ####### RECTANGLES
        temp = []
        for i in range(nx):
            plane = rg.Plane(lastPt, rg.Vector3d.ZAxis)
            recDom = rg.Interval(-sl/2, sl/2)
            temp.append(rg.Rectangle3d(plane, recDom, recDom).ToPolyline().ToPolylineCurve())
            lastPt.X += (2*sl + 2*kath) # gap in x direction
        rectangles.append(temp)

        if j % 2: # modulus, every second row
            lastPt.X = 0
            lastPt.Y += sl + kath
        else:
            lastPt.X = sl + kath
            lastPt.Y += sl + kath

    return [octogons, rectangles]

def hankins(polylist, contactAngle=60):
    """ Provides an islamic star pattern based on the paper of C.S. Kaplan.
        (http://www.cgl.uwaterloo.ca/~csk/papers/kaplan_gi2005.pdf)
        This is called "Hankin's Method" since he was the first Western scientist to describe these patterns.
        For this function to work correctly you need a set of polygons which are touching eachother without any gaps.
    """
    segments, midpts, startpts, endpts, vec1, vec2, sdl1, sdl2, lxlPt, innerLines, outerLines = [], [], [], [], [], [], [], [], [], [], []

    for item in polylist:
        segments.append(item.DuplicateSegments())

    for m, seglist in enumerate(segments):
        tempMid, tempStart, tempEnd, tempVec1, tempVec2, tl1, tl2, lxl = [], [], [], [], [], [], [], []


        # 1) points
        for k, seg in enumerate(seglist):
            # get the points of the segments
            # ! IMPORTANT: you have to use .PointAtNormalizedLength
            tempMid.append(seg.PointAtNormalizedLength(0.5))
            tempStart.append(seg.PointAtStart)
            tempEnd.append(seg.PointAtEnd)

        # nested lists
        midpts.append(tempMid)
        startpts.append(tempStart)
        endpts.append(tempEnd)

        # 2) vectors
        for k, seg in enumerate(seglist):
            # Vector: Endpt - Startpt
            # also rotate them
            tv1 = rg.Vector3d(startpts[m][k] - midpts[m][k])
            rg.Vector3d.Rotate(tv1, rm.ToRadians(-contactAngle), rg.Vector3d.ZAxis)
            tempVec1.append(tv1)
            tv2 = rg.Vector3d(endpts[m][k] - midpts[m][k])
            rg.Vector3d.Rotate(tv2, rm.ToRadians(contactAngle), rg.Vector3d.ZAxis)
            tempVec2.append(tv2)

        vec1.append(tempVec1)
        vec2.append(tempVec2)

        # 3) SDL lines
        for k, seg in enumerate(seglist):
            tl1.append(rg.Line(midpts[m][k], vec1[m][k], sl/3))
            tl2.append(rg.Line(midpts[m][k], vec2[m][k], sl/3))

        sdl1.append(tl1)
        sdl2.append(tl2)

        # 4) Line intersections, get points (inner points of a star)
        for k, seg in enumerate(seglist):
            lxl.append(ghcomp.LineXLine(sdl1[m][k], sdl2[m][k-1])[2])
        lxlPt.append(lxl)

    # inner polygons (stars)
    # some advanced slicing going on; dont worry, its acutally very pythonic
    for l, crv in enumerate(polylist):
        # listIn1.append(listIn1.pop(0)) # poor man's list shifting
        # shift(listIn1, -1)
        resultInner = [None]*(len(lxlPt[l][:])+len(midpts[l][:]))
        resultInner[::2] = lxlPt[l][:]
        resultInner[1::2] = midpts[l][:]
        resultInner.append(lxlPt[l][0]) # to close the polyline

        innerLines.append(rg.Polyline(resultInner).ToNurbsCurve())

    # outer polygons
    for p, poly in enumerate(polylist):
        tl = []
        for v in range(len(segments[p])):
            resultOuter = [midpts[p][v], startpts[p][v], midpts[p][v-1], lxlPt[p][v], midpts[p][v]]
            tl.append(rg.Polyline(resultOuter).ToNurbsCurve())
        outerLines.append(tl)

    # for visual clues how this is made
    global verbose
    verbose = segments, midpts, startpts, endpts, sdl1, sdl2, lxlPt

    return innerLines, outerLines


# -----------------------------------------------------------

# gets the base polygon tiling
base = th.list_to_tree(tiling(radiusOct, Ex, Ey))

_basetiling = base

# Flatten it and make it a list again
# Note: We have to call `tiling` again, because I didn't found an easy way to make
#       a deep copy of a tree in Python (and `Flatten()` is a mutable command)
#       and I want to retain the octogons and rectangles in different branches
tiles = th.list_to_tree(tiling(radiusOct, Ex, Ey))
tiles.Flatten()
tiles = th.tree_to_list(tiles)

_iStarPatIn = th.list_to_tree( hankins(tiles,contactAngle)[0])
_iStarPatOut = th.list_to_tree( hankins(tiles,contactAngle)[1])

_verbose = th.list_to_tree(verbose)

