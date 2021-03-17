# -----------------------------------------------------------
# Exercise 02: The Twisted Tower
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
#
# TODO:
# 	* Make the script more robust to user input
# 	* Make floors
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2018-11-13"

# Python Component I/Os
# +====+====== IN ======++==== OUT ===+
# │crv │  crv1          ││  _curves   │
# │int │  divisionZ		││  _panels   │
# │int │  divisionV 	││            │
# │f   │  width			││  		  │
# │f   │  superness 	││ 			  │
# +––––+––––––––––––––––++––––––––––––+


# IMPORTS
import Rhino.Geometry as rg
import ghpythonlib.treehelpers as th
import math


# throw an error ..
if superness == 0:
	raise ValueError("Superness can't be zero.")
# set superness if not set
if not superness:
	superness = 2.5

# throw an error ..
if divisionZ < 1:
	raise ValueError("divisionZ can't be smaller than one.")

###################################################################

def superellipse(width, height, zCoord, superness=2.5):
	""" Creates a 'superellipse' (also known as Lamé curve)
	    with the parameters width, height, zCoord and superness.
	"""

	smoothness = 40 	# never use less than 20, otherwise its bumpy
	step = (math.pi/2) / smoothness
	ellipsePoints = []
	crvParts = []

	for k in range(smoothness+1):
		# calc the superellipse function (~ graph points)
		xGraph = width  * (math.cos(k*step)**(2/superness))
		yGraph = height * (math.sin(k*step)**(2/superness))
		ellipsePoints.append(rg.Point3d(xGraph, yGraph, zCoord))

	# create actual curve by interpolating the points
	# [top right]
	crvDegree = 3
	ellipseCrvPart1 = rg.Curve.CreateInterpolatedCurve( ellipsePoints, crvDegree )

	# mirror to the left, but first duplicate crv since "transform" is a mutable command
	# [top left]
	ellipseCrvPart2 = rg.GeometryBase.Duplicate(ellipseCrvPart1)
	tr = rg.Transform.Mirror(rg.Plane.WorldYZ)
	ellipseCrvPart2.Transform(tr)

	# and mirror again (construct plane by point and normal vector)
	ellipseCrvPart3 = rg.GeometryBase.Duplicate(ellipseCrvPart2) # [lower left]
	ellipseCrvPart4 = rg.GeometryBase.Duplicate(ellipseCrvPart1) # [lower right]
	YZplaneRot = rg.Plane( rg.Point3d(0,0,0), rg.Vector3d(0,1,0) )
	tr = rg.Transform.Mirror(YZplaneRot)
	ellipseCrvPart3.Transform(tr)
	ellipseCrvPart4.Transform(tr)
	crvParts.extend( [ellipseCrvPart1, ellipseCrvPart2, ellipseCrvPart3, ellipseCrvPart4] )

	ellipse = rg.Curve.JoinCurves(crvParts)
	ellipse = rg.Curve.Rebuild( ellipse[0], 30, 3, True )
	# join to have a closed superellipse curve
	return ellipse

# -----------------------------------------------------------
# Get all the the points for the intersections of curve-plane

# Min and max z-coordinate
zCoordMin = min(crv1.PointAtStart.Z, crv1.PointAtEnd.Z)
zCoordMax = max(crv1.PointAtStart.Z, crv1.PointAtEnd.Z)

# Step size
step = (zCoordMax-zCoordMin)/divisionZ

# Create the points
points = []
for i in range(divisionZ+1):
	zCoord = zCoordMin + i*step
	points.append(rg.Point3d(0, 0, zCoord))


# -----------------------------------------------------------
# Create the lamé curves

# Initialize list
ellipses = []

# Loop over all the points (the different heights)
for m, point in enumerate(points):

	# Create a horizontal plane (XY plane) on each of the points
	plane = rg.Plane(point, rg.Vector3d(0,0,1))

	# Find intersection of the plane with curve 1 and 2
	intersection = rg.Intersect.Intersection.CurvePlane(crv1, plane, 0)

	# Get the points from the obtained intersection events
	pointOnCrv = intersection[0].PointA

	# Draw the ellipses
	if m == 0:
		# ratio should not change so just calc it once here
		ratio = pointOnCrv.X / width
		ellipses.append( superellipse(pointOnCrv.X, width, pointOnCrv.Z, superness) )
	else:
		ellipses.append( superellipse(pointOnCrv.X, pointOnCrv.X / ratio, pointOnCrv.Z, superness) )


# -----------------------------------------------------------
# Create facade panels

# Create empty list
panels=[]

## Loop over facades that are placed between two ellipses
for i in range(divisionZ):

	# Facade between two ellipses
	ellipse1 = ellipses[i]
	ellipse2 = ellipses[i+1]

	# Divide the ellipses in equal lines and obtain the points
	## Tangent of the points
	loc1 = rg.Curve.DivideByCount(ellipse1, divisionV, True)
	loc2 = rg.Curve.DivideByCount(ellipse2, divisionV, True)

	# Get the points
	points1=[]
	points2=[]
	for i,j in zip(loc1,loc2):
		points1.append(ellipse1.PointAt(i))
		points2.append(ellipse2.PointAt(j))

	# Create panels
	for i in range(divisionV):
		pt1 = points1[i-1]
		pt2 = points1[i]
		pt3 = points2[i]
		pt4 = points2[i-1]
		panel = rg.NurbsSurface.CreateFromCorners(pt1, pt2, pt3, pt4)
		panels.append(panel)


# -----------------------------------------------------------
# Output
_curves = th.list_to_tree(ellipses)
_panels = panels
