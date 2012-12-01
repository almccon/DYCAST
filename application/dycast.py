# This file includes most of the core DYCAST functions

from __future__ import division
import sys
import os
import shutil
#import datetime
from datetime import timedelta
import time
import fileinput
import ConfigParser
import logging
from ftplib import FTP

if sys.platform == 'win32':
    lib_dir = "C:\\DYCAST\\application\\libs"
else:
    lib_dir = "/Users/alan/github/DYCAST/application/libs"

sys.path.append(lib_dir)            # the hard-coded library above
sys.path.append("libs")             # a library relative to current folder

sys.path.append(lib_dir+os.sep+"dbfpy") # the hard-coded library above
sys.path.append("libs"+os.sep+"dbfpy")  # a library relative to current folder

try:
    import dbf
except ImportError:
    print "couldn't import dbf library in path:", sys.path
    sys.exit()

sys.path.append(lib_dir+os.sep+"psycopg2")  # the hard-coded library above
sys.path.append("libs"+os.sep+"psycopg2")   # a library relative to current folder

try:
    import psycopg2
except ImportError:
    print "couldn't import psycopg2 library in path:", sys.path
    sys.exit()

#loglevel = logging.DEBUG        # For debugging
loglevel = logging.INFO         # appropriate for normal use
#loglevel = logging.WARNING      # appropriate for almost silent use

conn = 0
cur = 0
dbfn = 0
riskdate_tuple = ()

# Conversions and the DYCAST parameters:
miles_to_metres = 1609.34722
#TODO: find a more appropriate way to initialize these
sd = 1
cs = 1
ct = 1
td = 1
threshold = 1

default_days_lit = 0
default_days_before = -1

risk_cutoff = 0.1

# postgresql database connection information and table names
dsn = "x"
dead_birds_table_unprojected = "x"
dead_birds_table_projected = "x"
human_cases_table_unprojected = "x"
human_cases_table_projected = "x"
effects_poly_table = "x"
effects_poly_tiles_table = "x"
all_risk_table = "x"
analysis_area_table = "x"

# dist_margs means "distribution marginals" and is the result of the
# monte carlo simulations.  See Theophilides et al. for more information
#def create_dist_margs():
#def load_prepared_dist_margs():

#def create_analysis_grid():
#def load_prepared_analysis_grid():

def read_config(filename):
    # All dycast objects must be initialized from a config file, therefore,
    # all dycast applications must include the name of a config file, or they
    # must use the default, which is dycast.config in the current directory

    global dbname
    global user
    global password
    global host
    global dsn
    global ftp_site
    global ftp_user
    global ftp_pass
    global dead_birds_filename
    global dead_birds_dir
    global risk_file_dir
    global lib_dir
    global dead_birds_table_unprojected
    global dead_birds_table_projected
    global human_cases_table_unprojected
    global human_cases_table_projected
    global effects_poly_table
    global effects_poly_tiles_table
    global all_risk_table
    global analysis_area_table
    global sd
    global td
    global cs
    global ct
    global threshold
    global logfile

    config = ConfigParser.SafeConfigParser()
    config.read(filename)

    dbname = config.get("database", "dbname")
    user = config.get("database", "user")
    password = config.get("database", "password")
    host = config.get("database", "host")
    dsn = "dbname='" + dbname + "' user='" + user + "' password='" + password + "' host='" + host + "'"

    ftp_site = config.get("ftp", "server")
    ftp_user = config.get("ftp", "username")
    ftp_pass = config.get("ftp", "password")
    dead_birds_filename = config.get("ftp", "filename")
    if sys.platform == 'win32':
        logfile = config.get("system", "windows_dycast_path") + config.get("system", "logfile")
        dead_birds_dir = config.get("system", "windows_dycast_path") + config.get("system", "dead_birds_subdir")
        risk_file_dir = config.get("system", "windows_dycast_path") + config.get("system", "risk_file_subdir")
    else:
        logfile = config.get("system", "unix_dycast_path") + config.get("system", "logfile")
        dead_birds_dir = config.get("system", "unix_dycast_path") + config.get("system", "dead_birds_subdir")
        risk_file_dir = config.get("system", "unix_dycast_path") + config.get("system", "risk_file_subdir")

    dead_birds_table_unprojected = config.get("database", "dead_birds_table_unprojected")
    dead_birds_table_projected = config.get("database", "dead_birds_table_projected")
    human_cases_table_unprojected = config.get("database", "human_cases_table_unprojected")
    human_cases_table_projected = config.get("database", "human_cases_table_projected")
    effects_poly_table = config.get("database", "effects_poly_table")
    effects_poly_tiles_table = config.get("database", "effects_poly_tiles_table")
    all_risk_table = config.get("database", "all_risk_table")
    analysis_area_table = config.get("database", "analysis_area_table")

    sd = float(config.get("dycast", "spatial_domain")) * miles_to_metres
    cs = float(config.get("dycast", "close_in_space")) * miles_to_metres
    ct = int(config.get("dycast", "close_in_time"))
    td = int(config.get("dycast", "temporal_domain"))
    threshold = int(config.get("dycast", "bird_threshold"))

def init_logging():
    logging.basicConfig(format='%(asctime)s %(levelname)8s %(message)s', 
        filename=logfile, filemode='a')
    logging.getLogger().setLevel(loglevel)

def debug(message):
    logging.debug(message)

def info(message):
    logging.info(message)

def warning(message):
    logging.warning(message)

def error(message):
    logging.error(message)

def create_db(dbname):
    # Currently this doesn't work
    try:
        #conn = psycopg2.connect("dbname='template1' user='" + user + "' host='" + host + "'")
        conn = psycopg2.connect("user='" + user + "' host='" + host + "'")
    except Exception, inst:
        logging.error("Unable to connect to server")
        logging.error(inst)
        sys.exit()
    #conn.autocommit(True)
    #conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    #conn.switch_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    try:
        cur.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
    except Exception, inst:
        logging.error(inst)
        return 0

    try:
        cur.execute("CREATE DATABASE " + dbname)
    except Exception, inst:
        logging.error(inst)
        return 0

    return 1
    

def init_db():
    global cur, conn
    try:
        conn = psycopg2.connect(dsn)
    except Exception, inst:
        logging.error("Unable to connect to database")
        logging.error(inst)
        sys.exit()
    cur = conn.cursor()

##########################################################################
##### functions for loading data:
##########################################################################

