# -----------------------------------------------------------
# Exercise 04: Floor and Facade Variation
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
#
# TODO:
#     * optimize the code somehow. It's slow as fuck (well, recursion...)
#     * let the depth of the Sierpinski Triangles be calculated by user input
#         in the way that you can shove BREPs into this components based on which
#         the facade will have more or fewer openings
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2018-11-26"

# Python Component I/Os
# +====+====== IN ====++== OUT ===+
# │pt  │  pos         ││   _wire  │
# │int │  stories     ││   _fac   │
# │f   │  height      ││   _ST    │
# │f   │ *floorsize   ││          │
# │int │  sidecount   ││          │
# │f   │  planeRot    ││          │
# │bool│  ST_ON       ││          │
# +––––+––––––––––––––++––––––––––+
# * = List Access  │  % = Tree Access


# IMPORTS
import sys
from os import path
thisPath = path.normpath(ghenv.Component.Attributes.Owner.OnPingDocument().FilePath)
parentDir = path.dirname(path.dirname(thisPath))
sys.path.append(parentDir)
import ghpy_helper as hf
import Rhino.Geometry as rg
import Rhino.RhinoMath as rm
import random
from scriptcontext import doc



stories = abs(stories)
height  = abs(height)

# Throw an error
if sidecount < 3:
    raise ValueError("How's that supposed to work? Polygon with less than 3 sides' not possible.")

if not floorsize:
    # what a hiccup. frange => generator -> list -> reversed iterator -> list again
    floorsize = list(reversed(list(hf.frange(25, 35, 10/stories))))

# -----------------------------------------------------------

def midpt(pt1, pt2):
    """ Get the midpoint for two arbitrary points in space. """
    return rg.Point3d((pt1[0] + pt2[0])/2, (pt1[1] + pt2[1])/2, (pt1[2] + pt2[2])/2 )

def drawST(pt1, pt2, pt3, level):
    """ Draw a Sierpinski Triangle until depth is reached. """
    global triST
    if level == 1:
        tri = rg.Polyline([pt1, pt2, pt3, pt1])
        tri = tri.ToNurbsCurve()
        trisrf = rg.Brep.CreatePlanarBreps(tri, doc.ModelAbsoluteTolerance)
        triST.append(trisrf[0])
    else:
        pt4 = midpt(pt1, pt2)
        pt5 = midpt(pt2, pt3)
        pt6 = midpt(pt1, pt3)
        drawST(pt1, pt4, pt6, level-1)
        drawST(pt4, pt2, pt5, level-1)
        drawST(pt6, pt5, pt3, level-1)


class Floor:

    def __init__(self, plane, w, h, sidecount=4):
        self.plane = plane
        self.w = w
        self.h = h
        # circle into which the polygon has to fit
        inscribingCircle = rg.Circle(plane, w)
        self.poly = rg.Polyline.CreateInscribedPolygon(inscribingCircle, sidecount)
        self.walls = rg.Extrusion.Create(self.poly.ToNurbsCurve(), h, False)
        self.f = self.facade()

    def facade(self):
        poly = self.poly
        lines = poly.GetSegments()

        triDown = []

        for line in lines:
            crv = line.ToNurbsCurve()
            # number of Sierpinski Triangles
            nOfST = int(crv.GetLength()/self.h)
            curveParams = crv.DivideByCount(nOfST*2, True)
            points = [crv.PointAt(t) for t in curveParams]

            # prepare necessary lists
            ptsBottom = points[::2]     # every second item starting at 0
            ptsTop = []
            ptsTop.append(points[0])    # first item
            ptsTop.extend(points[1::2]) # every second item
            ptsTop.append(points[-1])   # last item

            for i in range(len(ptsBottom)):
                # always closed parts (pointing down triangles)
                pt1 = rg.Point3d(ptsBottom[i])
                pt2 = rg.Point3d(ptsTop[i])
                pt3 = rg.Point3d(ptsTop[i+1])

                pt2.Z = pt2.Z + self.h
                pt3.Z = pt3.Z + self.h

                tri = rg.Polyline([pt1, pt2, pt3, pt1])
                tri = tri.ToNurbsCurve()

                # note that CPB without tol is obsolete
                cShape = rg.Brep.CreatePlanarBreps(tri, doc.ModelAbsoluteTolerance)
                triDown.append(cShape[0])


            for k in range(nOfST):
                depthST = random.randrange(2,5) if ST_ON else 1
                # draw the Sierpinski triangles
                ptsTop[k+1].Z += self.h
                drawST(ptsBottom[k], ptsBottom[k+1], ptsTop[k+1], depthST)

        return triDown


# -----------------------------------------------------------

slabs  = []
facade = []
triST  = []

for lvl in range(0, stories):
    plane = rg.Plane(rg.Point3d(pos.X, pos.Y, lvl*height), rg.Vector3d.ZAxis)
    plane.Rotate(rm.ToRadians(planeRot), rg.Vector3d.ZAxis)
    width = floorsize[lvl]
    floor = Floor(plane, width, height, sidecount)

    slabs.append(floor.poly)
    facade.extend(floor.f)

_wire = slabs
_fac = facade
_ST = triST
