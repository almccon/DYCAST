#! /usr/bin/env python

# Prints out some end-of-year statistics

import sys
import dycast
import datetime
import optparse

usage = "usage: %prog [options]"
p = optparse.OptionParser(usage)
p.add_option('--window', default=30)
p.add_option('--startdate')
p.add_option('--enddate')
p.add_option('--all', action="store_true", dest="combined")
p.add_option('--bycounty', action="store_false", dest="combined", default=True)
# need to specify date range, or default season
p.add_option('--config', '-c', 
            default="./dycast.config", 
            help="load config file FILE", 
            metavar="FILE"
            )

#TODO: add option to specify output path

options, arguments = p.parse_args()

config_file = options.config

try:
    dycast.read_config(config_file)
except:
    print "could not read config file:", config_file
    sys.exit()

dycast.init_logging()

dycast.init_db()

window = int(options.window)
startdate = options.startdate 
enddate = options.enddate 

if enddate == "today" or not enddate:
    enddate = datetime.date.today()
else:
    try:
        # This very simple parsing will work fine if date is YYYY-MM-DD
        (y, m, d) = startdate.split('-')
        startdate = datetime.date(int(y), int(m), int(d))
        (y, m, d) = enddate.split('-')
        enddate = datetime.date(int(y), int(m), int(d))
    except Exception, inst:
        print "couldn't parse", startdate, enddate
        print inst
        sys.exit()

#dycast.human_data_compare(startdate, enddate, window)
    

# text_export takes two arguments:

# First, either specify the window, which will be included in the file name
# of the exported file.  If you set it to None, it will use whatever the 
# maximum value of days_lit or first_captured in the database.  In most cases,
# this maximum will be the same as the window, unless the window variable was
# different when you ran human_data_compare().  In most cases, it's best to
# use window here, instead of None.

# Second, specify the folder to write the output files to.  Omit the path
# (or set to None) to print to the screen

if options.combined:
    dycast.text_export(window)   # Leaving the path blank prints to screen
    #dycast.text_export(None, "/Users/alan/Documents/DYCAST/outbox/")

# To use the text_export_all_counties() function, you must have have already 
# loaded a shapefile into postgresql containing the county boundaries.
# The table must have a field "name" and a field "the_geom" in SRID 4269

else: 
    dycast.text_export_all_counties(window)
    #dycast.text_export_all_counties(window, "/Users/alan/Documents/DYCAST/outbox/test/")