def load_bird(line):
    try:
        (bird_id, report_date_string, lon, lat, species) = line.split("\t")
    except ValueError:
        logging.warning("SKIP incorrect number of fields: %s", line.rstrip())
        return 0
    # We need to force this query to take lon and lat as the strings 
    # that they are, not quoted as would happen if I tried to list them 
    # in the execute statement.  That's why they're included in this line.
    #TODO: the hardcoded SRIDs should be changed, and instead read from the config file.
    #TODO: similarly, they should not be hardcoded in postgres_init.sql
    querystring = "INSERT INTO " + dead_birds_table_projected + " VALUES (%s, %s, %s, ST_Transform(GeometryFromText('POINT(" + lon + " " + lat + ")',4269),54003))"
    #querystring = "INSERT INTO " + dead_birds_table_unprojected + " VALUES (%s, %s, %s, GeometryFromText('POINT(" + lon + " " + lat + ")',4269))"
    try:
        cur.execute(querystring, (bird_id, report_date_string, species))
    except Exception, inst:
        conn.rollback()
        if str(inst).startswith("duplicate key"): 
            logging.debug("couldn't insert duplicate dead bird key %s, skipping...", bird_id)
            return -1
        else:
            logging.warning("couldn't insert dead bird record")
            logging.warning(inst)
            return 0
    conn.commit()
    return bird_id

def load_human_case(line):
    try:
        (human_case_id, onset_date_string, lon, lat) = line.split("\t")
    except ValueError:
        logging.warning("SKIP incorrect number of fields: %s", line.rstrip())
        return 0
    # We need to force this query to take lon and lat as the strings 
    # that they are, not quoted as would happen if I tried to list them 
    # in the execute statement.  That's why they're included in this line.
    #TODO: the hardcoded SRIDs should be changed, and instead read from the config file.
    #TODO: similarly, they should not be hardcoded in postgres_init.sql
    querystring = "INSERT INTO " + human_cases_table_projected + " VALUES (%s, %s, %s, %s, ST_Transform(GeometryFromText('POINT(" + lon + " " + lat + ")',4269),54003))"
    #querystring = "INSERT INTO " + human_cases_table_unprojected + " VALUES (%s, %s, %s, GeometryFromText('POINT(" + lon + " " + lat + ")',4269))"

    # if human_case_id is not an integer, what do we do?A
    if not str(human_case_id).isdigit():
        # The "-" is a special case of California's WNV ID system.
        # TODO: need a more robust system of setting an appropriate ID
        (left, sep, right_digits) = str(human_case_id).rpartition("-")
        human_case_id_old = human_case_id
        human_case_id = int(left+right_digits)
        logging.debug("splitting %s, using %i as integer index", human_case_id_old, human_case_id)

    try:
        cur.execute(querystring, (human_case_id, onset_date_string, default_days_lit, default_days_before))
    except Exception, inst:
        conn.rollback()
        if str(inst).startswith("duplicate key"): 
            logging.debug("couldn't insert duplicate human WNV case key %s, skipping...", human_case_id)
            return -1
        else:
            logging.warning("couldn't insert human WNV case record")
            logging.warning(inst)
            return 0
    conn.commit()
    return human_case_id

#def analyze_tables():
    # This must be run outside a transaction block.  However, psycopg2 has 
    # a problem doing that on Mac

    #querystring = "VACUUM ANALYZE " + dead_birds_table_projected
    #try:
    #    cur.execute(querystring)
    #except Exception, inst:
    #    print inst



##########################################################################
##### functions for exporting results:
##########################################################################

def export_risk(riskdate, format = "dbf", path = None):
    if path == None:
        path = risk_file_dir + "/tmp/"
        using_tmp = True
    else:
        using_tmp = False


    # riskdate is a date object, not a string
    try:
        riskdate_string = riskdate.strftime("%Y-%m-%d")
    except:
        logging.error("couldn't convert date to string: %s", riskdate)
        return 0
    querystring = "SELECT tile_id, num_birds, close_pairs, close_space, close_time, nmcm FROM \"risk%s\"" % riskdate_string
    try:
        cur.execute(querystring) 
    except Exception, inst:
        conn.rollback()
        logging.error("couldn't select risk for date: %s", riskdate_string)
        logging.error(inst)
        return 0

    if format == "txt":
        txt_out = init_txt_out(riskdate, path)
    else:   # dbf or other
        dbf_out = init_dbf_out(riskdate, path)

    rows = cur.fetchall()
    
    if format == "txt":
        # Currently just sprints to stdout.  Fix this later if needed
        for row in rows:
            # Be careful of the ordering of space and time in the db vs the txt file
            [id, num_birds, close_pairs, close_space, close_time, nmcm] = row
            print "%s\t1.5\t0.2500\t3\t%s\t%s\t?.???\t%s\t%s\t%s" % (id, num_birds, close_pairs, close_time, close_space, nmcm)
        txt_close()
    else:
        for row in rows:
            # Be careful of the ordering of space and time in the db vs the txt file
            [id, num_birds, close_pairs, close_space, close_time, nmcm] = row
            dbf_print(id, nmcm)
        dbf_close()
        if using_tmp:
            dir, base = os.path.split(dbf_out.name)
            dir, tmp = os.path.split(dir)   # Remove the "tmp" to get outbox
            outbox_tmp_to_new(dir, base)    # Move finished file to "new"
        

def init_txt_out(riskdate, path):
    # Currently just sprints to stdout.  Fix this later if needed
    print "ID\tBuf\tcs\tct\tnum\tpairs\texp\tT_Only\tS_Only\tnmcm"

def init_dbf_out(riskdate, path = None):
    if path == None:
        path = "."
    global dbfn
    global riskdate_tuple
    filename = path + os.sep + "risk" + riskdate.strftime("%Y-%m-%d") + ".dbf"
    dbfn = dbf.Dbf(filename, new=True)
    dbfn.addField(
        ("ID",'N',8,0),
        ("COUNTY",'N',3,0),
        ("RISK",'N',1,0),
        ("DISP_VAL",'N',8,6),
        ("DATE",'D',8)
    )

    riskdate_tuple = (int(riskdate.strftime("%Y")), int(riskdate.strftime("%m")), int(riskdate.strftime("%d")))

    #TODO: make this an object
    return dbfn

def txt_print(id, num_birds, close_pairs, close_space, close_time, nmcm):
    print "%s\t1.5\t0.2500\t3\t%s\t%s\t?.???\t%s\t%s\t%s" % (id, num_birds, close_pairs, close_time, close_space, nmcm)
    
