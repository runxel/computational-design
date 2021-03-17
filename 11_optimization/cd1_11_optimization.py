# -----------------------------------------------------------
# Exercise 11:
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
#
# Some kind of Annealing Solve
# Note:
# We generate a QuadTree and anneal the solution by iterate
# through the tree. It might be necessary to leave the initial QT
# later in the optimitation. This is however not done here.
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2019-02-02"

# Python Component I/Os
# +====+===== IN ======++== OUT =======+
# │srf │  surface      ││  _movPt1     │
# │pt  │  fixPt1       ││  _movPt2     │
# │pt  │  fixPt2       ││  _resultCrv  │
# │int │  nIterations  ││              │
# +----+---------------++--------------+

# IMPORTS
import Rhino.Geometry as rg
import ghpythonlib.components as ghc


if fixPt1 is None or fixPt2 is None:
    raise ValueError("Please provide the points on surface.")

if nIterations is None:
    nIterations = 1

# -----------------------------------------------------------
class Node(object):
    def __init__(self, xStart, yStart, width, height):
        self.xStart = xStart
        self.yStart = yStart
        self.width = width
        self.height = height
        self.midpoint = rg.Point3d(self.xStart + width/2, self.yStart + height/2, 0)
        self.children = []
        self.containsOtherEndPt = False

    def contains(self, pt):
        """ Test if a node contains a certain point and return True, otherwise False. """
        x = self.xStart
        y = self.yStart
        w = self.width
        h = self.height

        if pt.X >= x and pt.X <= x+w and pt.Y >= y and pt.Y <= y+h:
            return True
        else:
            return False

    def subdivide(self):
        """ Subdivide a node. """
        w_ = self.width/2
        h_ = self.height/2

        subn1 = Node(self.xStart, self.yStart, w_, h_)
        subn2 = Node(self.xStart, self.yStart + h_, w_, h_)
        subn3 = Node(self.xStart + w_, self.yStart, w_, h_)
        subn4 = Node(self.xStart + w_, self.yStart + h_, w_, h_)

        self.children = [subn1, subn2, subn3, subn4]
        #return self.children

    def get_midpoints(self):
        c = find_children(self)
        mdpts = []
        for n in c:
            mdpts.append(n.midpoint)
        return mdpts

    def get_children(self):
        """ Get the children of a certain node. """
        c = find_children(self)
        return c


class QuadTree(object):
    """ Initialize a QuadTree object. """
    def __init__(self, excl):
        self.root = Node(0, 0, 1, 1)
        self.excludePt = excl

    def get_children(self):
        """ Get ALL children of this QuadTree object. """
        c = find_children(self.root)
        return c

    def graph(self):
        """ Draw the Quadtree.
            Just for visual debugging at the moment.
        """
        c = find_children(self.root)
        areas = set()
        for el in c:
            areas.add(el.width*el.height)
        ax = []
        for n in c:
            plane = rg.Plane(rg.Point3d(n.xStart, n.yStart, 0), rg.Vector3d.XAxis, rg.Vector3d.YAxis)
            ax.append(rg.Rectangle3d(plane, n.width, n.height))
        return ax


def find_children(node):
    # no children?
    if not node.children:
        return [node]
    else:
        children = []
        for child in node.children:
            # find children recursively
            children += (find_children(child))
    return children

def initEndPt(q):
    """ Take a QuadTree and do the first steps. """
    q.root.subdivide()

    # get midpoints
    initMidPts = q.root.get_midpoints()

    # discard node with other fixPt in it
    children = q.get_children()
    for i, node in enumerate(children):
        if node.contains(q.excludePt):
            del initMidPts[i]
            del children[i]
            break # since there is only one other end point here we can safely break if contains=True

    lenNoD = {}  # a dict where we store the result from ghc.CrvOnSrf; Length is key
    # test the three midpoints
    for i in range(len(initMidPts)):
        inputPts = [fixPt1, initMidPts[i], fixPt2]
        # returns curve, length, domain
        srfcrvLen = ghc.CurveOnSurface(surface, inputPts, False)[1]
        # save to dict, length as key, node as value
        lenNoD[srfcrvLen] = children[i]

    # sort for shortest path and get the node
    shortest = sorted(lenNoD)[0]
    nodeToSubD = lenNoD[shortest]
    # return the node
    return nodeToSubD

#--------------------------------------------------------------------------------------

# init the quadtrees with point to exlude from subD'ing
qtPt1 = QuadTree(fixPt2)
qtPt2 = QuadTree(fixPt1)

winnerNode1 = initEndPt(qtPt1)
winnerNode2 = initEndPt(qtPt2)
# we just got the nodes to start off
# the difference: from now on both points are taken into account

for it in range(nIterations):
    # 1) subD, node gets children
    winnerNode1.subdivide()
    winnerNode2.subdivide()

    # 2) get midpoints
    midPts1 = winnerNode1.get_midpoints()
    midPts2 = winnerNode2.get_midpoints()

    # 3) test
    children1 = winnerNode1.get_children()
    lenNoD = {}
    for m in range(len(midPts1)):
        inputPts = [fixPt1, midPts1[m], winnerNode2.midpoint, fixPt2]
        srfcrvLen = ghc.CurveOnSurface(surface, inputPts, False)[1]
        lenNoD[srfcrvLen] = children1[m]
    shortest = sorted(lenNoD)[0]
    winnerNode1 = lenNoD[shortest]

    children2 = winnerNode2.get_children()
    lenNoD = {}
    for m in range(len(midPts2)):
        inputPts = [fixPt1, winnerNode1.midpoint, midPts2[m], fixPt2]
        srfcrvLen = ghc.CurveOnSurface(surface, inputPts, False)[1]
        lenNoD[srfcrvLen] = children2[m]
    shortest = sorted(lenNoD)[0]
    winnerNode2 = lenNoD[shortest]


#--------------------------------------------------------------------------------------
# Output

# points
_movPt1 = rg.Surface.Evaluate(surface, winnerNode1.midpoint.X, winnerNode1.midpoint.Y, 0)[1]
_movPt2 = rg.Surface.Evaluate(surface, winnerNode2.midpoint.X, winnerNode2.midpoint.Y, 0)[1]

# show the quadtree | debug for now
# d = th.list_to_tree(qtPt1.graph())
# f = th.list_to_tree(qtPt2.graph())

# resulting curve
inputPts = [fixPt1, winnerNode1.midpoint, winnerNode2.midpoint, fixPt2]
_resultCrv = ghc.CurveOnSurface(surface, inputPts, False)[0]


