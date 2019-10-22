Frame buffer manipulation tools for linux.

Framebuffer depths 16 (565), 24 (RGB), and 32 (ARGB) are supported.

Run 'make' to build fbquery, fbget, and fbput executables, and fb.bin library
used by fb.py.

fbtext.py, fbimage.py, and fbclear.py require the pgmagick module (i.e.
obtained via 'apt install python-pgmagick', 'pip install pgmagick', etc). These
are modules, used by fbtext, fbimage, and fbclear respectively.

All scripts must be located in the same directory as fb.py and fb.bin.

fbput and fbquery can be used with Imagemagick/Graphicsmagick.

    Fill screen with a color:

        gm convert -size $(./fbquery) xc:blue -depth 8 RGB:- | ./fbput

    Fill screen with an image:

        gm convert image.jpg -resize $(./fbquery)! -depth 8 RGB:- | ./fbput

    Write an arbitrary text file to screen:

        gm convert -size $(./fbquery) xc:black -fill green -pointsize 20 -draw 'text 10,10 "@textfile" -depth 8 RGB: | ./fbput

The python scripts provide similar functionality with more smarts.

Run any script or program with -h option for details.