def dbf_print(id, nmcm):
    global dbfn
    global riskdate_tuple
    rec = dbfn.newRecord()
    rec['ID'] = id
    rec['COUNTY'] = get_county_id(id)
    if nmcm > 0:
        rec['RISK'] = 1
    else:
        rec['RISK'] = 0
    rec['DISP_VAL'] = nmcm 
    rec['DATE'] = riskdate_tuple  
    rec.store()
   
def txt_close():
    # Currently just sprints to stdout.  Fix this later if needed
    print "done" 

def dbf_close():
    global dbfn
    dbfn.close()

##########################################################################
##### functions for uploading and downloading files:
##########################################################################

# The outbox functions are based on the Maildir directory structure.
# The use of /tmp/ allows to spend a lot of time writing to the file, 
# if necessary, and then atomically move it to a /new/ directory, where
# other scripts can find it.  In this way, the /new/ directory will never
# include incomplete files that are still being written.

def outbox_tmp_to_new(outboxpath, filename):
    shutil.move(outboxpath + "/tmp/" + filename, outboxpath + "/new/" + filename)
    
def outbox_new_to_cur(outboxpath, filename):
    shutil.move(outboxpath + "/new/" + filename, outboxpath + "/cur/" + filename)

def backup_birds():
    (stripped_file, ext) = os.path.splitext(dead_birds_filename)
    #stripped_file = dead_birds_filename.rstrip("tsv")
    #stripped_file = stripped_file.rstrip("txt")    # Just in case
    new_file = stripped_file + "_" + datetime.date.today().strftime("%Y-%m-%d") + ".tsv"
    shutil.copyfile(dead_birds_dir + dead_birds_filename, dead_birds_dir + new_file)

def download_birds():
    localfile = open(dead_birds_dir + os.sep + dead_birds_filename, 'w')

    try:
        ftp = FTP(ftp_site, ftp_user, ftp_pass)
    except Exception, inst:
        logging.error("could not download birds: unable to connect")
        logging.error(inst)
        localfile.close()
        sys.exit()
       
    try: 
        ftp.retrbinary('RETR ' + dead_birds_filename, localfile.write)
    except Exception, inst:
        logging.error("could not download birds: unable retrieve file")
        logging.error(inst)
        #sys.exit() # If there's no birds, we should still generate risk
    localfile.close()

def load_bird_file(filename = None):
    if filename == None:
        filename = dead_birds_dir + os.sep + dead_birds_filename
    lines_read = 0
    lines_processed = 0
    lines_loaded = 0
    lines_skipped = 0
    for line in fileinput.input(filename):
        if fileinput.filelineno() != 1:
            lines_read += 1
            result = 0
            result = load_bird(line)

            # If result is a bird ID or -1 (meaning duplicate) then:
            if result:                  
                lines_processed += 1
                if result == -1:
                    lines_skipped += 1
                else:
                    lines_loaded += 1

    # dycast.analyze_tables()   
    logging.info("bird load complete: %s processed %s of %s lines, %s loaded, %s duplicate IDs skipped", filename, lines_processed, lines_read, lines_loaded, lines_skipped)
    return lines_read, lines_processed, lines_loaded, lines_skipped

 
def load_human_file(filename):
    # Need to catch exception from missing files, also above in load_bird
    lines_read = 0
    lines_processed = 0
    lines_loaded = 0
    lines_skipped = 0
    for line in fileinput.input(filename):
        if fileinput.filelineno() != 1:
            lines_read += 1
            result = 0
            result = load_human_case(line)

            # If result is a human case ID or -1 (meaning duplicate) then:
            if result:                  
                lines_processed += 1
                if result == -1:
                    lines_skipped += 1
                else:
                    lines_loaded += 1

    # dycast.analyze_tables()   
    logging.info("human case load complete: %s processed %s of %s lines, %s loaded, %s duplicate IDs skipped", filename, lines_processed, lines_read, lines_loaded, lines_skipped)
    return lines_read, lines_processed, lines_loaded, lines_skipped

 
def load_risk(filename):

    # for loading the system with risk already generated (for example, in 
    # a previous year or on a different computer)

    # File must be dbf including fields: ID, DISP_VAL, DATE
    # Optional fields: COUNTY, RISK
    # Later: make DATE optional if it is provided in filename

    lines_read = 0
    lines_processed = 0
    lines_loaded = 0
    lines_skipped = 0

    dbfn = dbf.Dbf(filename, readOnly = 1)
    #for fldName in dbfn.fieldNames:
    #    print '%s\t' % fldName,
    for recnum in range(0,len(dbfn)):
        lines_read += 1
        risk = None
        rec = dbfn[recnum]
        for fldName in dbfn.fieldNames:
            if fldName == 'ID':
                id = rec[fldName]
            elif fldName == 'DISP_VAL':
                disp_val = rec[fldName]
            elif fldName == 'DATE':
                date = rec[fldName]
            elif fldName == 'RISK':
                risk = rec[fldName]
        if risk == None:
            if disp_val <= risk_cutoff:
                risk = 1
            else:
                risk = 0

        querystring = "INSERT INTO " + all_risk_table + " VALUES (%s, %s, %s, %s)"

        lines_processed += 1
        try:
            cur.execute(querystring, (id, risk, disp_val, date))
            lines_loaded += 1
        except Exception, inst:
            conn.rollback()
            dbfn.close()
            lines_skipped += 1
            logging.warning("couldn't load risk record")
            logging.warning(inst)
            return lines_read, lines_processed, lines_loaded, lines_skipped
    conn.commit()
    dbfn.close()

    # dycast.analyze_tables()   
    logging.info("risk load complete: %s processed %s of %s lines, %s loaded, %s skipped", filename, lines_processed, lines_read, lines_loaded, lines_skipped)
    return lines_read, lines_processed, lines_loaded, lines_skipped

def upload_new_risk(outboxpath = None):
    if outboxpath == None:
        outboxpath = risk_file_dir
    newdir = outboxpath + "/new/"
    for file in os.listdir(newdir):
         if ((os.path.splitext(file))[1] == '.dbf'):
            logging.debug("uploading %s and moving it from new/ to cur/", file)
            upload_risk(newdir, file)
            outbox_new_to_cur(outboxpath, file)

def upload_risk(path, filename):
    ######
    ###### WARNING: Not tested
    ######
    
    # Fix this: allow uploading multiple files:
    # Also check if this should use outboxpath
    localfile = open(path + os.sep + filename)
    
    ftp = FTP(ftp_site, ftp_user, ftp_pass)
    ftp.storbinary('STOR ' + filename, localfile)
    localfile.close()

##########################################################################
##### functions for generating risk:
##########################################################################

