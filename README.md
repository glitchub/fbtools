Frame buffer manipulation tools for linux.

This requires the python2 pgmagick package (obtained via 'apt install
python-pgmagick', 'pip install pgmagick', etc).

Before use you must 'make' the framebuffer binary fb.bin which handles bulk
copying of RGB data to the frame buffer (python is much too slow for that).

fb.bin and fb.py must be located in the same directory as the various fb*
scripts.
