# -----------------------------------------------------------
# Exercise 10: Recreating the "pipe"-Windows 95 screensaver
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
#
# TODO:
# 	* check for other pipes
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2019-01-26"

# Python Component I/Os
# +====+== IN =====++===== OUT ======+
# │bool│  RUN      ││  _curPositions │
# │bool│  isReset  ││  _allPos       │
# │f   │  radius   ││  _color        │
# │bool│  verbose  ││  _pipes        │
# │brep│  teapot   ││  _joints       │
# +----+-----------++----------------+

# IMPORTS
import Rhino.Geometry as rg
import Rhino.RhinoMath as rm
import rhinoscriptsyntax as rs
import ghpythonlib.treehelpers as th
import scriptcontext
import random
import colorsys
import math
import time

# tolerance
TOLER = scriptcontext.doc.ModelAbsoluteTolerance
TOLERRAD = scriptcontext.doc.ModelAbsoluteTolerance

spread = 50
maxNAgents = 8

# option set
jointOptions = [None, None, None, None,
                "ballJoint", "ballJoint", "teapotJoint"]

#-------------------------------------------------------------------------------


class AgentPipe(object):
    def __init__(self, _pos, _id, _radius):
        self.pos = _pos
        self.lastPos = None
        self.ID = _id
        self.color = self.color()
        self.lastMove = random.randint(1, 6)
        self.stuck = False
        self.pipeRadius = _radius
        self.ballJointRadius = self.pipeRadius * 1.5

    def color(self):
        """ Assigns a somewhat random color.
        """
        shift = 360/nAgents  # hue 0-360
        # try to seperate the colors at least a little bit
        self.hue = round((self.ID + 1) * shift)
        sat = random.randint(70, 100)  # saturation 0-100
        lit = random.randint(40, 80)  # lightness 0-100
        # colorsys expects 0-100
        colorRGB = colorsys.hls_to_rgb(self.hue/360, lit/100, sat/100)
        # rs.CreateColor expects 0-255
        colorRGB255 = map(lambda c: math.floor(c*255), colorRGB)
        colDT = rs.CreateColor(colorRGB255[0], colorRGB255[1], colorRGB255[2])
        return colDT

    def update(self):
        self.createPath()
        self.move()
        self.makePipe()
        joint = random.choice(jointOptions)
        if joint == "ballJoint":
            self.makeBallJoint(self.lastPos)
        elif joint == "teapotJoint":
            self.makeTeapotJoint(self.lastPos)

    def createPath(self):
        self.lastPos = rg.Point3d(self.pos)
        posList.append(self.lastPos)

    def move(self):
        # do some smart (or not so smart) trickery (look at the choices down there)
        # we could also compute vector between last two points, unitize, and then compare with new vector... but thats cpu intense
        invert = self.lastMove - 3
        if invert == 0:
            invert = 6
        if invert < 0:
            invert += 6

        while True:
            tryPos = rg.Point3d(self.pos)
            moveDis = random.randint(4, 15)
            choice = random.randint(1, 6)

            if choice == 5:    # left
                tryPos.X -= moveDis
            elif choice == 2:  # right
                tryPos.X += moveDis
            elif choice == 4:  # north
                tryPos.Y -= moveDis
            elif choice == 1:  # south
                tryPos.Y += moveDis
            elif choice == 6:  # down
                tryPos.Z -= moveDis
            else:              # up (3)
                tryPos.Z += moveDis

            if choice != invert and self.checkBoundary(tryPos):
                # update lastMove and new position
                self.lastMove = choice
                self.pos = rg.Point3d(tryPos)
                break

    def checkBoundary(self, pos):
        if boundaryBrep.IsPointInside(pos, TOLER, False):
            return True
        else:
            return False

    def makePipe(self):
        pipeCrv = rg.Line(self.lastPos, self.pos).ToNurbsCurve()
        pipeObj = rg.Brep.CreatePipe(
            pipeCrv, self.pipeRadius, False, rg.PipeCapMode.Round, False, TOLER, TOLERRAD)
        pipesList[self.ID].append(pipeObj[0])

    def makeTeapotJoint(self, _pos):
        tv = _pos - teapotOrigin  # translation vector
        dupl = rg.Brep.Duplicate(teapot)  # duplicate the OG teapot
        tr = rg.Transform.Translation(tv)  # move it to its new position
        dupl.Transform(tr)
        dupl.Scale(self.pipeRadius)  # scale it , and rotate it
        dupl.Rotate(random.choice(
            [0, rm.ToRadians(90)]), rg.Vector3d.XAxis, _pos)
        dupl.Rotate(random.choice(
            [0, rm.ToRadians(90)]), rg.Vector3d.YAxis, _pos)
        dupl.Rotate(random.choice(
            [0, rm.ToRadians(90)]), rg.Vector3d.ZAxis, _pos)
        jointsList[self.ID].append(dupl)

    def makeBallJoint(self, _pos):
        jointsList[self.ID].append(rg.Sphere(_pos, self.ballJointRadius))

    # container types
    def __str__(self):
        return "Agent {} at <{}, {}, {}>, stuck: {}, color: {}".format(
            self.ID, self.pos.X, self.pos.Y, self.pos.Z, self.stuck, colorNames[self.hue])


