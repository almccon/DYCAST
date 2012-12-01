#! /usr/bin/env python
#
# Handle daily tasks, end to end
#
# 1) Downloads dead bird file
# 2) Load dead birds into database
# 3) Runs risk analysis for last three days
# 4) Exports risk values to dbf
# 5) Uploads risk dbf to server 
#
# Meant to be run daily as a scheduled task

import sys
import dycast
import optparse
import datetime
import calendar

usage = "usage: %prog [options]"
p = optparse.OptionParser(usage)
p.add_option('--config', '-c', 
            default="./dycast.config", 
            help="load config file FILE", 
            metavar="FILE"
            )
p.add_option('--num_days', '-n', 
            default="3", 
            help="run NUMDAYS into past", 
            metavar="NUMDAYS"
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

i = int(options.num_days)

cur_date = datetime.date.today()
oneday = datetime.timedelta(days=1)

if cur_date.weekday() == calendar.FRIDAY:
    dycast.backup_birds()

dycast.download_birds() # All options set in config file
dycast.load_bird_file() # All options set in config file 
while i > 0:
    dycast.daily_risk(cur_date) # this just needs to know date 
    dycast.export_risk(cur_date) # needs to know date; use default directory
    dycast.upload_new_risk() # upload everything from default directory
    cur_date -= oneday  # back up one day
    i -= 1              # number of times remaining to back up
