// query frame buffer size
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include "fb.h"

#define warn(...) fprintf(stderr,__VA_ARGS__)
#define die(...) warn(__VA_ARGS__), exit(1)

static void usage(void)
{
    die("Usage:\n\
\n\
    fbquery [options]\n\
\n\
Write frame buffer dimension to stdout in form\"WIDTHxHEIGHT\" (in pixels)\n\
\n\
Options are:\n\
\n\
    -d  - frame buffer device, default is \"/dev/fb0\"\n\
    -v  - verbose info\n\
"   );
}

int main(int argc, char **argv)
{
    char *device="/dev/fb0";
    bool verbose=false;
    struct fbinfo fb;

    while (1) switch (getopt(argc,argv,":d:v"))
    {
        case 'd': device=optarg; break;
        case 'v': verbose=true; break;
        case ':':            // missing
        case '?': usage();   // or invalid options
        case -1: goto optx;  // no more options
    } optx:

    if (optind < argc) usage();

    if (fbopen(&fb, device) == 1) die("Failed to open %s: %s\n", device, strerror(errno));

    if (!verbose)
        printf("%dx%d\n", fb.width, fb.height);
    else
        printf("Width:       %d\n"
               "Height:      %d\n"
               "Bytes/pixel: %d\n"
               "Red shift:   %d\n"
               "Green shift: %d\n"
               "Blue shift:  %d\n",
               fb.width, fb.height,
               fb.bpp,
               fb.red,
               fb.green,
               fb.blue);
}