class RangeDict(dict):
    def __getitem__(self, item):
        if type(item) != xrange:  # xrange since this is Py2.X, ya know
            for key in self:
                if item in key:
                    return self[key]
        else:
            return super(RangeDict, self).__getitem__(item)


# because nobody can relate to fucking RGB codes thrown at him
colorNames = RangeDict({xrange(1, 10):    "red",
                        xrange(11, 40):   "orange",
                        xrange(41, 78):   "yellow",
                        xrange(79, 160):  "green",
                        xrange(161, 258): "blue",
                        xrange(259, 283): "purple",
                        xrange(284, 342): "pink",
                        xrange(343, 361): "magenta"})


def createBrepBox(size):
    spread = size / 2
    cornerPts = []
    cornerPts.append(rg.Point3d(-spread, -spread, 0))
    cornerPts.append(rg.Point3d(spread, -spread, 0))
    cornerPts.append(rg.Point3d(spread,  spread, 0))
    cornerPts.append(rg.Point3d(-spread,  spread, 0))
    cornerPts.append(rg.Point3d(-spread, -spread, size))
    cornerPts.append(rg.Point3d(spread, -spread, size))
    cornerPts.append(rg.Point3d(spread,  spread, size))
    cornerPts.append(rg.Point3d(-spread,  spread, size))
    BrepBox = rg.Brep.CreateFromBox(cornerPts)
    return BrepBox


def randomPoint(e):
    # avoid collisions
    while True:
        pt = rg.Point3d(random.randint(-spread, spread),
                        random.randint(-spread, spread), random.randint(0, spread*2))
        if e != 0 and pt not in [agent.pos for agent in agentsList]:
            break
        elif e == 0:
            break  # on first gen there is no agentsList yet
    return pt


#-------------------------------------------------------------------------------

boundaryBrep = createBrepBox(spread*2)
teapotBBox = teapot.GetBoundingBox(False)
teapotOrigin = rg.Point3d(0, 0, teapotBBox.Center[2])

if "agentsList" not in globals() or isReset:
    nAgents = random.randint(1, maxNAgents)

    agentsList = []
    pipesList = [[] for i in range(nAgents)]
    jointsList = [[] for i in range(nAgents)]
    posList = []
    pipesColorsList = []
    start_time = time.time()
    maxTime = random.randint(4, 10)

    # init the agents
    for i in range(nAgents):
        pt = randomPoint(i)
        myAgent = AgentPipe(pt, i, radius)
        agentsList.append(myAgent)


# RUN
# stop after random time
# TODO: find a method to call isReset so will automatically restart
if RUN and ((time.time() - start_time) < maxTime):
    for agent in agentsList:
        if agent.stuck:
            continue  # go into next loop
        agent.update()
        ghenv.Component.ExpireSolution(True)


#-------------------------------------------------------------------------------
# Output

if verbose:
    for i in range(len(agentsList)):
        print(agentsList[i])
_curPositions = [(agentsList[i].pos) for i in range(len(agentsList))]
_colors = [(agentsList[i].color) for i in range(len(agentsList))]
_allPos = posList
_pipes = th.list_to_tree(pipesList, True)
_joints = th.list_to_tree(jointsList, True)
