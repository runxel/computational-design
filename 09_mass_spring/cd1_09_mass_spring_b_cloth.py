# -----------------------------------------------------------
# Exercise 01: The Staircase
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
#
# Based on a 2001 SIGGRAPH paper by Thomas Jakobsen
# http://www.gpgstudy.com/gpgiki/GDC%202001%3A%20Advanced%20Character%20Physics
#
#
# TODO:
#     * add forces in y direction
#     * solve self intersections
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2019-01-22"

# Python Component I/Os
# +====+===== IN ===========++== OUT ==+
# │bool│  RUN               ││  _net   │
# │bool│  isReset           ││         │
# │f   │  timeInterval      ││         │
# │int │  nRows             ││   	   │
# │f   │  nColumns          ││    	   │
# │f   │  particleDistance  ││    	   │
# +----+--------------------++---------+


# IMPORTS
import Rhino.Geometry as rg
from math import sqrt


#-------------------------------------------------------------------------------
# Constants
GRAVITY = rg.Vector3d(0, 0, -9.8)
TSTEP = timeInterval
PDIS = particleDistance

#-------------------------------------------------------------------------------
# Use new-style classes (=> inherit from 'object' since this is Py2)
class Particle(object):
    """ Stores position, previous position, and where it is in the grid. """
    def __init__(self, currentPos, gridIndex):
        # current position
        self.currentPos = rg.Point3d(currentPos)
        # index [u][v] of where it lives in the grid
        self.gridIndex = gridIndex
        # previous position
        self.oldPos = rg.Point3d(currentPos)
        # init with just the force of gravity (see accumulateForces() below)
        self.forces = GRAVITY
        # lock?
        self.locked = False

    def draw(self):
        # return the point
        return self.currentPos

    def __str__(self):
        return "Particle <{}, {}>".format(self.gridIndex[0], self.gridIndex[1])


class Constraint(object):
    """ Stores 'constraint' data between two Particle objects. """
    def __init__(self, particles):
        self.particles = sorted(particles)
        # calculate restlength as the initial distance between the two particles
        self.restLength = sqrt(abs(pow(self.particles[1].currentPos.X -
                                       self.particles[0].currentPos.X, 2) +
                                   pow(self.particles[1].currentPos.Z -
                                       self.particles[0].currentPos.Z, 2)))

    def draw(self):
        # Draw line between the two particles
        p1 = self.particles[0].currentPos
        p2 = self.particles[1].currentPos
        lines.append(rg.LineCurve(p1, p2))

    def __str__(self):
        return "Constraint <{}, {}>".format(self.particles[0], self.particles[1])


class Grid(object):
    """ Making the grid of Particle objects. """
    def __init__(self, rows, columns, step):

        self.rows = rows
        self.columns = columns
        self.step = step

        # make grid, which is a 2d-array
        # [[p00], [p10], etc
        #  [p01], [p11],
        #   etc,   etc       ]]
        self._grid = []
        for u in range(columns):
            self._grid.append([])
            for v in range(rows):
                currentPos = rg.Point3d(u*self.step, 0, v*self.step)
                self._grid[u].append(Particle(currentPos, (u,v)))

    def getNeighbors(self, gridIndex):
        """ Return a list of all neighbor particles to the particle at the given gridIndex.
            gridIndex = [x,x] : The particle index we're polling.
        """
        possNeighbors = []
        possNeighbors.append([gridIndex[0]-1, gridIndex[1]])
        possNeighbors.append([gridIndex[0], gridIndex[1]-1])
        possNeighbors.append([gridIndex[0]+1, gridIndex[1]])
        possNeighbors.append([gridIndex[0], gridIndex[1]+1])

        neigh = []
        for coord in possNeighbors:
            if (coord[0] < 0) | (coord[0] > self.columns-1):
                pass
            elif (coord[1] < 0) | (coord[1] > self.rows-1):
                pass
            else:
                neigh.append(coord)

        finalNeighbors = []
        for point in neigh:
            finalNeighbors.append((point[0], point[1]))

        return finalNeighbors

    #--------------------------
    # implement container types

    def __len__(self):
        return len(self.rows * self.columns)

    def __getitem__(self, key):
        return self._grid[key]

    def __setitem__(self, key, value):
        self._grid[key] = value

    def __iter__(self):
        for x in self._grid:
            for y in x:
                yield y

    def __contains__(self, item):
        for x in self._grid:
            for y in x:
                if y is item:
                    return True
        return False


class ParticleSystem(Grid):
    """ Wrap it all up. """
    def __init__(self, rows=nRows, columns=nColumns, step=PDIS):
        # Call the parent with super (remember: GhPy is Py2)
        super(ParticleSystem, self).__init__(rows, columns, step)

        # generate constraints between every particle connection.
        self.constraints = []
        for p in self:
            #
            neighborIndices = self.getNeighbors(p.gridIndex)
            for ni in neighborIndices:
                # get the neighbor particle from the index
                n = self[ni[0]][ni[1]]
                # let's not add duplicates
                new = True
                for con in self.constraints:
                    if n in con.particles and p in con.particles:
                        new = False
                if new:
                    self.constraints.append(Constraint((p,n)))

        # lock our top left and right particles by default
        # (and because we actually built the grid from bottom left we end with a nice animation)
        self[0][0].locked = True
        self[1][0].locked = True
        self[-2][0].locked = True
        self[-1][0].locked = True

    def verlet(self):
        # Verlet integration
        for p in self:
            if not p.locked:
                # update old and new position
                temp = rg.Point3d(p.currentPos)
                p.currentPos += p.currentPos - p.oldPos + p.forces * TSTEP**2
                p.oldPos = temp

    def satisfyConstraints(self):
        # keep particles together
        for c in self.constraints:
            # retain a vector 'delta'
            delta = c.particles[0].currentPos - c.particles[1].currentPos
            delta.Unitize()
            deltaLength = rg.Point3d.DistanceTo(c.particles[0].currentPos, c.particles[1].currentPos)
            deflection = deltaLength - c.restLength
            if not c.particles[0].locked:
                c.particles[0].currentPos -= delta*0.5*deflection
            if not c.particles[1].locked:
                c.particles[1].currentPos += delta*0.5*deflection

    def accumulateForces(self):
        # This doesn't do much right now, other than constantly reset the particles 'forces' to 'gravity'.
        # We can implement other things like drag, wind, etc. here later
        for p in self:
            p.forces = GRAVITY

    def update(self):
        # do ya thing!
        self.accumulateForces()
        self.verlet()
        self.satisfyConstraints()

    def draw(self):
        """ Draw the line connections between the particles.
            Renew the list everytime draw() gets called, because this happens only
            once (at the end) per simulation cycle.
            (Will create a fishernet look-a-like)
        """
        global lines
        lines = []
        for c in self.constraints:
            c.draw()


# -----------------------------------------------------------

if 'lines' not in globals() or isReset:
    lines = []

    # create our grid of particles
    particleSystem = ParticleSystem()

    # draw the initial grid once
    particleSystem.draw()

if RUN:

    # update the positions
    particleSystem.update()
    # draw the grid
    particleSystem.draw()

    # expire the solution
    ghenv.Component.ExpireSolution(True)


# -----------------------------------------------------------
# Output
_net = lines