def create_temp_bird_table(riskdate, days_prev):
    enddate = riskdate
    startdate = riskdate - timedelta(days=(days_prev))
    tablename = "dead_birds_" + startdate.strftime("%Y-%m-%d") + "_to_" + enddate.strftime("%Y-%m-%d")
    querystring = "CREATE TEMP TABLE \"" + tablename + "\" AS SELECT * FROM " + dead_birds_table_projected + " where report_date >= %s and report_date <= %s" 
    try:
        cur.execute(querystring, (startdate, enddate))
    except Exception, inst:
        conn.rollback()
        # If string includes "already exists"...
        if str(inst).find("already exists") != -1: 
            cur.execute("DROP TABLE \"" + tablename + "\"")
            cur.execute(querystring, (startdate, enddate))
        else:
            logging.error(inst)
            sys.exit()
    conn.commit()
    return tablename

def create_daily_risk_table(riskdate):
    tablename = "risk" + riskdate.strftime("%Y-%m-%d") 
    querystring = "CREATE TABLE \"" + tablename + "\" (LIKE \"risk_table_parent\" INCLUDING CONSTRAINTS)"
    # the foreign key constraints are not being copied for some reason.
    try:
        cur.execute(querystring)
    except Exception, inst:
        conn.rollback()
        # TODO: save old version of risk instead of overwriting
        try:   
            cur.execute("DROP TABLE \"" + tablename + "\"")
            cur.execute(querystring)
        except:
            conn.rollback()
            logging.error("couldn't create risk table: %s", tablename)
            sys.exit()
    conn.commit()
    return tablename


def get_ids(startpoly=None, endpoly=None):
    try:
        if endpoly != None and startpoly != None:
            querystring = "SELECT tile_id from " + effects_poly_table + " where tile_id >= %s and tile_id <= %s"
            cur.execute(querystring, (startpoly, endpoly))
        elif startpoly != None:
            querystring = "SELECT tile_id from " + effects_poly_table + " where tile_id >= %s"
            cur.execute(querystring, (startpoly,))
        else:
            querystring = "SELECT tile_id from " + effects_poly_table
            cur.execute(querystring)
    except Exception, inst:
        logging.error("can't select tile_id from %s", effects_poly_table)
        logging.error(inst)
        sys.exit()
    rows = cur.fetchall()
    return rows

def get_county_id(tile_id):
    try:
        #TODO: This poly table needs to be the one with counties in it
        # I'm not sure why it works adding the tile_id as a string, but
        # doesn't work if I replace it with %s and include it in 
        #cur.execute as a second argument
        querystring = "SELECT county FROM effects_polys where tile_id = " + str(tile_id)
        cur.execute(querystring)
    except Exception, inst:
        conn.rollback()
        logging.warning("warning: can't select county for effects poly %s", tile_id)
        logging.warning(inst)
        return 0
    #TODO: should raise a warning if the county is not found (that is, the select might not fail, but the result could still be empty)
    return cur.fetchone()[0]

def get_county_id_from_county_name(county_name):
    try:
        querystring = "SELECT county_id FROM county_codes where name = \'" + str(county_name) + "\'"
        cur.execute(querystring)
    except Exception, inst:
        conn.rollback()
        logging.warning("warning: can't select county id for county name %s", county_name)
        logging.warning(inst)
        return 0
    #TODO: should raise a warning if the county is not found (that is, the select might not fail, but the result could still be empty)
    return cur.fetchone()[0]

def check_bird_count(bird_tab, tile_id):
    querystring = "SELECT count(*) from \"" + bird_tab + "\" a, " + effects_poly_table + " b where b.tile_id = %s and st_distance(a.location,b.the_geom) < %s" 
    try:
        cur.execute(querystring, (tile_id, sd))
    except Exception, inst:
        conn.rollback()
        logging.error("can't select bird count")
        logging.error(inst)
        sys.exit()
    new_row = cur.fetchone()
    return new_row[0]

def print_bird_list(bird_tab, tile_id):
    querystring = "SELECT bird_id from \"" + bird_tab + "\" a, " + effects_poly_table + " b where b.tile_id = %s and st_distance(a.location,b.the_geom) < %s" 
    try:
        cur.execute(querystring, (tile_id, sd))
    except Exception, inst:
        conn.rollback()
        logging.error("can't select bird list")
        logging.error(inst)
        sys.exit()
    for row in cur.fetchall():
        print row[0]

def create_effects_poly_bird_table(bird_tab, tile_id):
    tablename = "temp_table_bird_selection" 
    #tablename = bird_tab + "_" + tile_id
    # I don't think this can be a temp table, or else I'd have to use "EXECUTE"
    # (See Postgresql FAQ about functions and temp tables)
    querystring = "CREATE TABLE \"" + tablename + "\" AS SELECT * from \"" + bird_tab + "\" a, " + effects_poly_table + " b where b.tile_id = %s and st_distance(a.location,b.the_geom) < %s" 
    try:
        #logging.info("selecting CREATE TABLE with st_distance(a.location,b.the_geom) < %s", sd)
        cur.execute(querystring, (tile_id, sd))
    except:
        conn.rollback()
        cur.execute("DROP TABLE \"" + tablename + "\"")
        cur.execute(querystring, (tile_id, sd))
    conn.commit()
    return tablename 

def cst_cs_ct_wrapper():
    querystring = "SELECT * FROM cst_cs_ct(%s, %s)"
    try:
        #logging.info("selecting SELECT * FROM cst_cs_ct(%s, %s)", cs, ct)
        cur.execute(querystring, (cs, ct))
    except Exception, inst:
        conn.rollback()
        logging.error("can't select cst_cs_ct function")
        logging.error(inst)
        sys.exit()
    return cur.fetchall()
  
def nmcm_wrapper(num_birds, close_pairs, close_space, close_time):
    querystring = "SELECT * FROM nmcm(%s, %s, %s, %s)"
    try:
        cur.execute(querystring, (num_birds, close_pairs, close_space, close_time))
    except Exception, inst:
        conn.rollback()
        logging.error("can't select nmcm function")
        logging.error(inst)
        sys.exit()
    return cur.fetchall()
  
def insert_result(riskdate, tile_id, num_birds, close_pairs, close_time, close_space, nmcm):
    tablename = "risk" + riskdate.strftime("%Y-%m-%d") 
    querystring = "INSERT INTO \"" + tablename + "\" (tile_id, num_birds, close_pairs, close_space, close_time, nmcm) VALUES (%s, %s, %s, %s, %s, %s)"
    try:
        # Be careful of the ordering of space and time in the db vs the txt file
        cur.execute(querystring, (tile_id, num_birds, close_pairs, close_space, close_time, nmcm))
    except Exception, inst:
        conn.rollback()
        logging.error("couldn't insert effects_poly risk")
        logging.error(inst)
        return 0
    conn.commit()
         

