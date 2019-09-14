// Low-level support for framebuffer read/write
#include <linux/fb.h>

struct fbinfo
{
    uint32_t height,    // height must be first (for python)
             width,     // width must be second (for python)
             bpp,       // bytes per pixel: 2, 3, or 4. If 2 bytes, then colorspace is 565.
             red,       // red shift
             green,     // green shift
             blue;      // blue shift
    void   * mmap;      // pointer to frame buffer memory     
};

int fbopen(struct fbinfo *fb, char *device);
int fbunpack(struct fbinfo *fb, uint32_t pixels, uint32_t offset, uint8_t *rgb);
int fbpack(struct fbinfo *fb, uint32_t pixels, uint32_t offset, uint8_t *rgb);
