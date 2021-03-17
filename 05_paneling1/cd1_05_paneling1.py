# -----------------------------------------------------------
# Exercise 05: Oval Stadium
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
#
# TODO:
# 	* clean up the loops
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2018-12-04 v1"

# Python Component I/Os
# +====+====== IN ======++====== OUT ========+
# │pt  │  basePt        ││   _construction   │
# │f   │  radiusSmall   ││   _surfaces       │
# │f   │  ovalWidth     ││   _linework       │
# │f   │  ovalLength    ││   _verboseOval    │
# │f   │  height        ││   _verboseConstr  │
# │f   │  offsetMid     ││   _verbosePoints  │
# │f   │  midOHeight    ││                   │
# │f   │  offsetTop     ││                   │
# │int │  nDitches      ││                   │
# │f   │  openAngle     ││                   │
# │int │  nHorDiv       ││                   │
# +––––+––––––––––––––––++––––––---------––––+


# IMPORTS
import Rhino.Geometry as rg
import ghpythonlib.components as gc
import ghpythonlib.treehelpers as th
import math, copy
from scriptcontext import doc



# little hack so we don't get touching small circles
if radiusSmall == ovalWidth:
    radiusSmall -= 0.001

if not height:
    height = 4.0

if (abs(radiusSmall-offsetTop) < doc.ModelAbsoluteTolerance) or (radiusSmall < offsetTop):
    raise ValueError("offsetTop can't be that big.")

# get the height for the middle Oval
midOHeight = (height - basePt.Z) *midOHeight


# -----------------------------------------------------------
# O V A L
class Oval:
    """ Creates an oval by creating 4 tangent circles. """
    def __init__(self, midPt, radiusSmall, hSpace, height):
        self.baseCrc = []
        # CIRCLES #
        CircleLeft = rg.Circle(rg.Point3d(midPt.X -hSpace, midPt.Y, midPt.Z), radiusSmall)
        CircleLeft = CircleLeft.ToNurbsCurve()
        CircleLeft.Domain = rg.Interval(0,1)    # reparam crv
        CircleRight = rg.Circle(rg.Point3d(midPt.X +hSpace, midPt.Y, midPt.Z), radiusSmall)
        CircleRight = CircleRight.ToNurbsCurve()
        CircleRight.Domain = rg.Interval(0,1)   # reparam crv

        # Gegenkathetenwinkel und Hypotenuse berechnen
        degHeight = 90.0 - height
        hypotenuse = (hSpace / math.sin(math.radians(degHeight)))

        # Gegenkathete berechnen
        vSpace = math.sqrt( hypotenuse**2 - hSpace**2 )
        # radius of bigger circles
        radiusBig = hypotenuse + radiusSmall

        CircleTop = rg.Circle(rg.Point3d(midPt.X, midPt.Y +vSpace, midPt.Z), radiusBig)
        CircleTop = CircleTop.ToNurbsCurve()
        CircleTop.Domain = rg.Interval(0,1)     # reparam crv
        CircleBottom = rg.Circle(rg.Point3d(midPt.X, midPt.Y -vSpace, midPt.Z), radiusBig)
        CircleBottom = CircleBottom.ToNurbsCurve()
        CircleBottom.Domain = rg.Interval(0,1)  # reparam crv

        self.baseCrc.extend([CircleLeft, CircleRight, CircleTop, CircleBottom])

        # INTERSECTION
        # intersection params t
        cxct1 = [] # will be left
        cxct2 = [] # will be right

        # get the params
        for crc in [CircleTop, CircleBottom]:
            cxct1.append(gc.CurveXCurve(crc, CircleLeft)[2])
            cxct2.append(gc.CurveXCurve(crc, CircleRight)[2])

        # use the params
        splitLeftRight = []
        splitLeftRight.extend(CircleLeft.Split(cxct1))
        splitLeftRight.extend(CircleRight.Split(cxct2))
        splitTopBottom = []
        splitTopBottom.extend(CircleTop.Split([cxct1[0], cxct2[0]])) # first t is the bottom param
        splitTopBottom.extend(CircleBottom.Split([cxct1[1], cxct2[1]]))

        # get the inside curves
        # by calc'ing shortest pts on crv to midPt we can deselect unwanted crv
        ptclose = []
        for i, cpt in enumerate(self.baseCrc):
            ptclose.append(gc.CurveClosestPoint(midPt, cpt)[0])

        lnLR = rg.Line(ptclose[0], ptclose[1]) # left to right
        lnTB = rg.Line(ptclose[2], ptclose[3]) # top to bottom

        allcrv = []
        for crv in splitLeftRight:
            if (gc.CurveXCurve(crv, lnLR)[0] is None): # no touch means yep
                allcrv.append(crv)
        for crv in splitTopBottom:
            if (gc.CurveXCurve(crv, lnTB)[0]): # no touch means no
                allcrv.append(crv)

        # join curves and synchronize the seam
        joinedCrv = rg.Curve.JoinCurves(allcrv, doc.ModelAbsoluteTolerance)
        # project midPt unto crv
        ppt = gc.ProjectPoint(midPt, rg.Vector3d(-1,0,0), joinedCrv)[0]
        seamTparam = gc.CurveClosestPoint(ppt, joinedCrv)[1] # get t
        # change seam to left outer point
        rg.Curve.ChangeClosedCurveSeam(joinedCrv[0], seamTparam)
        # finally the oval
        self.oval = joinedCrv[0]

    def divide(self, nDiv=nDitches):
        """ Gives specified number of perpendicular (zero-twisting) frames at a curve parameter.
            This will be used to determine the points on the other ovals.
        """
        # get t param
        tForNdiv = rg.Curve.DivideByCount(self.oval, nDiv, True)
        # get perpendicular frames
        perpFrames = []
        perpFrames.extend(gc.PerpFrame(self.oval, tForNdiv))
        # get the actual points
        self.DivPts = []
        for p in perpFrames:
            self.DivPts.append(p.Origin)
        # set breps on the plane for later BrepXCurve
        perpBrep = []
        for i, pf in enumerate(perpFrames):
            tempRec = rg.Rectangle3d(pf, rg.Interval(-offsetMid-1, offsetTop+1), rg.Interval(-1, height+1))
            perpBrep.append(rg.Brep.CreateEdgeSurface(tempRec.ToPolyline().ToNurbsCurve().DuplicateSegments()))
        return perpBrep



