# build fb.bin, required by fb.py
fb.bin: fb.o; gcc -shared -Wl,-soname,$@ -o $@ $<

.INTERMEDIATE: fb.o  
fb.o: fb.c; gcc -c -fPIC -o $@ $<

clean:; rm -f fb.bin fb.pyc
