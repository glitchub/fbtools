# Frame buffer graphics manipulation using PIL
import os, sys, re, fb, PIL.Image as Image, PIL.ImageFont as Font, PIL.ImageDraw as Draw

# directory containing this module contains needed fonts
_here = os.path.dirname(__file__) or '.'

class Color():
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
        if type(color) is Color: return color   # already a Color, just return it
        return super().__new__(this)            # otherwise return new object

    def __init__(self, color, alpha=255):
        if type(color) is Color: return         # already a Color, do nothing
        color = (color or "black").lower()
        if color == "transparent": color = "black00"
        if re.match('^[a-z]+\d{2}$', color):
            # eg blue53 is blue with 53% alph
            alpha = int(255 * (int(color[-2:]) / 100))
            color = color[:-2]
        if color in self._colors:
            self.red, self.green, self.blue = self._colors[color]
            self.alpha = alpha
        elif re.match('^#[0-9a-f]{3,4,6,8}$', color):
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

    # return various tuples for use with PIL
    @property
    def rgb(self): return (self.red, self.green, self.blue)

    @property
    def rgba(self): return (self.red, self.green, self.blue, self.alpha)

    @property
    def rgbx(self): return (self.red, self.green, self.blue, 255)

class Align():
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
                    key = c if c is not " " else None
                    value=""
                else:
                    if key: value += c
            got[key]=value

        self.point = int(got.get('=',0))
        if self.point:
            self.columns = self.min = self.max = self.all = self.slash = None
        else:
            self.columns = int(got.get('+',0))
            self.min = int(got.get('>',0))
            self.max = int(got.get('<',0))
            self.entire = '!' in got
            self.slash = '/' in got
        self.align = Align(got.get('@','center'))