def daily_risk(riskdate, startpoly=None, endpoly=None):
    rows = get_ids(startpoly, endpoly)

    risk_tab = create_daily_risk_table(riskdate)
    dead_birds_daterange = create_temp_bird_table(riskdate, td)

    st = time.time()
    if startpoly or endpoly:
        logging.info("Starting daily_risk for %s, startpoly: %s, endpoly: %s", riskdate, startpoly, endpoly)
    else:
        logging.info("Starting daily_risk for %s", riskdate)

    inc = 0
    for row in rows:
        tile_id = row[0]
        inc += 1
        if not inc % 1000:
            logging.debug("tile_id: %s done: %s time elapsed: %s", tile_id, inc, time.time() - st)
        num_birds = check_bird_count(dead_birds_daterange, tile_id)
        if num_birds >= threshold:
            create_effects_poly_bird_table(dead_birds_daterange, tile_id)
            st0 = time.time()
            results = cst_cs_ct_wrapper()
            st1 = time.time()
            close_pairs = results[0][0]
            close_space = results[1][0] - close_pairs
            close_time = results[2][0] - close_pairs
            #print "tile ", tile_id, "found", num_birds, "birds (above threshold) %s actual close pairs, %s close in space, %s close in time" % (close_pairs, close_space, close_time)
            #print_bird_list(dead_birds_daterange, tile_id)
            result2 = nmcm_wrapper(num_birds, close_pairs, close_space, close_time)
            insert_result(riskdate, tile_id, num_birds, close_pairs, close_time, close_space, result2[0][0])
     
    #logging.info("Finished daily_risk for %s: done %s tiles, time elapsed: %s seconds", riskdate, inc, time.time() - st)
    logging.info("Finished daily_risk for %s: done %s tiles", riskdate, inc)

##########################################################################
##### functions for post season analysis:
##########################################################################

#def post_analysis():
def human_data_compare(startdate, enddate, window=None):
    # the human data could be populated without regard for window, but 
    # including the window is necessary to imitate previous functionality
    querystring = "UPDATE \"" + human_cases_table_projected + "\" SET days_lit = %s, days_before = %s" 
    try:
        cur.execute(querystring, (default_days_lit,default_days_before))
    except Exception, inst:
        conn.rollback()
        logging.error("can't reset risk history for human_cases")
        logging.error(inst)
        sys.exit()
    conn.commit()
  
    # This query is somewhat expensive, so we could just do it once when
    # we load the human cases, or have a separate one-time-only function
    # to initialize a table with a human <-> tile relationship 
    querystring = "SELECT a.human_case_id, a.onset_date, b.tile_id FROM \"" + human_cases_table_projected + "\" a INNER JOIN \"" + effects_poly_tiles_table + "\" b ON ST_Intersects(a.location, b.the_geom)" 
    #querystring = "SELECT a.human_case_id, a.onset_date, b.tile_id FROM \"" + human_cases_table_projected + "\" a INNER JOIN \"" + effects_poly_tiles_table + "\" b ON ST_Intersects(a.location, b.the_geom) ORDER BY a.onset_date" 
    try:
        cur.execute(querystring)
    except Exception, inst:
        conn.rollback()
        logging.error("can't select human case list")
        logging.error(inst)
        sys.exit()
    for row in cur.fetchall():
        logging.debug("Selecting history for tile %s, onset of %s, tile ", row[0], row[1], row[2])
        # for each human's tile, select its risk history
        querystring = "SELECT a.date FROM \"" + all_risk_table + "\" a WHERE a.tile_id = %s AND a.risk = 1 AND a.date <= %s" 
        try:
            if (window):
                startwin = row[1] - timedelta(window)
                querystring += " AND a.date >= %s"
                querystring += " ORDER BY a.date" 
                cur.execute(querystring, (row[2],row[1],startwin))    # row[2] is tile_id
            else:
                querystring += " ORDER BY a.date" 
                cur.execute(querystring, (row[2],row[1]))    # row[2] is tile_id
        except Exception, inst:
            conn.rollback()
            logging.error("can't select risk history for tile_id %s", row[2])
            logging.error(inst)
            sys.exit()
        tile_history = cur.fetchall()
        #for date in tile_history:
            #print date[0]
        days_lit = len(tile_history)
        # print "lit for %s days" % days_lit 
        if (days_lit != 0):
            first_day = tile_history[0][0]
            days_before = row[1] - first_day
            # print "lit %s days before" % days_before.days


            querystring = "UPDATE \"" + human_cases_table_projected + "\" SET days_lit = %s, days_before = %s WHERE human_case_id = %s" 
            try:
                cur.execute(querystring, (days_lit,days_before.days,row[0]))
            except Exception, inst:
                conn.rollback()
                logging.error("can't update risk history for human_case %s", row[0])
                logging.error(inst)
                sys.exit()
            conn.commit()
        
    if not (window):
        print "window was not tested"

def populate_histograms():
    #select uniq number of humans at each lag
    logging.info("test of dummy populate_histograms function")

