#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/types.h>

#include "fb.h"

#define warn(...) fprintf(stderr,__VA_ARGS__)
#define die(...) warn(__VA_ARGS__), exit(1)

static void usage(void)
{
    die("Usage:\n\
\n\
    fbget [options]\n\
\n\
Dump raw 24-bit RGB data from framebuffer to stdout.\n\
\n\
Options are:\n\
\n\
    -d path   - frame buffer device, default is \"/dev/fb0\"\n\
");
}

int main(int argc, char **argv)
{
    char *device="/dev/fb0";
    struct fbinfo fb;

    while (1) switch (getopt(argc,argv,":d:"))
    {
        case 'd': device=optarg; break;
        case ':':            // missing
        case '?': usage();   // or invalid options
        case -1: goto optx;  // no more options
    } optx:
    if (optind < argc) usage();

    if (fbopen(&fb, device)) die("Failed to open framebuffer %S: %s\n", device, strerror(errno));

    uint8_t RGB[fb.width*3]; 
    for (int line=0; line < fb.height; line++)
    {
        if (fbunpack(&fb, fb.width, fb.width*line, RGB)) die("Can't read %d pixels from framebuffer line %d\n", fb.width, line);
        if (fwrite(RGB, 3, fb.width, stdout) != fb.width) die("Can't write %d pixels to stdout\n", fb.width);
    }
}
