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

class layer():

    @property
    def width(self): return self.right-self.left+1

    @property
    def height(self): return self.bottom-self.top+1

    # create layer, note coordinates are relative to the screen image and can't be used directly
    def __init__(self, left, top, right, bottom, fg, bg, image=None):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.fg = fg or "white"
        self.bg = bg or "transparent"
        self.img = Image(Geometry(self.width, self.height), Color(self.bg)) if image is None else image

    # Add a border of specified width and style
    def border(self, width, color):
        self.img.strokeWidth(width)
        self.img.strokeColor(color or self.fg)
        self.img.fillColor("transparent")
        self.img.draw(DrawableRectangle(0, 0, self.width-1, self.height-1))

    # Add "button pressed" border
    def pressed(self):
        self.img.strokeWidth(1)
        self.img.strokeColor("#444")
        self.img.draw(DrawableLine(0, 0, self.width-1, 0))
        self.img.draw(DrawableLine(0, 0, 0, self.height-1))
        self.img.strokeColor("#CCC")
        self.img.draw(DrawableLine(0, self.height-1, self.width-1, self.height-1))
        self.img.draw(DrawableLine(self.width-1, 0, self.width-1, self.height-1))

    # Add "button released" border
    def released(self):
        self.img.strokeWidth(1)
        self.img.strokeColor("#CCC")
        self.img.draw(DrawableLine(0, 0, self.width-1, 0))
        self.img.draw(DrawableLine(0, 0, 0, self.height-1))
        self.img.strokeColor("#444")
        self.img.draw(DrawableLine(0, self.height-1, self.width-1, self.height-1))
        self.img.draw(DrawableLine(self.width-1, 0, self.width-1, self.height-1))

    # return raw rgb image data
    def rgb(self):
        blob = Blob()
        self.img.write(blob, "RGB", 8)
        return blob.data

class screen(layer):

    def __init__(
            self,
            width, height,              # screen size
            bg="black", fg="white",     # default colors
        ):
        super().__init__(0, 0, width-1, height-1, fg, bg)

    # Given values for left, top, right, and bottom as percentages 0-100, return tuple of the actual left, top, right, and bottom coordinates
    # Note the percentages could be negative, left them play through
    def box(self, pleft, ptop, pright, pbottom):
        return (int(self.right * pleft / 100), int(self.bottom * ptop / 100), int(self.right * pright / 100), int(self.bottom * pbottom / 100))

    def border(self, width, color=None):
        super().border(width, color)

    # Merge layer onto screen
    def merge(self, l):
        g = Geometry(0, 0, l.left, l.top) # an offset, see http://www.graphicsmagick.org/Magick++/Geometry.html
        self.img.composite(l.img, g, CompositeOperator.OverCompositeOp)

    # Write arbitrary text to the screen
    # Returns the text layer for future use
    def text(
            self,
            text,                               # text to be written, may contain tabs and linefeeds.
            left=0, top=0, right=0, bottom=0,   # text box
            fg = None,                          # default text color
            bg = None,                          # default background color
            wrap = None,                        # wrap long lines to fit the box
            clip = None,                        # clip text to fit the box (False will render partial characters)
            gravity = None,                     # text gravity (in the box)
            font = None,                        # text font
            point = None,                       # text point size
            commit = True                       # If true, merge layer to screen
        ):

        if right <= 0: right += self.right
        if bottom <= 0: bottom += self.bottom

        # create the text layer
        l = layer(left, top, right, bottom, fg or self.fg, bg or "transparent")

        # convert text to list of lines
        text=[s.expandtabs() for s in text.splitlines()]

        l.img.strokeWidth(0)
        l.img.fillColor(l.fg)
        l.img.font(font or __font__)
        l.img.fontPointsize(point or 20)
        tm = TypeMetric()
        l.img.fontTypeMetrics("M",tm)

        # the y offset is based on font and gravity
        gravity = _gravity(gravity or "northwest")
        if gravity in (GravityType.NorthWestGravity, GravityType.NorthGravity, GravityType.NorthEastGravity):
            yoffset = tm.ascent()
        elif gravity in (GravityType.SouthWestGravity, GravityType.SouthGravity, GravityType.SouthEastGravity):
            yoffset = -tm.descent()
        else: yoffset=0

        maxcols = int(l.width // tm.textWidth())
        maxlines = int(l.height // (tm.textHeight()+1))

        if wrap in (None, True):
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

        if clip in (None, True):
            text = text[:maxlines]
            text = [s[:maxcols] for s in text] # does nothing if wrapped

        if text:
            # Ok, render text. XXX can this be done with Image.annotate()?
            d = DrawableList()
            d.append(DrawableGravity(gravity))
            d.append(DrawableText(0, yoffset, '\n'.join(text)))
            l.img.draw(d)

        if commit: self.merge(l)

        return l

    # Place an image on the screen
    # If rgb is defined, load raw rgb, which must be width*height*3 bytes (for use with framebuffer.rgb())
    # Else if name is defined, load image file (or read it from stdin if "-"). Image can be stretched to fit.
    # Else create an image of specified bg color
    # Returns the image layer for future use
    def image(
            self,
            left = 0, top = 0, right = 0, bottom = 0,   # box
            rgb = None,                                 # Load RGB data (instead of file)
            file = None,                                # Load image file or "-" if rgb is not given
            bg = None,                                  # use background color if file not given
            stretch = None,                             # stretch image to fit box
            gravity = None,                             # align image if not stretched
            commit = True                               # If true, return layer to caller, do not merge
            ):

        if right <= 0: right += self.right
        if bottom <= 0: bottom += self.bottom

        width = right - left + 1
        height = bottom - top + 1

        bg = bg or self.bg
        stretch = stretch or False

        if rgb:
            l = layer(top, left, right, bottom, None, bg, image = Image(Blob(rgb), Geometry(width, height), 8, "RGB"))
        elif file:
            if file == '-':
                img = Image(Blob(sys.stdin.buffer.read()))
            else:
                img = Image(file)

            # scale to desired size
            g = Geometry(width, height)
            if stretch:
                g.aspect(True)
                img.scale(g)
                l = layer(top, left, right, bottom, None, bg, image = img)
            else:
                img.scale(g)
                l = layer(top, left, right, bottom, None, bg)
                l.img.composite(img, _gravity(gravity or "center"), CompositeOperator.OverCompositeOp)
        else:
            # just use the background color
            l = layer(top, left, right, bottom, None, bg)

        if commit: self.merge(l)

        return l

    # Return screen raw RGB data, for use with framnebuffer.pack()
    def rgb(self):
        return super().rgb()
