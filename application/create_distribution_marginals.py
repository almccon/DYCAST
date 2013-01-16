#! /usr/bin/env python

import sys
import dycast
import datetime
import optparse

usage = "usage: %prog [options]"
p = optparse.OptionParser(usage)
p.add_option('--closespace', default=1, type="float")
p.add_option('--closetime', default=1, type="int")
p.add_option('--spatialdomain', default=1, type="float")
p.add_option('--temporaldomain', default=3, type="int")
p.add_option('--startnumber', default=15, type="int")
p.add_option('--endnumber', default=100, type="int")

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

if options.startnumber > options.endnumber:
  print "value for startnumber must be less than or equal to endnumber"
  sys.exit()

dycast.create_dist_margs(options.closespace, options.closetime, options.spatialdomain, options.temporaldomain, options.startnumber, options.endnumber)
