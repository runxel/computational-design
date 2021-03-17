# -----------------------------------------------------------
# Exercise 010 Double AGENTS and Spies
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2019-01-24"

# Python Component I/Os
# +====+==== IN =======++===== OUT ======+
# │bool│  RUN          ││  _curPositions │
# │bool│  isReset      ││  _allPos       │
# │i   │  nAgents      ││  _color        │
# │bool│  boundaryType ││  _posColors    │
# │f   │  floorHeight  ││  _helperGeo    │
# │f   │* bBoxSize     ││                │
# │brep│  bBREP        ││                │
# │f   │  maxVisited   ││                │
# │i   │  maxTime      ││                │
# +----+---------------++----------------+
# * = List Access  |  % = Tree Access

import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import random, colorsys, math, time

# tolerance
TOLER = 0.001

spread = int(((nAgents * 2.1) + 10) / 2)

if nAgents < 1:
    raise ValueError("Yeah no. This won't work. Please make atleast _one_ Agent.")

if maxVisited is None:
    maxVisited = 1.5

if floorHeight is None:
    floorHeight = 0

if boundaryType == 2 and bBoxSize is None :
    raise ValueError("Please provide a size for the boundary box.")

if 0 in bBoxSize:
    raise ValueError("Size of boundary box can't be zero.")

if len(bBoxSize) != 3:
    raise ValueError("Please provide exactly three arguments for bBox size.")

bx = bBoxSize[0]/2
by = bBoxSize[1]/2
bz = bBoxSize[2]

if bBREP:
    solid = bBREP.IsSolid
if (boundaryType == 3 and bBREP is None) or (bBREP and not solid):
    raise ValueError("Please provide a valid and closed/solid BREP as boundary.")


#-------------------------------------------------------------------------------
# Create a class of agent
# use new style class
class Agent(object):
    def __init__(self, _pos, _id):
        self.pos = _pos
        self.ID = _id
        self.color = self.color()
        self.stuck = False

    def color(self):
        """ Assigns a somewhat random color.
        """
        shift = 360/nAgents  # hue 0-360
        self.hue = round((self.ID + 1) * shift)  # try to seperate the colors at least a little bit
        sat = random.randint(80, 100) # saturation 0-100
        lit = random.randint(40, 70) # lightness 0-100
        # colorsys expects 0-1
        colorRGB = colorsys.hls_to_rgb(self.hue/360, lit/100, sat/100)
        # rs.CreateColor expects 0-255
        colorRGB255 = map(lambda c: math.floor(c*255), colorRGB)
        colDT = rs.CreateColor(colorRGB255[0], colorRGB255[1], colorRGB255[2])
        return colDT

    def Update(self):
        self.CreatePath()
        self.Move()
        posColorsList.append(self.color)

    def CreatePath(self):
        posCopy = rg.Point3d(self.pos)
        posList.append(posCopy)

    def Move(self):
        """ Move the agent, but don't bump into already visited places.
        """
        tryCounterMove = 1
        while True:
            tryPos = rg.Point3d(self.pos)
            choice = random.randint(1, 6)

            if choice == 5:    # left
                tryPos.X -= 1
            elif choice == 2:  # right
                tryPos.X += 1
            elif choice == 4:  # north
                tryPos.Y -= 1
            elif choice == 1:  # south
                tryPos.Y += 1
            elif choice == 6:  # down
                tryPos.Z -= 1
            else:              # up (3)
                tryPos.Z += 1

            # check for boundaries
            check_successful = self.checkBoundary(tryPos)

            if check_successful:
                self.pos = rg.Point3d(tryPos)
                break
            elif tryCounterMove > 6:  # all options are exhausted
                # agent is stuck. removing from list might break things. better set a flag
                self.stuck = True
                break
            else:
                tryCounterMove += 1

    def checkBoundary(self, pos):
        """ Checks for a certain point 'pos' if it still fits into the boundary.
        """
        if pos not in posList:  # not already visited
            if boundaryType == 0:    # no boundary at all
                return True
            elif boundaryType == 1:  # Floor
                if pos.Z >= floorHeight:
                    return True
            elif boundaryType == 2:  # bBox
                if not bBoxAsBrep.IsPointInside(pos, TOLER, False):  # interestingly it needs to be "not" here. not sure why tho
                    return True
            elif boundaryType == 3:  # bBREP
                if bBREP.IsPointInside(pos, TOLER, False):
                    return True
        else:  # you've failed, try again
            return False

    # container types
    def __str__(self):
        return "Agent {} at <{}, {}, {}>, stuck: {}, color: {}".format(
                    self.ID, self.pos.X, self.pos.Y, self.pos.Z, self.stuck, colorNames[self.hue])

