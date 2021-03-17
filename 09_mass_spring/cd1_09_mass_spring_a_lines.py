# -----------------------------------------------------------
# Exercise 09: Mass Spring System
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2019-01-19 v1"


# Python Component I/Os
# +====+===== IN ======++=== OUT =====+
# │bool│  RUN          ││  _particles │
# │bool│  isReset      ││             │
# │crv │  line         ││             │
# │int │  system       ││   		  │
# │f   │  posEnd       ││    		  │
# │int │  nSegments    ││    	      │
# │f   │  mass         ││             │
# │f   │  k            ││             │
# │f   │  damping      ││             │
# │f   │  timeInterval ││             │
# +----+---------------++-------------+


# IMPORTS
import Rhino.Geometry as rg
import random


GRAVITY = rg.Vector3d(0, 0, -9.8)

# threshold distance
SYSSTOP = 0.0001

# stiffness too low?
if k < 1:
    k = 5

# end position should stay in domain
if posEnd < 0.01 or posEnd > 1:
    posEnd = 0.5

if mass < 0.1:
    raise ValueError("Mass is to low.")

if nSegments < 2:
    raise ValueError("Number of Segments can't be lower than two.")

#### BEWARE: timeInterval numbers too high will let the system actually *gain* power

# -----------------------------------------------------------
# Classes
class Particle:
    def __init__(self, _pos):
        self.pos = _pos
        self.isAnchor = False
        self.force = rg.Vector3d.Zero
        self.acc = rg.Vector3d.Zero
        self.vel = rg.Vector3d.Zero

class Spring:
    def __init__(self, _ptStart, _ptEnd, _restLength, _ForceMultiplier = 1):
        self.p1 = _ptStart
        self.p2 = _ptEnd
        self.restLength = _restLength # length at rest (also initial length) as target
        self.m = _ForceMultiplier # make bendy springs possible (they have more force)

    def applySpringForce(self):
        vec = self.p2.pos - self.p1.pos
        vec.Unitize()
        currentLength = rg.Point3d.DistanceTo(self.p1.pos, self.p2.pos)
        deflection = currentLength - self.restLength

        if system == 3: # random
            springForce = -randomK[isp] * deflection * vec
        else:
            springForce = -k * deflection * vec * self.m

        if self.p1.isAnchor == False: self.p1.force -= springForce
        if self.p2.isAnchor == False: self.p2.force += springForce


def CreateParticles():
    # array of param at points
    particleParams = rg.Curve.DivideByCount(line, nSegments, True)

    for i in range(len(particleParams)):
        pos = rg.Curve.PointAt(line, particleParams[i])
        particle = Particle(pos)
        if i == 0 or i == len(particleParams)-1: particle.isAnchor = True

        particlesList.append(particle)

def CreateSprings():
    for i in range(len(particlesList)-1):
        pA = particlesList[i]
        pB = particlesList[i+1]

        length = rg.Point3d.DistanceTo(pA.pos, pB.pos)
        spring = Spring(pA, pB, length)

        springsList.append(spring)

        if system == 2: # BENDING
            if i < len(particlesList)-2:
                pC = particlesList[i+2]
            length2 = rg.Point3d.DistanceTo(pA.pos, pC.pos)
            spring2 = Spring(pA, pC, length2, 2.5)
            springsList.append(spring2)

def applyFloor(inParticle):
    # include the possibility of inclined lines
    minHeight = min(line.PointAtStart.Z, line.PointAtEnd.Z)
    if inParticle.pos.Z < minHeight:
        inParticle.pos.Z = minHeight
        inParticle.vel.Z *= -1

def CreateRandomK():
    for i in range(len(springsList)):
        randomK.append(random.randint(1, k))


# -----------------------------------------------------------

# init particles and springs
if 'particlesList' not in globals() or isReset:
    particlesList = []
    springsList = []

    CreateParticles()
    CreateSprings()

    if system == 3: # random k values
        randomK = []
        CreateRandomK()

# Start and update simulation
if RUN:
    for isp, spring in enumerate(springsList):
        spring.applySpringForce()

    for ip, particle in enumerate(particlesList):
        endPtPos = line.Domain.Max * posEnd

        # make end point draggable
        if ip == len(particlesList)-1:
            particle.pos = line.PointAt(endPtPos)

        # move all other points accordingdly
        if particle.isAnchor == False:
            particle.force -= damping * particle.vel
            particle.force += mass * GRAVITY
            particle.acc = particle.force / (mass * len(particlesList)) * timeInterval
            particle.vel += particle.acc * timeInterval
            # take any sample as threshold
            if ip == 2:
                threshold = abs(particle.acc.Length)
            if system == 2: # BENDING
                applyFloor(particle)
            particle.pos += particle.vel
        particle.force = rg.Vector3d.Zero
        particle.acc = rg.Vector3d.Zero

    # Replace timer by expiring solution automatically
    # but stop, once the system is at rest
    if threshold > SYSSTOP:
        ghenv.Component.ExpireSolution(True)
    else:     # acceleration is now minmal, and lower than the set threshold SYSSTOP
        print("Simulation has stopped.")

# -----------------------------------------------------------
# Output
_particles = [(particlesList[i].pos) for i in range(len(particlesList))]