# An image layer
class Layer():

    @property
    def width(self): return self.right-self.left+1

    @property
    def height(self): return self.bottom-self.top+1

    # Create layer, note coordinates are relative to the parent layer.
    def __init__(self, parent=None, left=None, top=None, right=None, bottom=None, fg=None, bg=None, font=None, style=None, border=None):
        self.parent = parent    # the parent layer
        self.left = int(left)
        self.top = int(top)
        self.right = int(right)
        self.bottom = int(bottom)
        if not (0 <= self.left < self.right and 0 <= self.top < self. bottom):
            raise Exception("Invalid size left=%d top=%d right=%d bottom=%d" % (self.left, self.right, self.top, self.bottom))
        self.fg = Color(fg or "white")
        self.bg = Color(bg or "transparent")
        self.borderwidth = int(border or 0)
        self.font = font or _here+"/DejaVuSansMono.ttf"
        self.style = Style(style)
        self.img = Image.new("RGBA", (self.width, self.height), self.bg.rgba)
        self.border()

    # draw a border on the layer
    def border(self, width=None, color=None):
        if not width: width=self.borderwidth
        if width:
            color = Color(color or self.fg).rgba
            draw = Draw.Draw(self.img)
            draw.rectangle((0, 0, self.width-1, self.borderwidth-1), fill=color)                       # across the top
            draw.rectangle((0, 0, self.borderwidth-1, self.height-1), fill=color)                      # down the left
            draw.rectangle((self.width-self.borderwidth, 0, self.width-1, self.height-1), fill=color)  # down the right
            draw.rectangle((0, self.height-self.borderwidth, self.width-1, self.height-1), fill=color) # across the bottom
        return self

    # Clear this layer with specified or current background color (but without
    # transparency)
    def clear(self, color=None):
        self.img = Image.new("RGBA", (self.width, self.height), Color(color or self.bg).rgbx)
        return self

    # Merge this layer to parent, possibly recurse all the way to the screen layer
    def merge(self, recurse=True):
        if self.parent:
            self.parent.img.alpha_composite(self.img, (self.left, self.top))
            if recurse: self.parent.merge(recurse=True)
        return self

    # Normalize left, top, right, and bottom values relative to this layer.
    def normalize(self, left, top, right, bottom):
        # If fractional then they are percentage of this layer's width or
        # height.
        if not left: left=0
        elif -1 < left < 1: left *= self.width-1
        if not top: top=0
        elif -1 < top < 1: top *= self.height-1
        if not right: right=self.width-1
        elif -1 < right < 1: right *= self.width-1
        if not bottom: bottom=self.height-1
        elif -1 < bottom < 1: bottom *= self.height-1

        # If negative then they are offset from the this layer's right or
        # bottom.
        if left < 0: left += self.width-1
        if top < 0: top += self.height-1
        if right < 0: right += self.width-1
        if bottom < 0: bottom += self.height-1

        return int(left), int(top), int(right), int(bottom)

    # Create a child layer of this layer
    def child(self, left=0, top=0, right=0, bottom=0, fg=None, bg=None, font=None, style=None, border=None):
        left, top, right, bottom = self.normalize(left, top, right, bottom)
        return Layer(self, left=left, top=top, right=right, bottom=bottom,
                     fg=fg or self.fg, bg=bg or self.bg,
                     font=font or self.font, style=style or self.style,
                     border=border)

    # Create a sibling of this layer, i.e. by asking parent to create a child with same dimensions
    def sibling(self, fg=None, bg=None, font=None, style=None, border=None):
        return self.parent.child(left=self.left, top=self.top, right=self.right, bottom=self.bottom,
                                 fg=fg or self.fg, bg=bg or self.bg,
                                 font=font or self.font, style=style or self.style,
                                 border=border)

    # private method, wrap text list to width and return new list
    @staticmethod
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

    # Write arbitrary text to this layer
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
                        text = self._wrap(text, columns)
                else:
                    # find longest
                    columns = max(len(t) for t in text)

                # scale to number of columns
                point = (self.width // columns) * scalewidth

                # maybe scale to entire text
                if self.style.entire:
                    point = min(point, (self.height // len(text)) * scaleheight)

                # keep columns in min and max range
                if self.style.max: point = max(point, (self.width // self.style.max) * scalewidth)
                if self.style.min: point = min(point, (self.width // self.style.min) * scalewidth)

            # set the new point size, note it rounds down
            f = Font.truetype(font=self.font, size = int(point))
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
                    text = self._wrap(text, columns)

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
                elif self.style.align.east: xoff = self.width - f.getsize(l)[0]
                else: xoff = (self.width - f.getsize(l)[0]) // 2
                d.text((xoff, yoff), l, font = f, fill = self.fg.rgba)
                yoff += charheight  # next line

            self.merge()

        return self

    # Write in mage to this layer, can be an Image(), or a name of an image
    # file, or "-" to read formatted img data from stdin.  The image will be
    # scaled to fit on this layer, if stretch is True will fit exactly else
    # will be aligned as given (default centered).
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
        if img.width != self.width or img.height != self.height:
            if stretch:
                img = img.resize((self.width, self.height))
            else:
                aspect=min(self.width/img.width, self.height/img.height)
                img = img.resize((int(img.width * aspect), int(img.height * aspect)))

                align = Align(align)
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
        self.img.alpha_composite(img, (xoff, yoff))
        self.merge()
        return self

    # Return tuple of (left, top, right, bottom) for this layer, relative to the screen.
    # Note this function recurses.
    def box(self):
        if self.parent:
            left, top, _, _ = self.parent.box()
            left = left + self.left
            top = top + self.top
        else:
            left = self.left
            top = self.top
        return left, top, left+self.width-1, top+self.height-1

# All layers are children of the screen layer
class Screen(Layer):

    def __init__(
            self,
            fbdev = None,               # framebuffer device
            bg=None, fg=None,           # default colors
            font=None, style=None,      # default font and style
            border = None               # add border of given width
        ):

        self.fb = fb.Framebuffer(device=fbdev)
        super().__init__(None, left=0, top=0, right=self.fb.width-1, bottom=self.fb.height-1, fg=fg, bg=bg or "black", font=font, style=style, border=border)
        if self.bg.alpha != 255:
            # install existing framebuffer underneath non-opaque background
            i = Image.frombytes("RGB", (self.width, self.height), self.fb.unpack(), "raw", "RGB", 0, 1).convert("RGBA")
            i.alpha_composite(self.img)
            self.img = i

    # Write screen image to the framebuffer
    def display(self):
       self.fb.pack(self.img.convert("RGB").tobytes())
       return self
