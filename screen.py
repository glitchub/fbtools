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
        ):

        self.width = width
        self.height = height
        self.fg = fg
        self.bg = bg

        # create the base image
        self.base = Image(Geometry(width, height), Color(bg))

    @property
    def right(self):
        return self.width-1

    @property
    def bottom(self):
        return self.height-1

    # Given values for left, top, right, and bottom as percentages 0-100, return the actual left, top, right, and bottom coordinates
    def box(self, l, t, r, b):
        return int(self.right * l / 100), int(self.bottom * t / 100), int(self.right * r / 100), int(self.bottom * b / 100)

    # Merge an img onto base at specified (x,y) offset or gravity
    def merge(self, img, left, top):
        g = Geometry(0,0,left,top) # see http://www.graphicsmagick.org/Magick++/Geometry.html
        self.base.composite(img, g, CompositeOperator.OverCompositeOp)

    # Add screen border of specified width
    def border(self, width, color=None):
        self.base.strokeWidth(width)
        self.base.strokeColor(color or self.fg)
        self.base.fillColor("transparent")
        self.base.draw(DrawableRectangle(0, 0, self.right, self.bottom))

    # Write arbitrary text to the screen
    def text(
            self,
            text,                           # text to be written, may contain tabs and linefeeds.
            left = 0, top = 0,              # text box
            right = 0, bottom = 0,
            gravity = 'northwest',          # text gravity (in the box)
            wrap = False,                   # wrap long lines to fit the box
            clip = True,                    # clip text to fit the box (False will render partial characters)
            point = 20,                     # text point size
            fg = None,                      # default text color, default to self.fg
            bg = "transparent",             # default background color
            font = __font__                 # text font
        ):

        # convert text to list of lines
        text=[s.expandtabs() for s in text.splitlines()]

        if right <= 0: right += self.right
        if bottom <= 0: bottom += self.bottom

        width = (right-left)+1
        height = (bottom-top)+1

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

            self.merge(layer, left, top)

    # Place an image on the screen
    # If rgb is defined, load raw rgb, which must be width*height*3 bytes (for use with framebuffer.rgb())
    # Else if name is defined, load image file (or read it from stdin if "-"). Image can be stretched to fit.
    # Else create an image of specified bg color
    def image(
            self,
            file = None,                    # Image file name or "-"
            left = 0, top = 0,              # Image box
            right = 0, bottom = 0,
            rgb = None,                     # Raw RGB data (instead of file)
            bg = "black",                   # default background color
            stretch = False                 # stretch image to fit box
            ):

        if right <= 0: right += self.right
        if bottom <= 0: bottom += self.bottom

        width = (right - left) + 1
        height = (bottom - top) + 1

        if rgb:
            img = Image(Blob(rgb), Geometry(width, height), 8, "RGB")
        elif file:
            if file == '-':
                img = Image(Blob(sys.stdin.buffer.read))
            else:
                img = Image(file)
            # scale to desired size
            g = Geometry(width, height)
            if stretch: g.aspect(True)
            img.scale(g)
        else:
            # just use the background color
            img=(Geometry(width, height), Color(bg))

        # place image on screen
        self.merge(img, left, top)

    # Return screen raw RGB data, for use with framnebuffer.pack()
    def rgb(self):
        blob = Blob()
        self.base.write(blob, "RGB", 8)
        return blob.data