# just for the lolz. I mean – why not. This is cool stuff
class RangeDict(dict):
    def __getitem__(self, item):
        if type(item) != xrange:  # xrange since this is Py2
            for key in self:
                if item in key:
                    return self[key]
        else:
            return super(RangeDict, self).__getitem__(item)

# because nobody can relate to fucking RGB codes thrown at him
colorNames = RangeDict({xrange(1,10):    "red",
                        xrange(11,40):   "orange",
                        xrange(41,78):   "yellow",
                        xrange(79,160):  "green",
                        xrange(161,258): "blue",
                        xrange(259,283): "purple",
                        xrange(284,342): "pink",
                        xrange(343,361): "magenta"})

def randomPoint(e):
    """ Creates a random starting Point which avoids collision.
    """
    if boundaryType < 2:  # no boundary, or floor
        # avoid collisions
        while True:
            pt = rg.Point3d(random.randint(-spread, spread), random.randint(-spread, spread), random.randint(floorHeight, floorHeight+10))
            if e != 0 and pt not in [agent.pos for agent in agentsList]:
                break
            elif e == 0:
                break  # on first gen there is no agentsList yet
    elif boundaryType == 2: # bounding Box
        # before we avoid collisions here, we need to be sure the box can actually take all agents
        # ain't nobody got time fo dat. I'll implement it later
        _bx = int(math.floor(bx))
        _by = int(math.floor(by))
        _bz = int(math.floor(bBoxSize[2]))
        pt = rg.Point3d(random.randint(-_bx, _bx), random.randint(-_by, _by), random.randint(0, _bz))
    elif boundaryType == 3: # own boundary BREP
        # Note to myself: you don't invoke AMP at the geometry itself, instead it is an own class which
        # maintains area and mass data
        # so first compute the AMP, then extract the wanted data out of it
        BREP_amp = rg.AreaMassProperties.Compute(bBREP)
        bc = BREP_amp.Centroid
        bc = map(lambda bc: int(bc), bc)
        # hopefully no collisions or outside agents (it's not so bad, so this will get attention later maybe)
        _spread = int(spread/3)
        pt = rg.Point3d(random.randint(bc[0]-_spread, bc[0]+_spread),
                        random.randint(bc[1]-_spread, bc[1]+_spread),
                        random.randint(bc[2]-_spread, bc[2]+_spread))
    return pt


#-------------------------------------------------------------------------------
# MAIN
# create empty lists and global variables for simulation
if "agentsList" not in globals() or isReset:
    agentsList = []
    posList = []
    posColorsList = []
    start_time = time.time()

# init the agents
if len(agentsList) < nAgents:
    for i in range(nAgents):
        pt = randomPoint(i)
        myAgent = Agent(pt, i)
        agentsList.append(myAgent)

# RUN
# stop after threshold, incoporate time only if not zero
if RUN and (len(posList) < (maxVisited*1000)) and ((time.time() - start_time) < maxTime if maxTime != 0 else True):
    for agent in agentsList:
        if agent.stuck: continue  # go into next loop
        agent.Update()
        ghenv.Component.ExpireSolution(True)

#-------------------------------------------------------------------------------
# OUT
if boundaryType == 2:  # bounding box
    # draw the box as wire frame
    pt1 = rg.Point3d(-bx,  by, 0)
    pt2 = rg.Point3d( bx,  by, 0)
    pt3 = rg.Point3d( bx, -by, 0)
    pt4 = rg.Point3d(-bx, -by, 0)
    pt5 = rg.Point3d(-bx,  by, bz)
    pt6 = rg.Point3d( bx,  by, bz)
    pt7 = rg.Point3d( bx, -by, bz)
    pt8 = rg.Point3d(-bx, -by, bz)
    bboxCornerPts = [pt1, pt2, pt3, pt4, pt5, pt6, pt7, pt8]
    bBoxAsBrep = rg.Brep.CreateFromBox(bboxCornerPts)
    _helperGeo = bBoxAsBrep.DuplicateEdgeCurves()

if boundaryType == 3:  # own boundary BREP
    _helperGeo = bBREP.DuplicateEdgeCurves()



for i in range(len(agentsList)):
    print(agentsList[i])
_curPositions = [(agentsList[i].pos) for i in range(len(agentsList))]
_colors = [(agentsList[i].color) for i in range(len(agentsList))]
_allPos = posList
_posColors = posColorsList

