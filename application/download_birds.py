#! /usr/bin/env python
#
# Download a dead bird .tsv file from an FTP site
#
# Meant to be run daily as a scheduled task
#
# On Fridays, this script should create a backup of the current file before 
# overwriting it with the newly downloaded file. But I don't think that has 
# been added yet.
#
# The connection parameters for the FTP site are given in a config file
#
# See load_birds.py for more information about the dead bird file format

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

dycast.info("downloading birds")
dycast.download_birds()

