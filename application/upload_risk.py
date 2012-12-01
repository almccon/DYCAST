#! /usr/bin/env python
#
# Upload a risk .dbf file to an FTP site
#
# Meant to be run daily as a scheduled task
#
# The connection parameters for the FTP site are given in a config file
# 
# I'm not sure if this has been tested...

import sys
import dycast
import optparse
from ftplib import FTP

usage = "usage: %prog [options]"
p = optparse.OptionParser(usage)
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

dycast.info("uploading risk file %s", arguments[0])
dycast.upload_risk(arguments[0])

