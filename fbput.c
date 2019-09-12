#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <errno.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <fcntl.h>

#include "fb.h"

#define warn(...) fprintf(stderr,__VA_ARGS__)
#define die(...) warn(__VA_ARGS__), exit(1)

static void usage(void)
{
    die("Usage:\n\
\n\
    fbput [options]\n\
\n\
Write raw 24-bit RGB data from stdin to framebuffer.\n\
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

    for (int line=0; line < fb.width; line++)
    {
        uint8_t RGB[fb.width*3]; // one line
        int pixels = fread(&RGB, 3, fb.width, stdin);
        if (pixels == 0) return 0;
        if (pixels < 0) die("Input read failed: %s\n", strerror(errno));
        if (fbpack(&fb, pixels, fb.width*line, RGB)) die("Can't write %d pixels to framebuffer line %d\n", pixels, line);
    }
}
