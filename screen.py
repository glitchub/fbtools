# Frame buffer graphics manipulation using PIL
import os, sys, re, PIL.Image as Image, PIL.ImageFont as Font, PIL.ImageDraw as Draw

try:
    import fb               # works if fbtools is in the path
except ImportError:
    from fbtools import fb  # works if fbtools is a package

# directory containing this module contains needed fonts
_here = os.path.dirname(__file__) or '.'

# wrap text to specified width
def _wrap(text, width):
    def _wl(line):
        line = line.rstrip(' ') # retain left white-space
        while len(line) > width:
            i = line[:width].rfind(' ')
            if (i < 0):
                yield line[:width].rstrip(' ')
                line = line[width:].lstrip(' ')
            else:
                yield line[:i].rstrip(' ')
                line = line[i+1:].lstrip(' ')
        yield line
    return [w.rstrip(' ') for line in text for w in _wl(line)]

class _Color():
    _colors = {
        # https://en.wikipedia.org/wiki/Web_colors
        "white"     : (255, 255, 255),
        "silver"    : (192, 192, 192),
        "gray"      : (128, 128, 128),
        "grey"      : (128, 128, 128), # alias for gray
        "black"     : (0, 0, 0),
        "red"       : (255, 0, 0),
        "maroon"    : (128, 0, 0),
        "yellow"    : (255, 255, 0),
        "olive"     : (128, 128, 0),
        "lime"      : (0, 255, 0),
        "green"     : (0, 128, 0),
        "aqua"      : (0, 255, 255),
        "teal"      : (0, 128, 128),
        "blue"      : (0, 0, 255),
        "navy"      : (0, 0, 128),
        "fuschia"   : (255, 0, 255),
        "purple"    : (128, 0, 128)
    }

    def __new__(this, color, **kwargs):
        if type(color) is _Color: return color   # already a _Color, just return it
        return super().__new__(this)            # otherwise return new object

    def __init__(self, color, alpha=255):
        if type(color) is _Color: return         # already a _Color, do nothing
        color = (color or "black").lower()
        if color == "transparent": color = "black00"
        if re.match('^[a-z]+\d{2}$', color):
            # eg blue53 is blue with 53% alph
            alpha = int(255 * (int(color[-2:]) / 100))
            color = color[:-2]
        if color in self._colors:
            self.red, self.green, self.blue = self._colors[color]
            self.alpha = alpha
        elif len(color) in [4,5,7,9] and re.match('^#[0-9a-f]+$', color):
            if len(color) <= 5:
                # #RGB or #RGBA
                self.red = int(color[1],16) * 17
                self.green = int(color[2],16) * 17
                self.blue = int(color[3],16) * 17
                self.alpha = alpha if len(color) == 4 else int(color[4],16) * 17
            else:
                # #RRGGBB or #RRGGBBAA
                self.red = int(color[1:3], 16)
                self.green = int(color[3:5], 16)
                self.blue = int(color[5:7], 16)
                self.alpha = alpha if len(color) == 7 else int(color[7:9],16)
        else:
            raise Exception("Invalid color '%s'" % color)

    # true if color is transparent
    @property
    def transparent(self): return self.alpha != 255

    # return various tuples for use with PIL
    @property
    def rgb(self): return (self.red, self.green, self.blue)

    @property
    def rgba(self): return (self.red, self.green, self.blue, self.alpha)

    @property
    def rgbx(self): return (self.red, self.green, self.blue, 255)

class _Align():
    _west = 1
    _north = 2
    _east = 4
    _south = 8
    _align = { "nw":          _north|_west,
               "northwest":   _north|_west,
               "n":           _north,
               "north":       _north,
               "ne":          _north|_east,
               "northeast":   _north|_east,
               "w":           _west,
               "west":        _west,
               "c":           0,
               "center":      0,
               "e":           _east,
               "east":        _east,
               "sw":          _south|_west,
               "southwest":   _south|_west,
               "s":           _south,
               "south":       _south,
               "se":          _south|_east,
               "southeast":   _south|_east }

    def __init__(self, align):
        if align is None:
            a = 0 # center
        else:
            try:
                a = int(align)
            except:
                a = self._align.get(align.lower(),None)
            if a not in self._align.values(): raise Exception("Invalid alignment '%s'" % str(align))

        self.west   = bool(a & self._west)
        self.north  = bool(a & self._north)
        self.east   = bool(a & self._east)
        self.south  = bool(a & self._south)

