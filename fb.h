// Low-level support for framebuffer read/write
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

int fbopen(struct fbinfo *fb, char *device);
int fbunpack(struct fbinfo *fb, uint32_t pixels, uint32_t offset, uint8_t *rgb);
int fbpack(struct fbinfo *fb, uint32_t pixels, uint32_t offset, uint8_t *rgb);
