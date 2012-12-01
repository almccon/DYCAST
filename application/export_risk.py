#! /usr/bin/env python

import sys
import dycast
import datetime
import optparse

usage = "usage: %prog [options] YYYY-MM-DD"
p = optparse.OptionParser(usage)
p.add_option('--dbf', '-d')
p.add_option('--txt', '-t')
#p.add_option('--outfile', '-o')
p.add_option('--config', '-c', 
            default="./dycast.config", 
            help="load config file FILE", 
            metavar="FILE")

options, arguments = p.parse_args()

config_file = options.config

dycast.read_config(config_file)

dycast.init_db()


riskdate = arguments[0]

if riskdate == "today" or not riskdate:
    riskdate = datetime.date.today()
else:
    try:
        # This very simple parsing will work fine if date is YYYY-MM-DD
        (y, m, d) = riskdate.split('-')
        riskdate = datetime.date(int(y), int(m), int(d))
    except Exception, inst:
        print "couldn't parse", riskdate
        print inst
        sys.exit()

if options.txt:
    dycast.export_risk(riskdate, "txt")
else:
    dycast.export_risk(riskdate, "dbf")