class Style():
    def __new__(this, style):
        if type(style) is Style: return style   # already a Style, just return it
        return super().__new__(this)            # otherwise return new object

    def __init__(self, style):
        if type(style) is Style: return         # already a Style, do nothing
        # Parse font style string, containing:
        #   =NN    -> set specific point size (default 0, no point)
        #   [+]NN  -> wrap text to NN columns, scale to longest line (default 0, don't actually wrap)
        #   !      -> scale text to show all lines
        #   >NN    -> minimum required columns (default 0, no minimum)
        #   <NN    -> maximum allowed columns (default 0, no maximum)
        #   @aa    -> alignment (default "center")
        #   /      -> slash long lines (i.e. don't wrap), default False
        got={}
        if style:
            style=str(style)
            key = "+" if style[0].isdigit() else None
            value=""
            for c in list(style):
                if c in "=+!<>/@ ":
                    if key: got[key]=value
                    key = None
                    if c in "!/": got[c] = True
                    elif c is not " ": key = c
                    value=""
                elif key: value += c
                else: raise Exception("Unexpected character '%s' in style" % c)
            if key: got[key]=value

        self.point = self.columns = self.min = self.max = self.all = self.slash = None
        if '=' in got:
            self.point = int(got['='])
            assert self.point > 0
        else:
            self.columns = int(got.get('+',0) or '0')
            assert self.columns >= 0
            self.min = int(got.get('>',0))
            assert self.min >= 0
            self.max = int(got.get('<',0))
            assert self.min >= 0
            self.entire = '!' in got
            self.slash = '/' in got
        self.align = _Align(got.get('@','center'))

