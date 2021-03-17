# -----------------------------------------------------------
# Exercise 07: Image Sampling
# EDEK, University of Kassel
#
# (C) 2018 Lucas Becker
# Released under the Blue Oak Model License (BOML)
# -----------------------------------------------------------
__author__ = "Lucas Becker"
__version__ = "2018-12-16"

# Python Component I/Os
# +====+====== IN =========++=== OUT ====+
# │str │  FilePath         ││  _pts      │
# │f   │  gridSize         ││  _geom     │
# │bool│  resizeMethod     ││  _origCol  │
# │f   │  resRatio         ││  _newCol   │
# │int │  resFix           ││  _BCol_    │
# │int │  geomForm         ││            │
# │int │  sizeHSL          ││            │
# │int │ *fx_              ││            │
# │int │  ignore           ││            │
# │f   │  ignoreThreshold  ││            │
# +----+-------------------++------------+
# * = List Access  |  % = Tree Access


# IMPORTS
import Rhino.Geometry as rg
import rhinoscriptsyntax as rs
import ghpythonlib.treehelpers as th
import System, colorsys


# just to be sure
resFix = int(resFix)

# OUTPUT TREES and Constants
Pts, Geometry, ColorOrig, ColorHLS, ColorNew  = [], [], [], [], []
SIDES = [3, 4, 6, 8]

nFX = sum(fx_)

# -----------------------------------------------------------
def invert(clist):
    return [1-c for c in clist]


# -----------------------------------------------------------
# import image file
# `System` gives us the .Net classes
image = System.Drawing.Bitmap(FilePath)
origHeight = image.Height
origWidth  = image.Width

# resize image
if resizeMethod:    # == use Fixed pixel Size
    if origHeight == origWidth:
        image = System.Drawing.Bitmap(image, resFix, resFix)
    elif origHeight == min(origHeight, origWidth):
        resPar = round((origHeight / origWidth) * resFix)
        image = System.Drawing.Bitmap(image, resFix, resPar)
    else:
        resPar = round((origWidth / origHeight) * resFix)
        image = System.Drawing.Bitmap(image, resPar, resFix)
else:               # == use Ratio
    image = System.Drawing.Bitmap(image, round(origWidth*resRatio), round(origHeight*resRatio))


# get current image dimensions
height = image.Height
width  = image.Width

# -----------------------------------------------------------

# POINT GRID
#  + COLORS
# Beware: images are from top left corner!
h = 0
for hrev in reversed(range(height)):
    tPts, tColO, tColHLS, tColNew = [], [], [], []
    for j in range(width):

        tPts.append(rg.Point3d(j * gridSize, hrev * gridSize, 0))

        # get pixel color, RGB
        color = image.GetPixel(j, h)
        tColO.append(color)
        # Make conversion into HLS for easier calc (Hue Lightness Saturation)
        # HSL & HSV shouldn't actually be used due to their percepted non-uniformity
        # but for the moment this is sufficient (also because LAB color conversion is CPU intensive)

        # RGB needs to be in 0–1 domain
        color = map(lambda c: c/255, color)
        tColHLS.append(colorsys.rgb_to_hls(color[0], color[1], color[2]))

        curNCol = color
        #### FX ####
        if nFX >= 4:      # black and white
            curNCol = [ tColHLS[j][1], tColHLS[j][1], tColHLS[j][1] ]
            if nFX >= 6:  # invert colors
                curNCol = invert([curNCol[0], curNCol[1], curNCol[2]])

        elif nFX >=2:     # invert colors
            curNCol = invert([curNCol[0], curNCol[1], curNCol[2]])


        # back to 0–255 domain for rs.CreateColor()
        curNCol = map(lambda c: round(c*255), curNCol)

        # FINAL FX COLOR
        tColNew.append(rs.CreateColor( curNCol[0], curNCol[1], curNCol[2]))

    h+=1
    Pts.append(tPts)
    ColorOrig.append(tColO)
    ColorHLS.append(tColHLS)
    ColorNew.append(tColNew)


# -----------------------------------------------------------

for g in range(height):
    tGeo  = []
    for w in range(width):

        currentLit = ColorHLS[g][w][1] # Lightness
        currentSat = ColorHLS[g][w][2] # Saturation
        if currentSat == 0.0:   # if greyscale still get output
            currentSat = 0.5

        # DRAW GEOMETRY
        if (ignore > 1) & (currentLit > (1-ignoreThreshold)):  # ignore (near) white pixels
            tGeo.append(None)  # so we don't destroy the tree
        elif (ignore == 1) & (currentLit < (ignoreThreshold)):  # ignore (near) black pixels
            tGeo.append(None)
        else:
            # calculate size
            if sizeHSL == 2:        # size by saturation
                size = (gridSize/2) * currentSat
                nSides = int(round(3 * currentSat))
            elif sizeHSL == 1:      # size by darkness
                size = (gridSize/2) * (1-currentLit)
                size = (gridSize/2) * 0.1 if size == 0 else size    # avoid None type errors
                nSides = int(round(3 * (1-currentLit)))
            else:                   # size by lightness
                size = (gridSize/2) * currentLit
                nSides = int(round(3 * currentLit))

            if geomForm == 1:                    # CIRCLE
                tGeo.append( rg.Circle( Pts[g][w], size))
            elif geomForm == 4:                  # SQUARE
                tGeo.append(rg.Rectangle3d( rg.Plane(Pts[g][w], rg.Vector3d.ZAxis), rg.Interval(-size, size), rg.Interval(-size, size)))
            elif geomForm > 2 & geomForm != 4:    # POLYGON
                tGeo.append(rg.PolylineCurve( rg.Polyline.CreateInscribedPolygon( rg.Circle(Pts[g][w], size), geomForm)))
            else:                            # -1 # POLYGON BY SIZE
                tGeo.append(rg.PolylineCurve( rg.Polyline.CreateInscribedPolygon( rg.Circle(Pts[g][w], size), SIDES[nSides])))
    Geometry.append(tGeo)

# -----------------------------------------------------------
# OUTPUT
_pts     = th.list_to_tree(Pts)
_geom    = th.list_to_tree(Geometry)
_origCol = th.list_to_tree(ColorOrig)
_newCol  = th.list_to_tree(ColorNew)
_BCol_   = 0 if nFX == 1 else 1         # stream filter for coloring the geometry