# -----------------------------------------------------------

### OVALS
ovalBottom = Oval(basePt, radiusSmall, ovalWidth, ovalLength)
ovalMid = Oval(rg.Point3d(basePt.X, basePt.Y, basePt.Z +midOHeight), radiusSmall+offsetMid, ovalWidth, ovalLength)
ovalTop = Oval(rg.Point3d(basePt.X, basePt.Y, basePt.Z +height), radiusSmall-offsetTop, ovalWidth, ovalLength)

### Points on Ovals
ovalBottomBx = ovalBottom.divide()
ovalBottomDivPts = ovalBottom.DivPts

ovalMidDivPts = []
ovalTopDivPts = []
for p in ovalBottomBx:
    # get the intersection points with the plane
    # [1] since we just want points back
    ovalMidDivPts.append(gc.BrepXCurve(p, ovalMid.oval)[1])
    ovalTopDivPts.append(gc.BrepXCurve(p, ovalTop.oval)[1])


### BASE ARCS for the ditches
vertArcs = []
for k in range(nDitches):
    vertArcs.append(rg.Curve.CreateInterpolatedCurve([ovalBottomDivPts[k],ovalMidDivPts[k],ovalTopDivPts[k]], 3))

### Actual Arc
# we will set the the midpoint between
# TODO: maybe make this parametric
midArcs = []
for k in range(nDitches):
    newMPX = (vertArcs[k].PointAtStart.X + ovalMidDivPts[k].X)/2
    newMPY = (vertArcs[k].PointAtStart.Y + ovalMidDivPts[k].Y)/2
    newMidPt = rg.Point3d(newMPX, newMPY, ovalMidDivPts[k].Z)
    midArcs.append(rg.Curve.CreateInterpolatedCurve([ovalBottomDivPts[k], newMidPt, ovalTopDivPts[k]], 3))

### DITCHES
# by rotating the arcs to the right and the left we create the ditches
if openAngle > 0:
    # we have to copy them first, because rotation is a mutable process
    vertArcsLeft = copy.deepcopy(vertArcs)  # rotated vertArcs
    vertArcsRight = copy.deepcopy(vertArcs)

    for i, crv in enumerate(vertArcsLeft):
        rotVec = crv.PointAtEnd - crv.PointAtStart
        crv.Rotate(math.radians(-openAngle), rotVec, crv.PointAtEnd)
    for i, crv in enumerate(vertArcsRight):
        rotVec = crv.PointAtEnd - crv.PointAtStart
        crv.Rotate(math.radians(openAngle), rotVec, crv.PointAtEnd)

### POINTS on Arcs
midArcPt, leftArcPt, rightArcPt = [], [], []
# we will create now 2dimensional lists
for k in range(nDitches):
    midArcT = rg.Curve.DivideByCount(midArcs[k], nHorDiv, True)
    leftArcT = rg.Curve.DivideByCount(vertArcsLeft[k], nHorDiv, True)
    rightArcT = rg.Curve.DivideByCount(vertArcsRight[k], nHorDiv, True)
    mid, left, right = [], [], []
    for l in range(nHorDiv+1):
        mid.append(rg.Curve.PointAt(midArcs[k], midArcT[l]))
        left.append(rg.Curve.PointAt(vertArcsLeft[k], leftArcT[l]))
        right.append(rg.Curve.PointAt(vertArcsRight[k], rightArcT[l]))
    midArcPt.append(mid)
    leftArcPt.append(left)
    rightArcPt.append(right)