# An image layer, the class is not exposed by the methods are
class _Layer():

    @property
    def width(self): return self.right-self.left+1

    @property
    def height(self): return self.bottom-self.top+1

    @property
    def size(self): return self.width, self.height

    # true if fg or bg is transparent
    @property
    def transparent(self): return self.fg.transparent or self.bg.transparent

    # Create layer, note coordinates are relative to the parent layer, and must be constrained within it
    def __init__(self, parent=None, left=None, top=None, right=None, bottom=None, fg=None, bg=None, font=None, style=None, border=None):
        self.left = int(left)
        self.top = int(top)
        self.right = int(right)
        self.bottom = int(bottom)
        self.parent = parent    # remember parent
        if self.parent:
            assert 0 <= self.left <= self.right < self.parent.width and 0 <= self.top <= self.bottom < self.parent.height
            # track absolute coordinates on the screen layer
            self.abs_left = self.parent.abs_left + self.left
            self.abs_top = self.parent.abs_top + self.top
        else:
            # left and top must be 0, and right and bottom are presumably the size of the framebuffer
            assert 0 == self.left <= self.right and 0 == self.top <= self.bottom
            self.abs_left = 0
            self.abs_top = 0
        self.fg = _Color(fg or "white")
        self.bg = _Color(bg or "transparent")
        self.borderwidth = int(border or 0)
        self.font = font or _here+"/DejaVuSansMono.ttf"
        self.style = Style(style)
        self.img = Image.new("RGBA", self.size, self.bg.rgba)
        self.border()
        self.children = []      # layer has no children
        self.updated = True     # layer has been updated

    # Normalize left, top, right, and bottom values relative to this layer.
    def _normalize(self, left, top, right, bottom):
        # If fractional then they are percentage of this layer's width or
        # height.
        if left is None: left=0
        elif -1 < left < 1: left *= self.width-1
        if top is None: top=0
        elif -1 < top < 1: top *= self.height-1
        if right is None: right=self.width-1
        elif -1 < right < 1: right *= self.width-1
        if bottom is None: bottom=self.height-1
        elif -1 < bottom < 1: bottom *= self.height-1

        # If negative then they are offset from the this layer's right or
        # bottom.
        if left < 0: left += self.width-1
        if top < 0: top += self.height-1
        if right < 0: right += self.width-1
        if bottom < 0: bottom += self.height-1

        return int(left), int(top), int(right), int(bottom)

    # overlay layer with image at designated offset
    def _overlay(self, img, left=0, top=0):
        assert left+img.width <= self.width and top+img.height <= self.height
        if img.size == self.size:
            self.img = Image.alpha_composite(self.img, img)
        else:
            pilbox = (left, top, left+img.width, top+img.height)
            self.img.paste(Image.alpha_composite(self.img.crop(pilbox), img), pilbox)
        self.updated = True

    # Return true if layer or any children are updated
    def _isupdated(self):
        if self.updated: return True
        for c in self.children:
            if c._isupdated():
                return True
        return False

    # Given an _Update object, recursively update it with current layer and/or children
    def _update(self, upd, force=False):
        if not force and not self.updated:
            # look for updateable children
            r = [c for c in self.children if c._isupdated()]
            if len(r) == 0: return None  # done if none
            if len(r) == 1 and not r[0].transparent: return r[0]._update(upd) # if exactly one and not transparent, update and return
        # Install this layer onto the surface
        upd._overlay(self)
        # Then recursively install all children
        for c in self.children: upd = c._update(upd, force=True)
        self.updated = False
        return upd

    # Create and return child layer of this layer
    def child(self, left=0, top=0, right=0, bottom=0, fg=None, bg=None, font=None, style=None, border=None):
        left, top, right, bottom = self._normalize(left, top, right, bottom)
        c = _Layer(self, left=left, top=top, right=right, bottom=bottom,
                   fg=fg or self.fg, bg=bg or self.bg,
                   font=font or self.font, style=style or self.style,
                   border=border)
        self.children.append(c) # remember it
        return c

    # Public method - remove layer and all children, must not subsequently be used
    def remove(self):
        self.img = None
        for c in self.children:         # recursively remove all children
            c.parent = None
            c.remove()
        self.children = []
        if self.parent:                 # then unlink from parent
            try:
                self.parent.children.remove(self)
            except ValueError:
                pass
            self.parent.updated = True   # parent should be updated
            self.parent = None          # last, dereference parent

    # Public method, draw a border on the layer
    def border(self, width=None, color=None):
        if not width: width = self.borderwidth
        if width and width < self.width and width < self.height:
            color = _Color(color or self.fg).rgba
            draw = Draw.Draw(self.img)
            draw.rectangle((0, 0, self.width-1, self.borderwidth-1), fill=color)                       # across the top
            draw.rectangle((0, 0, self.borderwidth-1, self.height-1), fill=color)                      # down the left
            draw.rectangle((self.width-self.borderwidth, 0, self.width-1, self.height-1), fill=color)  # down the right
            draw.rectangle((0, self.height-self.borderwidth, self.width-1, self.height-1), fill=color) # across the bottom
            self.updated = True
        return self

    # Public method, clear layer to specified or current background color.
    # Bckground transparency is ignored, all children are removed
    def clear(self, color=None):
        for c in list(self.children): c.remove()
        self.img = Image.new("RGBA", self.size, _Color(color or self.bg).rgbx)
        self.updated = True
        return self

    # Public mewthod, return tuple of (left, top, right, bottom) for this layer, relative to the screen.
    def box(self):
        return self.abs_left, self.abs_top, self.abs_left+self.width-1, self.abs_top+self.height-1

    # Public method, write arbitrary text to this layer, using the layer's alignment
    def text(self, text):
        # Convert text escapes eg '\n' to corresponding controls
        text=(text or '').encode("raw_unicode_escape").decode("unicode_escape")
        # Split into lines, expand tabs, delete all other controls
        text=[''.join(c for c in s.expandtabs() if c.isprintable()).rstrip(' ') for s in text.splitlines()]

        if text:
            if self.style.point:
                # use exact point size
                point = self.style.point
            else:
                # Try to determine font's pixels-per-point, this fails
                # miserably if font is not monospaced.
                f = Font.truetype(font=self.font, size=2048)
                scalewidth=2048/f.getsize(" ")[0] # meh
                scaleheight=2048/f.font.height

                if self.style.columns:
                    columns = self.style.columns
                    # slash or wrap as required
                    if self.style.slash:
                        text = [s[:columns].rstrip(' ') for s in text]
                    else:
                        text = _wrap(text, columns)
                else:
                    # find longest
                    columns = max(len(t) for t in text)

                # scale to number of columns
                point = (self.width / columns) * scalewidth

                # maybe scale to entire text
                if self.style.entire:
                    point = min(point, (self.height / len(text)) * scaleheight)

                # keep columns in min and max range
                if self.style.max: point = max(point, (self.width / self.style.max) * scalewidth)
                if self.style.min: point = min(point, (self.width / self.style.min) * scalewidth)

            # set the new point size, note it rounds down
            f = Font.truetype(font=self.font, size = int(point) or 1)
            charwidth = f.getsize(" ")[0] # meaningless for proportional fonts
            charheight = f.font.height

            # get actual columns and rows, but at least one to allow partial display if necessary
            columns = (self.width // charwidth) or 1
            lines = (self.height // charheight) or 1

            # enforce style limits
            if self.style.columns: columns = min(columns, self.style.columns)
            if self.style.max:
                columns = min(columns, self.style.max)
                # slash or wrap as required
                if self.style.slash:
                    text = [s[:columns].rstrip(' ') for s in text]
                else:
                    text = _wrap(text, columns)

            # discard extra lines
            text = text[:lines]

            # align first line vertical
            if self.style.align.north: yoff = 0
            elif self.style.align.south: yoff = self.height - (charheight * len(text))
            else: yoff = (self.height - (charheight * len(text))) // 2

            d = Draw.Draw(self.img)
            for l in text:
                # align horizontal
                if self.style.align.west: xoff = 0
                elif self.style.align.east: xoff = self.width - f.getsize(l)[0] + 1
                else: xoff = (self.width - f.getsize(l)[0] + 1) // 2
                d.text((xoff, yoff), l, font = f, fill = self.fg.rgba)
                yoff += charheight  # next line

            self.updated = True # screen update required

        return self

    # Piblic method, write an image to this layer
    # Argument can be a PIL Image, or a name of an image file, or "-" to read
    # formatted img data from stdin.  The image will be scaled to fit on this
    # layer, if stretch is True will fit exactly else will be aligned as given
    # (default centered).
    def image(self, img, align=None, stretch=None):

        if type(img) is Image:
           # clone the image
           img = img.copy()
        elif img == "-":
           # read image from stdin
           img = Image.open(sys.stdin.buffer)
        else:
           # read image from file
           img = Image.open(img)
        if img.mode != "RGBA": img = img.convert("RGBA")

        # resize as required
        xoff = yoff = 0
        if img.size != self.size:
            if stretch:
                img = img.resize(self.size)
            else:
                aspect=min(self.width/img.width, self.height/img.height)
                img = img.resize((int(img.width * aspect), int(img.height * aspect)))

                align = _Align(align)
                if align.north:
                    yoff = 0
                elif align.south:
                    yoff = self.height - img.height
                else:
                    yoff = (self.height - img.height) // 2

                if align.west:
                    xoff = 0
                elif align.east:
                    xoff = self.width - img.width
                else:
                    xoff = (self.width - img.width) // 2
        self._overlay(img, xoff, yoff)
        return self

# Created by Screen.update() and passed to layer._update(), aggregate layers for display
class _Update():
    def __init__(self, screen):
        assert type(screen) is Screen
        self.screen = screen  # remember the screen layer
        self.img = None       # image to write
        self.box = None       # portion that is actually updated


    # overlay layer's image
    def _overlay(self, layer):
        if not self.box: self.box = layer.box() # remember the first layer that gets here
        if layer == self.screen:
            # copy the screen layer
            self.img = self.screen.img.copy()
        else:
            if not self.img: self.img = Image.new("RGBA", self.size, _Color("black").rgbx)
            if layer.size == self.screen.size:
                # just composite
                self.img = Image.alpha_composite(self.image, layer.img)
            else:
                # crop, composite, and paste
                pilbox = (layer.abs_left, layer.abs_top, layer.abs_left+layer.width, layer.abs_top+layer.height)
                self.img.paste(Image.alpha_composite(self.img.crop(pilbox), layer.img), pilbox)

    # write update image to frame buffer, if defined
    def _update(self):
        if self.img: self.creen.fb.pack(self.img.convert("RGB").tobytes(), *self.box)

# All layers are children of the screen layer
class Screen(_Layer):

    def __init__(
            self,
            fbdev = None,               # framebuffer device
            bg=None, fg=None,           # default colors
            font=None, style=None,      # default font and style
            border = None               # add border of given width
        ):

        self.fb = fb.Framebuffer(device=fbdev)
        super().__init__(None, left=0, top=0, right=self.fb.width-1, bottom=self.fb.height-1, fg=fg, bg=bg or "black", font=font, style=style, border=border)
        if self.bg.transparent:
            # install existing framebuffer underneath non-opaque background
            i = self.img
            self.img = Image.frombytes("RGB", self.size, self.fb.unpack(), "raw", "RGB", 0, 1).convert("RGBA")
            self._overlay(i)

    # prevent remove()
    def remove(self):
        raise RuntimeError("Can't remove the screen layer!")

    # Update screen if changed or forced
    def update(self, force=False):
        u = _Update(self)           # create the update surface
        u = self._update(u, force)  # recursively install each layer
        u._update()                 # write to the screen
        return self
