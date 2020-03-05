# Graphic screen manipulation using pgmagick

# See https://www.imagemagick.org/Magick++/Image++.html for C++ API which is
# directly exposed by the python module.

from __future__ import print_function, division
import os, sys
from pgmagick import *

# directory containing this module also contains needed fonts
__here__ = os.path.dirname(__file__) or '.'

# default font is monospaced
__font__ = __here__ + "/WenQuanYiMicroHeiMono.ttf"

# convert gravity string to gravity type
def _gravity(g):
    if type(g) is GravityType: return g
    return { "nw":          GravityType.NorthWestGravity,
             "northwest":   GravityType.NorthWestGravity,
             "n":           GravityType.NorthGravity,
             "north":       GravityType.NorthGravity,
             "ne":          GravityType.NorthEastGravity,
             "northeast":   GravityType.NorthEastGravity,
             "w":           GravityType.WestGravity,
             "west":        GravityType.WestGravity,
             "c":           GravityType.CenterGravity,
             "center":      GravityType.CenterGravity,
             "e":           GravityType.EastGravity,
             "east":        GravityType.EastGravity,
             "sw":          GravityType.SouthWestGravity,
             "southwest":   GravityType.SouthWestGravity,
             "s":           GravityType.SouthGravity,
             "south":       GravityType.SouthGravity,
             "se":          GravityType.SouthEastGravity,
             "southeast":   GravityType.SouthEastGravity }[g.lower()]

class screen():

    def __init__(
            self,
            width, height,              # screen size
            bg="black", fg="white",     # default colors
            rgb=None                    # initialize with raw rgb data (must be width*height*3 bytes)
        ):

        self.width = width
        self.height = height
        self.fg = fg
        self.bg = bg

        if rgb:
            self.image = Image(Blob(rgb), Geometry(width, height), 8, "RGB")
        else:
            self.image = Image(Geometry(width, height), Color(bg))

    # A bounding box is list of  [left, top, right, bottom], each specified
    # as fraction of the relevant screen dimension if <= 1 , or as an absolute
    # coordinate if > 1. Parse the box for current image, make sure x2,y2 is
    # southeast of x1,y1 and return (left, top, width, height)
    def box(self, l, t, r, b):
        x1 = l if l > 1 else self.width * l
        y1 = t if t > 1 else self.height * t
        x2 = r if r > 1 else self.width * r
        y2 = b if b > 1 else self.height * b
        assert x1 < x2 and y1 < y2
        return (int(x1), int(y1), int(x2-x1+1), int(y2-y1+1))

    # Merge an image onto screen at specified (x,y) offset or gravity
    def merge(self, image, offset=(0,0)):
        if type(offset) in [list, tuple]:
            offset = Geometry(0,0,offset[0],offset[1]) # see http://www.graphicsmagick.org/Magick++/Geometry.html
        else:
            offset = _gravity(offset)
        self.image.composite(image, offset, CompositeOperator.OverCompositeOp)

    # Add screen border of specified width
    def border(self, width, color=None):
        self.image.strokeWidth(width)
        self.image.strokeColor(color or self.fg)
        self.image.fillColor("transparent")
        self.image.draw(DrawableRectangle(0, 0, self.width-1, self.height-1))

    # Write arbitrary text to the screen
    def text(
            self,
            text,                           # text to be written, may contain tabs and linefeeds.
            left = 0, top = 0,              # offset of the text box on the screen
            width = None, height = None,    # text box size
            box = None,                     # alternative way of defining left, top, width and height, see box()
            gravity = 'northwest',          # gravity (text pulls in that direction)
            wrap = False,                   # wrap long lines to fit
            clip = True,                    # clip text to fit frame (False will render partial characters)
            point = 20,                     # pointsize
            fg = None,                      # text color, default to self.fg
            bg = "transparent",             # background color
            font = __font__                 # font
        ):

        # convert text to list of lines
        text=[s.expandtabs() for s in text.splitlines()]

        if box:
            left, top, width, height = self.box(*box)
        else:
            if height is None: height is self.height
            if width is None: width is self.width

        gravity = _gravity(gravity)

        # create the text layer
        layer = Image(Geometry(width, height), Color(bg))
        layer.strokeWidth(0)
        layer.fillColor(fg or self.fg)
        layer.font(font)
        layer.fontPointsize(point)
        tm = TypeMetric()
        layer.fontTypeMetrics("M",tm)

        # the y offset is based on font and gravity
        if gravity in (GravityType.NorthWestGravity, GravityType.NorthGravity, GravityType.NorthEastGravity):
            yoffset = tm.ascent()
        elif gravity in (GravityType.SouthWestGravity, GravityType.SouthGravity, GravityType.SouthEastGravity):
            yoffset = -tm.descent()
        else: yoffset=0

        maxcols = int(width // tm.textWidth())
        maxlines = int(height // (tm.textHeight()+1))

        if wrap:
            # wrap text to fit... this fails for characters wider than the font's 'M'
            def wrapt(t):
                t = t.rstrip(' ')
                while len(t) > maxcols:
                    i = t[:maxcols].rfind(' ')
                    if (i < 0):
                        yield t[:maxcols]
                        t = t[maxcols:]
                    else:
                        yield t[:i]
                        t = t[i+1:]
                    t = t.rstrip(' ')
                yield t
            text = [w for t in text for w in wrapt(t)]

        if clip:
            text = text[:maxlines]
            text = [s[:maxcols] for s in text] # does nothing if wrapped

        if text:
            # Ok, render text. XXX can this be done with Image.annotate()?
            d = DrawableList()
            d.append(DrawableGravity(gravity))
            d.append(DrawableText(0, yoffset, '\n'.join(text)))
            layer.draw(d)

            self.merge(layer, (left, top))

    # Return screen raw RGB data
    def rgb(self):
        blob = Blob()
        self.image.write(blob, "RGB", 8)
        return blob.data
