# -----------------------------------------------------------
# Exercise 08: Spring Pendulumwith Hooke's Law
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2018-13-01"

# Python Component I/Os
# +====+====== IN ====++== OUT ====+
# │bool│  reset       ││  _pos     │
# │pt  │  ptOrigin    ││  _sphere  │
# │pt  │  ptSpring    ││           │
# │f   │  k           ││   		   │
# │f   │  L           ││           │
# │f   │  mass        ││    	   │
# │f   │  dragFactor  ││           │
# │f   │  radius      ││           │
# │f   │  elasticity  ││           │
# │vect│  windVector  ││           │
# │f   │  windForce   ││           │
# +----+--------------++-----------+


# IMPORTS
import Rhino.Geometry as rg
from math import copysign, pi


if radius < 0.1:
	radius = 1

if mass < 0.1:
	mass = 10

if elasticity <= 0:
	elasticity = 1

# always unitize your vectors!
windVector.Unitize()


# -----------------------------------------------------------

# Check if the variables exists
if "position" not in globals() or reset:
	position = ptOrigin
	velocity = rg.Vector3d(0, 0, 0)
	force    = rg.Vector3d(0, 0, 0)
	GRAVITY  = rg.Vector3d(0, 0, -9.8)
	TIMEINTERVAL = 0.01
	RHO = 1.225    # Density of air/fluid, kg/m³

frontalArea = 2 * pi * radius**2    # (= half the area of the sphere)
dragFx = 0.5 * RHO * frontalArea * dragFactor

### Calculate drag
velocitySquared = rg.Vector3d(velocity.X**2, velocity.Y**2, velocity.Z**2)
drag = dragFx * velocitySquared
## Get the direction of the drag force (the opposite direction of the velocity)
direction = -1 * velocity
drag.X = copysign(drag.X, direction.X)
drag.Y = copysign(drag.Y, direction.Y)
drag.Z = copysign(drag.Z, direction.Z)

# Calculate weight (N)
WEIGHT = GRAVITY * mass

# vector from top to sphere
curLenVec = position - ptSpring
# length of that vector
curLen = curLenVec.Length
curLenVec.Unitize()
# deflection of the spring
deflection = L - curLen
springForce = k * deflection * curLenVec

# Calculate force
# the bigger the Fpot of the spring is (~deflection), the smaller the wind Force shall be
# this is a hack to fake the look
# TODO: next time better make a random * sin(timeInterval) func or therelike
wind = (windVector/abs(deflection)) * frontalArea * windForce
force = WEIGHT + drag + springForce + wind

# Acceleration A = F / m (second law of Newton)
acceleration = force / mass

# Update velocity
velocity += acceleration * TIMEINTERVAL

# Update position
translation = rg.Transform.Translation(velocity)
position.Transform(translation)

# Check for floor (should bounce here)
if position.Z < radius:
	position.Z = radius
	# object loses velocity on impact
	velocity.Z *= -elasticity

# Update sphere
sphere = rg.Sphere(position, radius)

# Print values
print("drag   : {}".format(drag.Length))
print("force  : {}".format(force.Length))
print("acc    : {}".format(acceleration.Length))
print("vel    : {}".format(velocity.Length))
print("wind   : {}".format(wind.Length))

# -----------------------------------------------------------
# Output
_pos = position
_sphere = sphere
