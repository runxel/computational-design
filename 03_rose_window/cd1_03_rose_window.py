# -----------------------------------------------------------
# Exercise 03: The Apollonian Gasket
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
#
# TODO:
#     * implement nested sets
#     * write an exception when invalid circles are generated
#     * there might be issues if the gasket is not drawn at Z=0 (not tested)
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2018-11-18"

# Python Component I/Os
# +====+====== IN =======++==== OUT ====+
# │circ│  startCircle    ││  _startCrc  │
# │f   │  circleSize     ││  _d         │
# │f   │  minRadius      ││             │
# +----------------------++-------------+


# IMPORTS
import Rhino.Geometry as rg
import ghpythonlib.treehelpers as th
import cmath  # need this for complex numbers


startCenter = startCircle.Center
startRadius = startCircle.Radius
globalY     = startCenter.Y

# throw an error ..
if minRadius == 0:
    raise ValueError("Minimal Radius can't be zero.")
if not minRadius:
    minRadius = startRadius * 0.1
if minRadius < (startRadius / 1000):
    raise ValueError("You sure, dawg? We're drawing 2*3^{d+1} circles here for every layer of depth[d].")


if circleSize == 0 or circleSize > startRadius:
    raise ValueError("circleSize can't be zero or bigger than the initial circle radius.")
if not circleSize:
    circleSize = startRadius * 0.5


# -----------------------------------------------------------


def descartesEq(k1, k2, k3):
    """ Solve the Descartes Theorem. """
    # "When trying to find the radius of a fourth circle tangent to three
    # given kissing circles, the equation is best rewritten as:"
    # <https://en.wikipedia.org/wiki/Descartes%27_theorem>
    return k1 + k2 + k3 + 2*(cmath.sqrt(k1 * k2 + k2 * k3 + k1 * k3))

def bVal(circle):
    """ Return the bend of a circle. """
    return 1/circle.Radius

def getAdjacent(c1, c2, c3):
    """ Get the fourth circle. """
    # calc the bend {Krümmung}
    b1 = complex(bVal(c1))
    b2 = complex(bVal(c2))
    b3 = complex(bVal(c3))
    # find the bend of the fourth circle
    # bend of startcircle needs to be negative
    b4 = descartesEq(b1*-1, b2, b3)
    # calc the radius of crc4
    r4 = abs(1/b4.real)

    # position of fourth circle
    # https://mathlesstraveled.com/2016/06/10/apollonian-gaskets-and-descartes-theorem-ii/
    # http://arxiv.org/pdf/math/0101066v1.pdf
    cc1 = cx1*(-bVal(c1))
    cc2 = cx2*(bVal(c2))
    cc3 = cx3*(bVal(c3))

    pos4 = descartesEq(cc1, cc2, cc3) / b4
    p4 = rg.Point3d(pos4.real, pos4.imag, startCenter.Z)
    return rg.Circle(p4, r4)

def flip(c4, c1, c2, c3):
    """ Get the remaining circles in the gasket. """
    # DISCLAIMER:
    #    since rg.Circle.Radius gives us no negative values I have to crosscheck every circle here
    #    thats why the following code looks so ugly. I'm sorry.

    # we already have one b4 value, for other we can
    #    just subtract it from double the sum of the
    #    other three bends
    if c4 == startCircle:
        bend = 2 * (bVal(c1) + bVal(c2) + bVal(c3)) + bVal(c4)
    elif c1 == startCircle:
        bend = 2 * (-bVal(c1) + bVal(c2) + bVal(c3)) - bVal(c4)
    elif c2 == startCircle:
        bend = 2 * (bVal(c1) - bVal(c2) + bVal(c3)) - bVal(c4)
    elif c3 == startCircle:
        bend = 2 * (bVal(c1) + bVal(c2) - bVal(c3)) - bVal(c4)
    else:
        bend = 2 * (bVal(c1) + bVal(c2) + bVal(c3)) - bVal(c4)


    # for each operation we compute the same formula twice
    # one is for the bends, the other for the centers
    # to recover the center you just divide the bend-center product by the bend
    cc1 = complex(c1.Center.X, c1.Center.Y) * (bVal(c1))
    cc2 = complex(c2.Center.X, c2.Center.Y) * (bVal(c2))
    cc3 = complex(c3.Center.X, c3.Center.Y) * (bVal(c3))
    cc4 = complex(c4.Center.X, c4.Center.Y) * (bVal(c4))
    # negative bend if startCircle
    if c1 == startCircle:
        cc1 *= -1
    if c2 == startCircle:
        cc2 *= -1
    if c3 == startCircle:
        cc3 *= -1
    if c4 == startCircle:
        cc4 *= -1

    centerCx = ((cc1 + cc2 + cc3)*2 - cc4) / bend
    centerPt = rg.Point3d(centerCx.real, centerCx.imag, startCenter.Z)
    return rg.Circle(centerPt, 1/bend)


def recurse(c1, c2, c3, c4, depth = 0):
    cn2 = flip(c2, c1, c3, c4)
    cn3 = flip(c3, c1, c2, c4)
    cn4 = flip(c4, c1, c2, c3)

    global rec

    if cn2.Radius > minRadius:
        rec.append(cn2)
        recurse(cn2, c1, c3, c4, depth + 1)

    if cn3.Radius > minRadius:
        rec.append(cn3)
        recurse(cn3, c1, c2, c4, depth + 1)

    if cn4.Radius > minRadius:
        rec.append(cn4)
        recurse(cn4, c1, c2, c3, depth + 1)


def drawGasket(c1, c2, c3):
    """ Draw the Apollonian Gasket. """
    # RhinoCommon has .TryFitCircleTTT
    # BUT unfortunately we don't know the necessary t param
    c4 = getAdjacent(c1, c2, c3)
    c5 = flip(c1, c2, c3, c4)

    recurse(c1, c2, c3, c4)
    recurse(c5, c2, c3, c4)

    return th.list_to_tree([c4, c5, rec])


# -----------------------------------------------------------
# M a i n

# Symmetric Apollonian gasket
# complex numbers are needed for calculation later
cx1 = complex(startRadius, startRadius)
# For reference: in terms of correct calculation the radius and its derivates of
#   the startCircle need to be negative (!) = encapsulating other circles
# This will be the cause of headaches later...


cx2 = complex(circleSize, startRadius)
crc2Center = rg.Point3d(startCenter.X-startRadius+circleSize, globalY, startCenter.Z)
crc2 = rg.Circle(crc2Center, circleSize)


cx3 = complex(startCenter.X + crc2.Radius, globalY)
crc3Center = rg.Point3d(cx3.real, cx3.imag, startCenter.Z)
crc3 = rg.Circle(crc3Center, startRadius - crc2.Radius)


# -----------------------------------------------------------
# DRAW
rec = []  # global list
_startCrc = [startCircle, crc2, crc3]
_d = drawGasket(startCircle, crc2, crc3)
