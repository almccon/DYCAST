#! /usr/bin/env python

# Simple script for printing out the content of a DBF.
# Meant only for quick debugging

import sys
import os
import optparse

# Workaround to load dbf library:
if sys.platform == 'win32':
    lib_dir = "C:\\DYCAST\\application\\libs"
else:
    lib_dir = "/Users/alan/Documents/DYCAST/application/libs"

sys.path.append(lib_dir)            # the hard-coded library above
sys.path.append("libs")             # a library relative to current folder

sys.path.append(lib_dir+os.sep+"dbfpy") # the hard-coded library above
sys.path.append("libs"+os.sep+"dbfpy")  # a library relative to current folder

try:
    import dbf
except ImportError:
    print "couldn't import dbf library in path:", sys.path
    sys.exit()
# end workaround


usage = "usage: %prog [options] file.dbf"
p = optparse.OptionParser(usage)
p.add_option('--postgres', '-p', 
            help="print only ids, suitable for postgres",
            action="store_true")
options, arguments = p.parse_args()

for filename in arguments:
    dbfn = dbf.Dbf(filename, readOnly = 1)
    for fldName in dbfn.fieldNames:
        print '%s\t' % fldName,
    print
    for recnum in range(0,len(dbfn)):
        rec = dbfn[recnum]
        for fldName in dbfn.fieldNames:
            if options.postgres:
                if fldName == 'ID':
                    print '%s,' % rec[fldName],
            else:
                print '%s\t' % rec[fldName],
        if not options.postgres:
            print
    dbfn.close()
        
