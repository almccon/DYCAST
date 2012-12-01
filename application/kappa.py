#! /usr/bin/env python

import sys
import dycast
import datetime
import optparse

usage = "usage: %prog [options]"
p = optparse.OptionParser(usage)
p.add_option('--windowstart', default=1, type="int")
p.add_option('--windowend', default=1, type="int")
p.add_option('--windowstep', default=1, type="int")
p.add_option('--lagstart', default=3, type="int")
p.add_option('--lagend', default=3, type="int")
p.add_option('--lagstep', default=1, type="int")
p.add_option('--startdate', default="2005-04-01")
p.add_option('--enddate', default="2005-10-01")
# you must specify date range, or fall back to default season

p.add_option('--useanalysisarea', default=True)
#p.add_option('--analysisareaid', default=None, type="int")
# Give the id for the analysis area. If none, will choose first one 
# Of no analysis areas are present, will fall back to analyzing all tiles

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

startdate = options.startdate 
enddate = options.enddate 

try:
    # This very simple parsing will work fine if date is YYYY-MM-DD
    (y, m, d) = startdate.split('-')
    startdate = datetime.date(int(y), int(m), int(d))

    if enddate == "today" or not enddate:
        enddate = datetime.date.today()
    else:
        (y, m, d) = enddate.split('-')
        enddate = datetime.date(int(y), int(m), int(d))

except Exception, inst:
    print "couldn't parse", startdate, enddate
    print inst
    sys.exit()

if options.windowstart > options.windowend:
  print "value for windowstart must be less than windowend"
  sys.exit()

if options.lagstart > options.lagend:
  print "value for lagstart must be less than lagend"
  sys.exit()

if options.windowstep > 1:
  print "value for windowstep must be greater than or equal to 1"
  sys.exit()

if options.lagstep > 1:
  print "value for lagstep must be greater than or equal to 1"
  sys.exit()


print "window\tlag\tsuccess_rate\thit_kappa\tnon_hit_success\tnon_hit_kappa\toverall_success_rate\toverall_kappa\tweighted_kappa\tchi_sq_value\tsignificance_level"
for window in range(options.windowstart, options.windowend+options.windowstep, options.windowstep):
    for lag in range(options.lagstart, options.lagend+options.lagstep, options.lagstep):
        if options.useanalysisarea:
            print dycast.kappa(window, lag, startdate, enddate, dycast.get_analysis_area_id())
            #if options.analysisareaid != None:
            #    print dycast.kappa(window, lag, startdate, enddate, dycast.get_analysis_area_id())
            #else:
            #    print dycast.kappa(window, lag, startdate, enddate, options.analysisareaid) # I haven't tested this one
        else:
            print dycast.kappa(window, lag, startdate, enddate, None)

