# -----------------------------------------------------------
# Exercise 06b: Mapping a Grid unto a Surface
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2018-12-11"

# Python Component I/Os
# +====+====== IN ========++=== OUT =====+
# │surf      │  Surface   ││  _ptsOnSrf  │
# │crv [flat]│  Grid      ││  _polyCrv   │
# │f         │  adjSeam   ││  _panels    │
# +----------+------------++-------------+


# IMPORTS
import Rhino.Geometry as rg
import ghpythonlib.components as ghc
import Grasshopper.DataTree as DataTree
import Grasshopper.Kernel.Data.GH_Path as GH_Path


# test whether the surface is closed (has a seam) or not
bUSeam = rg.Surface.IsClosed(Surface, 0) # seam is in U space
bVSeam = rg.Surface.IsClosed(Surface, 1) # seam is in V space

# -----------------------------------------------------------

# 1) Reparameterize the surface space
domain = rg.Interval(0, 1)
Surface.SetDomain(0, domain)
Surface.SetDomain(1, domain)

# 2) Getting the Grid Domains
GridPtsX = []
GridPtsY = []
for crv in Grid:
    crvPts = ghc.Discontinuity(crv, 1)[0] # Get the cell corner points
    for pt in crvPts:
        GridPtsX.append(pt.X)
        GridPtsY.append(pt.Y)
# create domain [ternary operator]
domainX = rg.Interval(min(GridPtsX), max(GridPtsX)-adjSeam) if bUSeam else rg.Interval(min(GridPtsX), max(GridPtsX))
domainY = rg.Interval(min(GridPtsY)-adjSeam, max(GridPtsY)) if bVSeam else rg.Interval(min(GridPtsY), max(GridPtsY))

# 3) Remaping the points
surfPts = DataTree[rg.Point3d]()
for pathNo, crv in enumerate(Grid):
    crvPts = ghc.Discontinuity(crv, 1)[0]
    path = GH_Path(pathNo)
    for pt in crvPts:
        x = ghc.RemapNumbers(pt.X, domainX, domain)[0]
        y = ghc.RemapNumbers(pt.Y, domainY, domain)[0]
        surfPts.Add(Surface.PointAt(x,y),path)

# 4) Creating the panels
surcCrvs = DataTree[rg.Curve]()
survPanels = DataTree[rg.Brep]()
for i in range(surfPts.BranchCount):
    path = GH_Path(i)
    branch = surfPts.Branch(i)
    flatCrv = []
    if branch.Count > 3:
        # let the GH do the work for us
        plane = ghc.PlaneFit(branch)[0]
        for i in range(0, branch.Count):
            pt = plane.ClosestPoint(branch[i])
            flatCrv.append(pt)
    else:
        flatCrv = branch
    closedCrv = ghc.PolyLine(flatCrv, True)
    surcCrvs.Add(closedCrv, path)
    Panel = ghc.BoundarySurfaces(closedCrv)
    survPanels.Add(Panel, path)


# -----------------------------------------------------------
# Output
_ptsOnSrf = surfPts
_polyCrv = surcCrvs
_panels = survPanels
