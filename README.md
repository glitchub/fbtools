Frame buffer manipulation tools

------

fbtext [options] text.file

Write arbitrary, possibly multi-line text to frame buffer. Options are:

    -b width                - screen border width, default is "0" (no border)
    -c [fg][:bg]            - foreground and background colors, default is "white:black"
    -d device               - framebuffer device, default is "/dev/fb0"
    -f path/to/font         - specify font, default is "WenQuanYiMicroHeiMono.ttf"
    -g direction            - text gravity, one of "nw", "n", "ne", "w", "c", "e", "sw", "s", or "se", default is "nw"
    -m                      - text margin in pixels, default is "10"
    -r char                 - reference character, default is "M"
    -s point                - font point size, default is "20"
    -w                      - wrap text to page width
    -x                      - trim text to page width
    -y                      - trim text to page height

Note -w, -x, and -y operations are based on size of reference character
specified by -r, best results are with a monospaced font.

If the text file name is '-' then read it from stdin.

------

fbimage [options] image.file

Decode an image file and output to frame buffer. 

Options are:

    -c color                - background color, default is "black"
    -d device               - framebuffer device, default is "/dev/fb0"
    -m width                - margin width, default is "0" (no margin)
    -s                      - stretch the image to fit, default is scale to fit.

If the image file name is '-' then read it from stdin.

------

fbclear [options]

Clear the frame buffer. 

Options are:

    -c color                - background color, default is "black"
    -d device               - framebuffer device, default is "/dev/fb0"

------

fbquery [options]

Print frame buffer size in format "WIDTHxHEIGHT". 

Options are:

    -d device               - framebuffer device, default is "/dev/fb0"

------

fbput [options] rawRGB.bin

Copy raw 24-bit RGB data from file to frame buffer. If file name is '-', copy
from stdin.

Options are:

    -d device               - framebuffer device, default is "/dev/fb0"

------
