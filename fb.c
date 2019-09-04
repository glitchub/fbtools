// Low-level support for framebuffer read/write, because python is waaaay too slow

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <linux/fb.h>

struct fbinfo
{
    uint32_t height,  // height must be first
             width,   // width must be second
             *mmap,   // the rest is private
             red,
             green,
             blue;
};

int fbopen(struct fbinfo *fb, char *device)
{
    int fd=open(device, O_RDWR);
    if (fd < 0) return 1;

    struct fb_var_screeninfo vsi;
    if (ioctl(fd, FBIOGET_VSCREENINFO, &vsi) < 0)
    {
        close(fd);
        return 2;
    }

    if (vsi.bits_per_pixel != 32 || vsi.red.length != 8 || vsi.green.length != 8 || vsi.blue.length != 8)
    {
        close(fd);
        return 3;
    }

    fb->height = vsi.yres_virtual;
    fb->width = vsi.xres_virtual;
    fb->red = vsi.red.offset;
    fb->green = vsi.green.offset;
    fb->blue = vsi.blue.offset;
    fb->mmap=mmap(NULL, vsi.xres_virtual * vsi.yres_virtual * 4, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (fb->mmap == MAP_FAILED) return 4;

    return 0;
}

// Unpack pixels from framebuffer pixel offset to raw rgb data and return 0.
// Return 1 if pixels+offset is out of range. *rgfb size must be pixels*3 bytes
int fbunpack(struct fbinfo *fb, uint32_t pixels, uint32_t offset, uint8_t *rgb)
{
    if (offset+pixels > fb->height*fb->width) return -1;

    while (pixels--)
    {
        uint32_t p = fb->mmap[offset++];
        *rgb++ = p >> fb->red;
        *rgb++ = p >> fb->green;
        *rgb++ = p >> fb->blue;
    }
    return 0;
}

// Pack pixels of raw rgb data to framebuffer specified pixel offset and return
// 0. Error ERANGE if pixels+offset out of range. *rgb must be pixels*3 bytes
// long.
int fbpack(struct fbinfo *fb, uint32_t pixels, uint32_t offset, uint8_t *rgb)
{
    if (offset+pixels > fb->height*fb->width) return -1;

    while (pixels--)
    {
        fb->mmap[offset++]=(rgb[0] << fb->red)+(rgb[1] << fb->green)+(rgb[2] << fb->blue);
        rgb += 3;
    }
    return 0;
}
