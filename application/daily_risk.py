#! /usr/bin/env python

import sys
import dycast
import datetime
import optparse

usage = "usage: %prog [options] YYYY-MM-DD"
p = optparse.OptionParser(usage)
p.add_option('--date', '-d', 
            default="today", 
            )
p.add_option('--startpoly', '-s')
p.add_option('--endpoly', '-e')
p.add_option('--config', '-c', 
            default="./dycast.config", 
            help="load config file FILE", 
            metavar="FILE"
            )

options, arguments = p.parse_args()

config_file = options.config

try:
    dycast.read_config(config_file)
except:
    print "could not read config file:", config_file
    sys.exit()

dycast.init_logging()

dycast.init_db()

riskdate = options.date 

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

if options.endpoly and options.startpoly:
    dycast.daily_risk(riskdate, options.startpoly, options.endpoly)
elif options.endpoly and not options.startpoly:
    print "ERROR: the endpoly option is only supported along with startpoly"
elif options.startpoly:
    dycast.daily_risk(riskdate, options.startpoly)
else:
    dycast.daily_risk(riskdate)

