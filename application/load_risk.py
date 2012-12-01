#! /usr/bin/env python
#
# Read a file containing WNV risk and load it into the database.
# This is useful if you have already generated risk files, but
# need to repopulate your database for whatever reason.
#
# The file(s) can be provided as the arguments like so:
#
# load_risk.py riskYYYY-MM-DD.dbf riskYYYY-MM-DD.dbf ...etc  
#
# Files must be in DBF format, including at least the following fields:
# ID (the ID of one of the DYCAST analysis tile
# DISP_VAL (the probability of WNV risk, from 1 to 0: high probability) 
# DATE (MM/DD/YYYY)

import dycast
import optparse

usage = "usage: %prog [options] datafile.dbf"
p = optparse.OptionParser(usage)
p.add_option('--config', '-c', 
            default="./dycast.config", 
            help="load config file FILE", 
            metavar="FILE")
options, arguments = p.parse_args()

config_file = options.config

dycast.read_config(config_file)

dycast.init_logging()

dycast.init_db()

for file in arguments:
    (lines_read, lines_processed, lines_loaded, lines_skipped) = dycast.load_risk(file)