def text_export(window=None, file_prefix=None, countyname=None):
    #print two tsvs using previous format, suitable for Excel

    days_lit_dict = {}

    querystring = "SELECT days_lit, count(distinct human_case_id) FROM " + human_cases_table_projected + " GROUP BY days_lit"
    if (countyname):
        querystring = "SELECT a.days_lit, count(distinct a.human_case_id) FROM " + human_cases_table_projected + " a INNER JOIN counties b ON ST_Intersects(transform(a.location,4269), b.the_geom) WHERE b.name = \'" + countyname + "\' GROUP BY a.days_lit"
        #county_id = get_county_id_from_county_name(countyname)
        #querystring = "SELECT a.days_lit, count(distinct a.human_case_id) FROM " + human_cases_table_projected + " a INNER JOIN human_tiles_temp b ON a.human_case_id=b.human_case_id INNER JOIN effects_polys_unprojected c ON b.tile_id=c.tile_id WHERE c.county = " + str(county_id) + " GROUP BY a.days_lit"
    else:
        countyname = ""     # this will be used in the output filename
    try:
        cur.execute(querystring)
    except Exception, inst:
        conn.rollback()
        logging.error("can't select days_lit history for human_cases")
        logging.error(inst)
        sys.exit()

    tot_hit = 0
    cumul = 0
    for days_lit_count in cur.fetchall():
        days_lit_dict[days_lit_count[0]] = days_lit_count[1]
    if not days_lit_dict:
        # no human cases.
        print "No human cases in", countyname
        return 0

    days_lit_keys = sorted(days_lit_dict.keys())
    max_lit = days_lit_keys[-1]

    # if we have requested only a window, then (to simplify calculation below)
    # we will take all the human cases that have days greater than the window
    # and collapse them into the window
    if window:
        max_to_display = window + 1
        for i in range(max_lit, max_to_display, -1):
            try:
                case_count = days_lit_dict[i]
            except KeyError:
                case_count = 0
            days_lit_dict[max_to_display] += case_count
            print "i: %s, case_count: %s, max_date_total: %s" % (i, case_count, days_lit_dict[max_to_display])
    else:
        max_to_display = max_lit
        

    localfile = None
    filename_string = "hist_days_lit_0_to_" + str(max_to_display - 1) + str(countyname)
    if file_prefix:
        localfile = open(file_prefix + filename_string + ".txt", 'w')
    else:
        print filename_string
    print >> localfile, "Number_cases\tDays_lit\tCumulative_Cases\tPercent"
    # TODO: This loop should not be duplicated with the one below 
    # TODO: I am going through these twice so I know the final cumulative number
    for i in range(max_to_display, -1, -1): # count down to 0
        try:
            case_count = days_lit_dict[i]
        except KeyError:
            case_count = 0
        cumul += case_count
    tot_cumul = cumul
    cumul = 0
    for i in range(max_to_display, -1, -1): # count down to 0
        try:
            case_count = days_lit_dict[i]
        except KeyError:
            case_count = 0
        cumul += case_count
        
        if i == 1:
            # This is our overall hit rate (at least one day lit)
            tot_hit = cumul
        #print "%s\t%s\t%s" % (case_count, i, cumul)
        # Note, this division requires "from __future__ import division"
        print >> localfile, "%s\t%s\t%s\t%0.2f" % (case_count, i, cumul, 100*(cumul / tot_cumul))
    if localfile:
        localfile.close()


    days_before_dict = {}

    querystring = "SELECT days_before, count(distinct human_case_id) FROM " + human_cases_table_projected + " GROUP BY days_before"
    if (countyname):
        querystring = "SELECT a.days_before, count(distinct a.human_case_id) FROM " + human_cases_table_projected + " a INNER JOIN counties b ON ST_Intersects(transform(a.location,4269), b.the_geom) WHERE b.name = \'" + countyname + "\' GROUP BY a.days_before"
        #county_id = get_county_id_from_county_name(countyname)
        #querystring = "SELECT a.days_before, count(distinct a.human_case_id) FROM " + human_cases_table_projected + " a INNER JOIN human_tiles_temp b ON a.human_case_id=b.human_case_id INNER JOIN effects_polys_unprojected c ON b.tile_id=c.tile_id WHERE c.county = " + str(county_id) + " GROUP BY a.days_before"
    try:
        cur.execute(querystring)
    except Exception, inst:
        conn.rollback()
        logging.error("can't select days_before history for human_cases")
        logging.error(inst)
        sys.exit()

    cumul = 0
    tot_cumul = 0
    for days_before_count in cur.fetchall():
        days_before_dict[days_before_count[0]] = days_before_count[1]

    days_before_keys = sorted(days_before_dict.keys())
    max_before = days_before_keys[-1]
    #logging.debug("Max before: %s", max_before)

    # if we have requested only a window, then (to simplify calculation below)
    # we will take all the human cases that have days greater than the window
    # and collapse them into the window
    if window:
        max_to_display = window
        for i in range(max_before, max_to_display, -1):
            try:
                case_count = days_before_dict[i]
            except KeyError:
                case_count = 0
            days_before_dict[max_to_display] += case_count
    else:
        max_to_display = max_before


    localfile = None
    filename_string = "hist_first_captured_0_to_" + str(max_to_display) + str(countyname)
    if file_prefix:
        localfile = open(file_prefix + filename_string + ".txt", 'w')
    else:
        print filename_string
    print >> localfile, "Number_cases\tFirst_captured\tCumulative_Cases\tPercent"
    for i in range(max_to_display,-2,-1): # count down to -1
        try:
            case_count = days_before_dict[i]
        except KeyError:
            case_count = 0
        cumul += case_count
    tot_cumul = cumul
    cumul = 0
    for i in range(max_to_display,-2,-1): # count down to -1
        try:
            case_count = days_before_dict[i]
        except KeyError:
            case_count = 0
        cumul += case_count
        #print "%s\t%s\t%s" % (case_count, i, cumul)
        # Note, this division requires "from __future__ import division"
        print >> localfile, "%s\t%s\t%s\t%0.2f" % (case_count, i, cumul, 100*(cumul / tot_cumul)) 
    if localfile:
        localfile.close()

    
    print "%s\thit %s of %s\t%0.2f" % (countyname, tot_hit, tot_cumul, 100*(tot_hit / tot_cumul))

def text_export_all_counties(window=None, file_prefix=None):
    #querystring = "SELECT name FROM county_codes"
    querystring = "SELECT name FROM counties ORDER BY name"
    try:
        cur.execute(querystring)
    except Exception, inst:
        conn.rollback()
        logging.error("couldn't select county names using %s", querystring)
        logging.error(inst)
        return 0

    for county in cur.fetchall():
        text_export(window, file_prefix, county[0])

def get_analysis_area_id():
    # Right now this function returns the ID of the first record. This will
    # be used as the analysis region (the "participating area")
    # If no records are found, return None and kappa will analyze all tiles 
   
    querystring = "SELECT id FROM \"" + analysis_area_table + "\""
    try:
        cur.execute(querystring)
    except Exception, inst:
        conn.rollback()
        logging.error("can't select analysis area table")
        logging.error(inst)
        sys.exit()
    new_row = cur.fetchone()
    if new_row:
      return new_row[0]
    else:
      return None

