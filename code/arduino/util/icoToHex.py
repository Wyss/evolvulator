#!usr/bin/env python
# encoding: utf-8
"""
Copyright (c) 2012 Wyss Institute at Harvard University

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

http://www.opensource.org/licenses/mit-license.php
"""
"""
icoToHex.py
Short code to convert an .ico image to hex values for inclusion in c code

used in creating favicons for the webduino
The ico file can be whatever favicon format that works
you can for example  use the photoshop plugin from
http://www.telegraphics.com.au/sw/
"""

import sys
import struct

def show_usage():
    print "icoToHex.py <filename>"
    print "filename - is a *.ico file for a favicon"
# end def

def convertIcoToHex(argv=None):
    if argv is None:
        argv = sys.argv
    argc = len(argv)
    if argc != 2:
        show_usage()
        sys.exit(-1)
    # end if    
    filename = argv[1]
    with open(filename, "rb") as f:
        outString = ""
        i = 0
        b = f.read(1)
        while b != '':
            a = struct.unpack('B', b)[0]
            if a < 16:
                outString += "0x0%x, " % a
            else:
               outString += "0x%x, " % a 
            i += 1
            if i == 7:
                print outString, "\\"
                outString = "" 
                i = 0
            # Do stuff with byte.
            b = f.read(1)
        
# end def

if __name__ == "__main__":
    print "Converting"
    convertIcoToHex()