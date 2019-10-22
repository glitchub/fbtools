#!/usr/bin/python2

from __future__ import print_function
import os
from pgmagick import *
from fb import framebuffer

__here__ = os.path.dirname(__file__) or '.'

# Display arbitrary text in frame buffer, see the fbtext utility for more
# information
def fbtext(text, bg=None, fg=None, gravity='nw',point=20,
           font=__here__+'/WenQuanYiMicroHeiMono.ttf',
           device='/dev/fb0', margin=10, border=0, wrap=False,
           xtrim=False, ytrim=False, debug=False, reference='M'):

    if type(text) is str: text=[text]

    fb = framebuffer(device)
    if debug: print("frame buffer height=%d width=%d" % (fb.height, fb.width))

    # create surface
    im = Image(Geometry(fb.width,fb.height),Color(bg or "black"))
    im.fillColor(Color(fg or "white"))
    im.strokeWidth(0)
    im.font(font)
    im.fontPointsize(point)

    if border == 1:
        im.draw(DrawableLine(0, 0, fb.width-1, 0)) # across the top
        im.draw(DrawableLine(0, 0, 0, fb.height-1)) # down the left
        im.draw(DrawableLine(fb.width-1, 0, fb.width-1, fb.height-1)) # down the right
        im.draw(DrawableLine(0, fb.height-1, fb.width-1, fb.height-1)) # across the bottom
    elif border > 0:
        im.draw(DrawableRectangle(0, 0, fb.width-1, border-1)) # across the top
        im.draw(DrawableRectangle(0, 0, border-1, fb.height-1)) # down the left
        im.draw(DrawableRectangle(fb.width-border, 0, fb.width-1, fb.height-1)) # down the right
        im.draw(DrawableRectangle(0, fb.height-border, fb.width-1, fb.height-1)) # across the bottom

    margin += border

    # get font infp
    tm = TypeMetric()
    im.fontTypeMetrics(reference,tm)
    if debug:
        print("reference char '%s': ascent=%d descent=%d textheight=%d textwidth=%d maxadvance=%d" %
            (reference, tm.ascent(),tm.descent(),tm.textHeight(),tm.textWidth(), tm.maxHorizontalAdvance()))

    # x and y margins are based on gravity
    if gravity in ("nw","ne","w","e","sw","se"):
        xoffset = margin
    else:
        xoffset = 0

    if gravity in ("nw","n","ne"):
        yoffset = margin+tm.ascent()
    elif gravity in ("sw","s","se"):
        yoffset = margin+(-tm.descent())
    else:
        yoffset=0

    maxcols = int((fb.width-(margin*2))/tm.textWidth())
    maxlines = int((fb.height-(margin*2))/(tm.textHeight()+1))
    if debug: print("xoffset=%d yoffset=%d maxcols=%d maxlines=%d" % (xoffset, yoffset, maxcols, maxlines))

    if wrap:
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

    if ytrim:
        text = text[:maxlines]

    if xtrim:
        text = map(lambda s:s[:maxcols],text)

    if debug: print('\n'.join(text))

    dl = DrawableList()
    dl.append(DrawableGravity({"nw": GravityType.NorthWestGravity,
                               "n":  GravityType.NorthGravity,
                               "ne": GravityType.NorthEastGravity,
                               "w":  GravityType.WestGravity,
                               "c":  GravityType.CenterGravity,
                               "e":  GravityType.EastGravity,
                               "sw": GravityType.SouthWestGravity,
                               "s":  GravityType.SouthGravity,
                               "se": GravityType.SouthEastGravity}[gravity]))
    dl.append(DrawableText(xoffset, yoffset, '\n'.join(text).encode("utf8")))
    im.draw(dl)

    blob = Blob()
    im.write(blob,"RGB",8)
    fb.pack(blob.data)