def kappa(window, lag, startdate, enddate, analysis_area_id=None):

    logging.info("running kappa: window %s lag %s", window, lag)
    # Should there be a check if there is continuous risk days generated?

    total_cells = 0
    total_cells_lit = 0
    total_cells_not_lit = 0
    total_cells_lit_confirmed = 0
    total_cells_not_lit_confirmed = 0
    all_possible_captured = 0
    all_possible_no_hits = 0

    querystring = "SELECT count(*) FROM \"" + effects_poly_tiles_table + "\""
    try:
        cur.execute(querystring)
    except Exception, inst:
        conn.rollback()
        logging.error("can't select lit cells")
        logging.error(inst)
        sys.exit()
    new_row = cur.fetchone()
    all_cells = new_row[0]

    effects_poly_tiles_table_analysis = effects_poly_tiles_table
    human_cases_table_analysis = human_cases_table_projected 
    human_tiles_table_analysis = "human_effects_polys" 

    if analysis_area_id != None:
        logging.debug("Selecting effects polys within analysis area, please be patient...")
        # The analysis_geom must be a geometry that has already been
        # projected to the same projection as the analysis.

        #intersect tiles with analysis_geom
        effects_poly_tiles_table_analysis = "effects_polys_projected_analysis"

        querystring = "CREATE TEMP TABLE \"" + effects_poly_tiles_table_analysis + "\" AS SELECT a.* FROM \"" + effects_poly_tiles_table + "\" a, \"" + analysis_area_table + "\" b WHERE b.id = " + str(analysis_area_id) + " AND ST_Intersects(a.the_geom, b.the_geom)"
        try:
            cur.execute(querystring)
        except Exception, inst:
            conn.rollback()
            # If string includes "already exists"...
            if str(inst).find("already exists") != -1: 
                cur.execute("DROP TABLE \"" + effects_poly_tiles_table_analysis + "\"")
                cur.execute(querystring, (startdate, enddate))
            else:
                print "okay"
                logging.error("can't select create temp analysis table")
                logging.error(inst)
                sys.exit()
        
        conn.commit()

    # Here we find out the effects_poly for each human case and create 
    # a temp table with all of these polys.
    # This query is somewhat expensive, so we only do it once when
    # we load the human cases.
    logging.debug("Selecting effects polys for human cases, please be patient...")
    human_effects_polys = "human_effects_polys"
    querystring = "CREATE TEMP TABLE \"" + human_effects_polys + "\" AS SELECT a.human_case_id, a.onset_date, b.tile_id FROM \"" + human_cases_table_analysis + "\" a INNER JOIN \"" + effects_poly_tiles_table_analysis + "\" b ON ST_Intersects(a.location, b.the_geom) ORDER BY a.onset_date" 
    try:
        cur.execute(querystring)
    except Exception, inst:
        conn.rollback()
        # If string includes "already exists"...
        if str(inst).find("already exists") != -1: 
            cur.execute("DROP TABLE \"" + human_effects_polys + "\"")
            cur.execute(querystring, (startdate, enddate))
        else:
            logging.error("can't select human case list")
            logging.error(inst)
            sys.exit()
    conn.commit()

    # test if startdate and enddate are date objects?

    # curdate is the date of the risk file, our predicted risk of infection for that day. We then look into the future (the lag) to see if there was any human onset that occured after the risk date.
    curdate = startdate
    while curdate <= enddate: 

        startofwindow = curdate + timedelta(days = lag)
        endofwindow = startofwindow + timedelta(days = window-1)

        querystring = "SELECT tile_id, onset_date FROM \"" + human_effects_polys + "\" WHERE onset_date >= %s and onset_date <= %s" 
        try:
            cur.execute(querystring, (startofwindow, endofwindow))
        except Exception, inst:
            conn.rollback()
            logging.error("can't select human case list")
            logging.error(inst)
            sys.exit()

        rows = cur.fetchall()
        human_count = len(rows)
        logging.debug("Kappa for %s got %s human(s)", curdate, human_count)

        if human_count:
            list_of_human_cells = []
            for row in rows:
                # print them all
                #logging.debug("got human case id %s, onset of %s", row[0], row[1])
                # test if any of these cells are lit on the curdate.
                # add up the number... this is all_possible_captured. 
                # CAREFUL, we must not overcount if two humans occured in the same cell. Only count that cell once. Use "set" to uniquify.
                #list_of_human_cells_str.append(str(row[0]))
                list_of_human_cells.append(row[0])
            all_possible = len(set(list_of_human_cells))
            #list_of_human_cells_str = ",".join(set(list_of_human_cells_str))
            #for cell in set(list_of_human_cells):
                #list_of_human_cells_str = "," str(cell)

            # this needs to be stored as a tuple for the query to execute
            list_of_human_cells_tuple = tuple(set(list_of_human_cells))

            querystring = "SELECT count(*) FROM \"" + all_risk_table + "\" a WHERE tile_id IN %s AND risk = 1 AND date = %s" 
            try:
                cur.execute(querystring, (list_of_human_cells_tuple, curdate))
            except Exception, inst:
                conn.rollback()
                logging.error("can't select lit human cells")
                logging.error(inst)
                sys.exit()
            new_row = cur.fetchone()
            cells_lit_confirmed = new_row[0]
            #print "lit human cells: ", cells_lit_confirmed, "/", all_possible
            
            querystring = "SELECT count(*) FROM \"" + all_risk_table + "\" a WHERE risk = 1 AND date = %s" 
            try:
                cur.execute(querystring, (curdate,))
            except Exception, inst:
                conn.rollback()
                logging.error("can't select lit cells")
                logging.error(inst)
                sys.exit()
            new_row = cur.fetchone()
            cells_lit = new_row[0]
            logging.debug("lit cells: %s / %s", cells_lit, all_cells)

            # all_cells includes everything, lit or unlit, with humans or 
            # without. We add this up in total_cells for all the days we test.
            total_cells += all_cells

            # cells_lit are the at-risk cells, whether or not they have humans
            total_cells_lit += cells_lit

            # cells_not_lit are the cells that are not at risk
            total_cells_not_lit += (all_cells - cells_lit)

            # cells_lit_confirmed are the lit cells that intersect humans 
            # some amount of days later. These are correct predictions.
            total_cells_lit_confirmed += cells_lit_confirmed

            # cells_not_lit_confirmed are the unlit cells that do not have
            # humans. These are also correct predictions.
            total_cells_not_lit_confirmed += (all_possible - cells_lit_confirmed) 

            # These are all the cells with human cases in them. These are all 
            # the possible cases we could have captured. The best case scenario.
            all_possible_captured += all_possible

            # These are all the cells with no humans. In the best case (but
            # unlikely) scenario, we would not have shown risk in these cells.
            all_possible_no_hits += (all_cells - all_possible)

        # end of if statement where humans > 0            

        curdate = curdate + timedelta(days=1)
    # end loop

    if all_possible_captured == 0:
        return "no humans found"

    if total_cells_lit == 0:
        return "no lit cells found"

    # Now, what do we do with these numbers?

    logging.debug("total cells: %s total cells lit: %s total humans (all_possible_captured): %s", total_cells, total_cells_lit, all_possible_captured)

    logging.debug("Expected chance agreement in cells with human cases")
    logging.debug("(Total_Cells_lit / Total_cells) x total_humans = ( %s / %s ) x %s", total_cells_lit, total_cells, all_possible_captured)
    logging.debug("Expected chance agreement in cells with no human cases")
    logging.debug("(Total_Cells_not_lit / Total_cells) x (1_season's_worth_of_cells-total_humans) = ( %s / %s ) x ( %s - %s )", total_cells_not_lit, total_cells, total_cells, all_possible_captured)
    expected_cases_captured = (total_cells_lit/total_cells)*all_possible_captured
    logging.debug("Expected cases captured by chance: %s", expected_cases_captured)
    expected_cases_not_captured = (total_cells_not_lit/total_cells)*(total_cells-all_possible_captured)
    logging.debug("Expected agreement on non active cells: %s", expected_cases_not_captured)


    observed = total_cells_lit_confirmed
    observed_unhits = total_cells_not_lit_confirmed
    total_agreement = observed + observed_unhits # These are all our successes
    expected_chance_agreement = expected_cases_captured + expected_cases_not_captured

    logging.debug("Observed agreement: %s", total_agreement)
    logging.debug("Expected agreement: %s", expected_chance_agreement)

    # all_possible_agreement is the total number of cell days.
    all_possible_agreement = all_possible_captured + all_possible_no_hits

    # if we were a perfect predictor, this number would be 1
    overall_success_rate = total_agreement/all_possible_agreement

    #kappa_value = (observed - expected) / (total - expected)
    kappa_value = (total_agreement - expected_chance_agreement) / (total_agreement - expected_chance_agreement)

    # calculate chi here

    # calculate hit_success_rate, the_hit_kappa
    # calculate non_hit_success_rate, the_non_hit_kappa

    hit_success_rate = observed / all_possible_captured
    the_hit_kappa = (observed - expected_cases_captured) / (all_possible_captured - expected_cases_captured)

    non_hit_success_rate = observed_unhits / all_possible_no_hits
    the_non_hit_kappa = (observed_unhits - expected_cases_not_captured) / (all_possible_no_hits - expected_cases_not_captured)
    
    the_weight = all_possible_no_hits/all_possible_captured

    # The +1 is necessary, because if the_weight is 1, then the
    # weighted kappa should be the average of the hit and non-hit
    # kappas (hence, we would divide their sum by 2)
    weighted_kappa = ((the_weight*the_hit_kappa) + the_non_hit_kappa)/(the_weight + 1)

    logging.debug("Kappa for window %s, lag %s from %s to %s is %s", window, lag, startdate, enddate, weighted_kappa)

    overall_success = 0
    chi_sq_value = 0
    significance_level = 0
    #outstring = str(window) + "\t" + str(lag) + "\t" + str(weighted_kappa)
    outstring = "\t".join(map(str, (window, lag, hit_success_rate, the_hit_kappa, non_hit_success_rate, the_non_hit_kappa, overall_success, kappa_value, weighted_kappa, chi_sq_value, significance_level)))
    return outstring

    # The following notes were made by Alan McConchie and Ylli Kellici 
    # in 2005, trying to understand the original Kappa code written by 
    # Constandinos Theophilides

