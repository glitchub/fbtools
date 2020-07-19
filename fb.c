// Framebuffer I/O, because pure python is waaaay too slow
#include <stdlib.h>
#include <stdint.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <errno.h>
#include <linux/fb.h>

struct fbinfo
{
    uint32_t height,    // height in pixels
             width,     // width in pixels
             bpp,       // bytes per pixel: 2, 3, or 4. If 2 bytes, then columnorspace is 565.
             red,       // red shift
             green,     // green shift
             blue;      // blue shift
    void   * mmap;      // pointer to frame buffer memory
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

    if (vsi.bits_per_pixel == 32 && vsi.red.length == 8 && vsi.green.length == 8 && vsi.blue.length == 8)
    {
        // ARGB
        fb->bpp=4;
    }
    else if (vsi.bits_per_pixel == 24 && vsi.red.length == 8 && vsi.green.length == 8 && vsi.blue.length == 8)
    {
        // RGB
        fb->bpp=3;
    }
    else if (vsi.bits_per_pixel == 16 && vsi.red.length == 5 && vsi.green.length == 6 && vsi.blue.length == 5)
    {
        // 565
        fb->bpp=2;
    } else
    {
        close(fd);
        return 3;
    }

    fb->height = vsi.yres_virtual;
    fb->width = vsi.xres_virtual;
    fb->red = vsi.red.offset;
    fb->green = vsi.green.offset;
    fb->blue = vsi.blue.offset;

    fb->mmap=mmap(NULL, vsi.xres_virtual * vsi.yres_virtual * fb->bpp, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);

    if (fb->mmap == MAP_FAILED)
    {
        return 4;
    }

    return 0;
}

// Unpack framebuffer to *rgb array, which must be fb->height*fb->width*3 bytes long
void fbunpack(struct fbinfo *fb, uint8_t *rgb)
{
    uint32_t pixels = fb->width * fb->height;
    switch(fb->bpp)
    {
        case 2:
        {
            uint16_t *p = fb->mmap;
            while (pixels--)
            {
                uint16_t n = *p++;
                *rgb++ = (n >> fb->red) << 3;
                *rgb++ = (n >> fb->green) << 2;
                *rgb++ = (n >> fb->blue) << 3;
            }
            break;
        }
        case 3:
        {
            uint8_t *p = fb->mmap;
            while (pixels--)
            {
                uint32_t n = (*p++ << 0) + (*p++ << 8) + (*p++ << 16); // little-endian
                *rgb++ = n >> fb->red;
                *rgb++ = n >> fb->green;
                *rgb++ = n >> fb->blue;

            }
        }
        case 4:
        {
            uint32_t *p = fb->mmap;
            while (pixels--)
            {
                uint32_t n = *p++;
                *rgb++ = n >> fb->red;
                *rgb++ = n >> fb->green;
                *rgb++ = n >> fb->blue;
            }
            break;
        }
    }
}

// Pack raw rgb data to specified area of framebuffer and return 0. The rgb
// array must always be fb->height * fb->width * 3 bytes long, even if the
// specified area is smaller than that. Return 0 if success, or ERANGE if
// specified area is invalid.
int fbpack(struct fbinfo *fb, uint8_t *rgb, uint32_t left, uint32_t top, uint32_t right, uint32_t bottom)
{
    if (left < 0 || left > right || left >= fb->width || right >= fb->width ||
        top < 0 || top > bottom || top >= fb->height || bottom >= fb->height) return ERANGE;

    for (uint32_t line = top; line <= bottom; line++)
    {
        uint8_t *d = rgb + (line * fb->width * 3) + (left * 3);
        switch(fb->bpp)
        {
            case 2:
            {
                uint16_t *p = fb->mmap + (line * fb->width * 2) + (left * 2);
                for (uint32_t column = left; column <= right; column++)
                {
                    *p++ = ((d[0]>>3) << fb->red) | ((d[1]>>2) << fb->green) | ((d[2]>>3) << fb->blue);
                    d += 3;
                }
                break;
            }
            case 3:
            {
                uint8_t *p = fb->mmap + (line * fb->width * 3) + (left * 3);
                for (uint32_t column = left; column <= right; column++)
                {
                    uint32_t n = (d[0] << fb->red) | (d[1] << fb->green) | (d[2] << fb->blue);
                    *p++ = n; *p++ = n>>8; *p++ = n >> 16; // little-endian
                    d += 3;
                }
                break;
            }
            case 4:
            {
                uint32_t *p = fb->mmap + (line * fb->width * 4) + (left * 4);
                for (uint32_t column = left; column <= right; column++)
                {
                    *p++ = (d[0] << fb->red) | (d[1] << fb->green) | (d[2] << fb->blue) | 0xff000000;
                    d += 3;
                }
                break;
            }
        }
    }
    return 0;
}
