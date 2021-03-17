# -----------------------------------------------------------
# Exercise 01: The Staircase
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
#
# TODO:
# 	* tidy up the code
# 	* make the posts more parametric
# 	* surfaces should be itself extruded to BREPs
# 	* fancy shit like passing sections of profiles to sweep them
# 	  (railings, posts)
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2018-10-30"

# Python Component I/Os
# +====+====== IN ===========++== OUT ===+
# │f   │  heightOfStaircase  ││  _wire	 │
# │f   │  minHeightRiser 	 ││  _stp 	 │
# │f   │  maxHeightRiser 	 ││  _rsr 	 │
# │pt  │  axisStartPt 		 ││  _rl 	 │
# │f   │  radius 			 ││  _pst	 │
# │f   │  innerRadius 		 ││          │
# │bool│  clockwise 		 ││			 │
# │f   │  headspace 		 ││			 │
# │f   │  pipeRadius 		 ││			 │
# │bool│  showWire 			 ││			 │
# +----+---------------------++----------+


# IMPORTS
import Rhino.Geometry as rg
import ghpythonlib.components as ghcomp
import ghpythonlib.treehelpers as th
# we import treehelpers for outputting datatrees [Rhino 6 and up only]


# throw an error
if maxHeightRiser < minHeightRiser:
	raise ValueError("Maximal height of riser can't be lower than it's minimum.")

# throw an error
if (radius - innerRadius)< 0.8:
	raise ValueError("This staircase is unusable. Stair width too small.")

# calc min and max nSteps
stepsLowerBound = heightOfStaircase / minHeightRiser
stepsUpperBound = heightOfStaircase / maxHeightRiser

# dirty hack for number of steps
nSteps = round(((stepsLowerBound + stepsUpperBound) / 2), 0)

# calc the height of the risers
riserHeight = heightOfStaircase / nSteps

# define starting pt of helix' axis if user has not set it
if not axisStartPt:
	axisStartPt = rg.Point3d(0, 0, 0)

# general use vectors
zVector = rg.Vector3d(0, 0, 1)
rightHandVector = rg.Vector3d(1, 0, 1)
perpPt = axisStartPt + rightHandVector

# throw an error ..
pitch = headspace
if pitch < 2.1:
	raise ValueError("This staircase is unusable. You'd probably bang your head.")

# calc the turnCount
turnCount = heightOfStaircase / pitch

# make turnCount negative to rise stair clockwise
if clockwise:
	turnCount *= -1



# -----------------------------------------------------------
# HELIX
# Create the helix crv (radius 1 and 2 are the same)
helix = rg.NurbsCurve.CreateSpiral( \
	axisStartPt, zVector, perpPt, pitch, turnCount, radius, radius )
# inner helix boundary
helixInner = rg.NurbsCurve.CreateSpiral( \
	axisStartPt, zVector, perpPt, pitch, turnCount, innerRadius, innerRadius )

# divide helix crv
helixParams = []
helixParams = helix.DivideByCount( nSteps, True )

# points on the helix itself
ptHelixList = []
ptHelixInnerList = []
for param in helixParams:
	ptHelixList.append( helix.PointAt(param) )
	ptHelixInnerList.append( helixInner.PointAt(param) )


# -----------------------------------------------------------
# center line | axis
axisEndPt = rg.Point3d(axisStartPt.X, axisStartPt.Y, heightOfStaircase)
axis = rg.LineCurve(axisStartPt, axisEndPt)

# divide axis
axisParams = []
axisParams = axis.DivideByCount(nSteps, True)

# points on axi
ptAxisList = []
for param in axisParams:
	ptAxisList.append(axis.PointAt(param))



# -----------------------------------------------------------
# Steps
# risers first {{Setzstufe}}
riserLines = []
riserSrfs  = []

for i in range(0, int(nSteps)):
	# lines from helix to axis
	riserLines.append(rg.LineCurve(ptHelixInnerList[i], ptHelixList[i]))

	# create riser surfaces
	extrusionVector = rg.Vector3d(0 , 0 , (pitch * abs(turnCount)) / nSteps)
	riserSrfs.append(rg.Extrusion.CreateExtrusion(riserLines[i],  extrusionVector))

# steps
# {{Trittstufen}}
stepSrfs = []
ptPostList = [] 	# for the railing posts later on
ptPostInnerList = []