#     at end of season, we have:
#     total_cells_lit              (marginal)
#     total_cells_not_lit          (marginal)
#     total_cells_lit_confirmed
#     total_cells_not_lit_confirmed
#     all_possible_captured        (marginal)
#     all_possible_no_hits         (marginal)
#
#
#  (imagine a table, please:)
#
#                      real life:
#                      all_possible_captured      all_possible_no_hits
# model:
#
# total_cells_lit      total_cells_lit_confirmed
#
#
#
# total_cells_not_lit                               total_cells_not_lit_confirmed
#
#  (below, remember "total_cells" is really total cell days
#   over whole season)
#
#  calculations:
#  We have all the values for the observed table.  Using the
#  observed marginals, we calculate the interior of the
#  expected table under the null hypothesis.

#  calculate expected chance agreement in cells with human cases:
#  (Total_Cells_lit / Total_cells) X total_humans
#
#  Save as expected_cases_captured
#  (This is the upper left cell)
#
#  (note, total_humans is not the same as all_possible_captured.
#  all_possible is total_humans * window.  It is all the
#  possible successes our tiles could have.  If a tile is lit
#  on a particular day, and our window is 3, then there are
#  three tile-days that could successfully capture that one human.
#  all_possible_captured will be less that total_humans *
#  window if more than one human appears in the same cell on
#  the same day.  (Or also if humans are in the same cell on
#  adjacent days?) Constandinos uses all_possible_captured in the
#  calculations, but tells us he's using total_humans in the display)
						
#  Expected chance agreement in cells without human cases
#  He prints:
#  (Total_Cells_not_lit / Total_cells) X (1_days_worth_of_cells-total_humans)
#  he calculates:
#  (total_cells_not_lit / total_cells) x (total_cells - all_possible_captured)

#  Save as expected_cases_not_captured
#  (This is the lower right cell)
#  (I would have called it expected_non-cases_captured)

#  Total_agreement is observed upper left plus observed lower right.
#  expected_chance_agreement is same thing from expected table

#  Calculate overall success rate: total_agreement / all_possible_agreement
#  total_agreement = observed + observed_unhits (tot hits conf + unhits conf)
#  all_possible_agreement = all_possible_captured + all_possible_no_hits

#  run calculate_kappa(), which simply does ((observed-expected) / (total-expected))
#  In this case, it is
# total_agreement-expected_chance_agreement /
# all_possible_agreement-expected_chance_agreement
#  print the result

#  now calculate the upper right and lower left of the observed table

#  calculate the chi squared probability (we don't understand
# all of this)

#  calculate success rate for hits only
#  calculate hit kappa (uses observed hits, expected hits and
# total possible hits (all_possible_captured))

#  Then calculate non-hit success rate and kappa

#  Calculate the weight which is (all_possible_no_hits /
#  all_possible_captured).  So, the weight will be 1 only if
# the cells are 50% saturated with humans.  Basically, the
# weight will always be a very large number if we are trying to
# identify a sparse phenomenon.

#  Calculate the weighted Kappa:
#  ((the_weight*the_hit_kappa) + the_non_hit_kappa)/(the_weight + 1)

#  In our situation, human cases will be much rarer than
# non-human cells, and it is considered more important to
# capture the humans than to avoid false positives.  So, the
# weighted kappa is largely determined by the hit kappa. 





    




##########################################################################
##########################################################################