# -----------------------------------------------------------
### LINEWORK
hLineLeft, hLineRight, dgLineLeft, dgLineRight, hBars, midLines, leftLines, rightLines = [], [], [], [], [], [], [], []
# linify arcs
for d in range(nDitches):
    ml, ll, rl = [], [], []
    for p in range(nHorDiv):
        ml.append(rg.LineCurve(midArcPt[d][p], midArcPt[d][p+1]))
        ll.append(rg.LineCurve(leftArcPt[d][p], leftArcPt[d][p+1]))
        rl.append(rg.LineCurve(rightArcPt[d][p], rightArcPt[d][p+1]))
    midLines.append(ml)
    leftLines.append(ll)
    rightLines.append(rl)

# inside the ditches
# horizontal
for d in range(nDitches):
    left, right = [], []
    for m in range(1,nHorDiv):
        left.append(rg.LineCurve(leftArcPt[d][m], midArcPt[d][m]))
        right.append(rg.LineCurve(rightArcPt[d][m], midArcPt[d][m]))
    hLineLeft.append(left)
    hLineRight.append(right)
# diagonal
for d in range(nDitches):
    leftDg, rightDg = [], []
    for m in range(1,nHorDiv-1):
        leftDg.append(rg.LineCurve(leftArcPt[d][m+1], midArcPt[d][m]))
        rightDg.append(rg.LineCurve(rightArcPt[d][m+1], midArcPt[d][m]))
    dgLineLeft.append(leftDg)
    dgLineRight.append(rightDg)

# outside the ditches, horizontal bars
for d in range(nDitches):
    horizontal = []
    for m in range(nHorDiv+1):
        if d == nDitches-1:
            nextd = 0
        else:
            nextd = d+1
        horizontal.append(rg.LineCurve(rightArcPt[d][m], leftArcPt[nextd][m]))
    hBars.append(horizontal)

# -----------------------------------------------------------
### SURFACES
surfQuad, surfTri = [], []

for d in range(nDitches):
    qBrep, tBrep = [], []

    # quad surfaces
    for z in range(nHorDiv):
        if d == nDitches-1:
            nextd = 0
        else:
            nextd = d+1
        qBrep.append(rg.Brep.CreateEdgeSurface([rightLines[d][z], hBars[d][z+1], leftLines[nextd][z], hBars[d][z]]))
    surfQuad.append(qBrep)

    # triangle surfaces
    # ganz unten
    tBrep.append(rg.Brep.CreateEdgeSurface([leftLines[d][0], hLineLeft[d][0], midLines[d][0]]))
    for w in range(1,nHorDiv-1):
        tBrep.append(rg.Brep.CreateEdgeSurface([leftLines[d][w], dgLineLeft[d][w-1], hLineLeft[d][w-1]]))
        tBrep.append(rg.Brep.CreateEdgeSurface([midLines[d][w], dgLineLeft[d][w-1], hLineLeft[d][w]]))
    # ganz oben
    tBrep.append(rg.Brep.CreateEdgeSurface([leftLines[d][-1], hLineLeft[d][-1], midLines[d][-1]]))
    # aaand right
    tBrep.append(rg.Brep.CreateEdgeSurface([rightLines[d][0], hLineRight[d][0], midLines[d][0]]))
    for w in range(1,nHorDiv-1):
        tBrep.append(rg.Brep.CreateEdgeSurface([rightLines[d][w], dgLineRight[d][w-1], hLineRight[d][w-1]]))
        tBrep.append(rg.Brep.CreateEdgeSurface([midLines[d][w], dgLineRight[d][w-1], hLineRight[d][w]]))
    # ganz oben
    tBrep.append(rg.Brep.CreateEdgeSurface([rightLines[d][-1], hLineRight[d][-1], midLines[d][-1]]))
    # pack all together
    surfTri.append(tBrep)


# -----------------------------------------------------------
# OUTPUT

_construction = th.list_to_tree([ovalBottom.oval, ovalMid.oval, ovalTop.oval, vertArcsLeft, vertArcsRight, midArcs])

_linework = th.list_to_tree([hLineLeft, hLineRight, dgLineLeft, dgLineRight, hBars, midLines, leftLines, rightLines])

_surfaces = th.list_to_tree([surfQuad, surfTri])

_verboseOval = ovalBottom.baseCrc
_verboseConstr = th.list_to_tree([ovalBottomBx, ovalBottomDivPts, ovalMidDivPts, ovalTopDivPts, vertArcs])
_verbosePoints = th.list_to_tree([midArcPt, leftArcPt, rightArcPt])