for i in range( 0, int(nSteps) ):
	if (i < len(ptAxisList)):
		# create srf points
		#  pt1  +----+  pt2
        #       |    |
		#  pt4  +----+  pt3
		ptA = ptAxisList[i+1] 						# on axis
		pt1 = rg.Point3d(ptHelixInnerList[i+1])		# on inner helix
		pt2 = ptHelixList[i+1]						# on outer helix
		pt3 = rg.Point3d(ptHelixList[i].X, ptHelixList[i].Y, ptHelixList[i+1].Z)
		pt4 = rg.Point3d(ptHelixInnerList[i].X, ptHelixInnerList[i].Y, ptHelixInnerList[i+1].Z)

		# create srf lines as boundary
		surfaceLines = []

		surfaceLines.append( rg.LineCurve(pt1, pt2))
		surfaceLines.append( rg.LineCurve(pt3, pt4))
		# the other boundaries should be arc
		# :: arc(plane, radius, angle)
		# plane's easy
		arcPlane = rg.Plane(ptA, pt2, pt3)
		# compute the angle by feedig the VectorAngle method our points
		# corrected by subtracting the midpoint (axis)
		arcOuterAngle = rg.Vector3d.VectorAngle(pt2 - ptA, pt3 - ptA)
		# an Arc is just a simple structure
		# curve representation of an arc is a Rhino.Geometry.ArcCurve object
		# we create one by passing a Rhino.Geometry.Arc object
		arcOuter = rg.ArcCurve( rg.Arc(arcPlane, radius, arcOuterAngle))
		surfaceLines.append(arcOuter)

		# if stair is 'Wendeltreppe', not 'Spindeltreppe'
		if innerRadius > 0:
			arcInnerAngle = rg.Vector3d.VectorAngle(pt1 - ptA, pt4 - ptA)
			arcInner = rg.ArcCurve( rg.Arc(arcPlane, innerRadius, arcInnerAngle))
			surfaceLines.append(arcInner)

			# start points for the inner posts
			postPtParam = arcInner.DivideByCount(2, False)
			if i == 0:
				zDistancePost = (arcInner.PointAt(postPtParam[0]).Z)/2
			ptPostInnerList.append(arcInner.PointAt(postPtParam[0]))


		# finally create srf itself by passing our boundaries as crv
		stepSrfs.append(rg.Brep.CreateEdgeSurface(surfaceLines))

		# start points for the posts
		postPtParam = arcOuter.DivideByCount(2, False)
		if i == 0:
			zDistancePost = (arcOuter.PointAt(postPtParam[0]).Z)/2
		ptPostList.append(arcOuter.PointAt(postPtParam[0]))


# -----------------------------------------------------------
# Railing
# railing curve
railingCrv = helix.DuplicateCurve()
railingCrvInner = helixInner.DuplicateCurve()
# z-translate the curve 1m
tr = rg.Transform.Translation(zVector)
railingCrv.Transform(tr)
railingCrvInner.Transform(tr)

# railing pipe
railing = rg.Brep.CreatePipe(railingCrv, pipeRadius, True, 0, True, 0.001, 0.001)
# cap the railing
railing = ghcomp.CapHolesEx(railing)[0]

if innerRadius > 0:
	railingInner = rg.Brep.CreatePipe(railingCrvInner, pipeRadius, True, 0, True, 0.001, 0.001)
	railingInner = ghcomp.CapHolesEx(railingInner)[0]


# railing posts
postLines = []
postLinesInner = []

for i in range(0,len(ptPostList)):
	# lines from helix to axis
	postLines.append(rg.LineCurve(ptPostList[i], ptPostList[i] + rg.Point3d(0, 0, 1-zDistancePost-pipeRadius)))

if innerRadius > 0:
	for i in range(0,len(ptPostInnerList)):
		# lines from helix to axis
		postLinesInner.append( rg.LineCurve( ptPostInnerList[i], ptPostInnerList[i] + rg.Point3d(0, 0, 1-zDistancePost-pipeRadius)))



# -----------------------------------------------------------
# Output
if showWire:
	_wire = [helix, helixInner, axis]
_stp = stepSrfs
_rsr = riserSrfs
if innerRadius > 0:
	_rl = [railing, railingInner]
	_pst = th.list_to_tree([postLines, postLinesInner])
else:
	_rl = railing
	_pst = postLines


# CAUTION
# Using a struct like `out = [foo,bar] can actually
# return a list of a list (like `[foo,[bar]]`)
# GH does not like that...
