#!/bin/sh

# This script is for initializing the DYCAST database

DBNAME=dycast
USERNAME=postgres
DYCAST_PATH=/Users/alan/Documents/DYCAST/
DYCAST_APP_PATH=$DYCAST_PATH/application/
DYCAST_INIT_PATH=$DYCAST_PATH/init/
PG_SHARE_PATH_1_5=/usr/local/pgsql/share/contrib/postgis-1.5/
PG_SHARE_PATH_2_0=/usr/local/pgsql/share/contrib/postgis-2.0/

# Change this to TRUE if you are using PostgreSQL 8.4 and PostGIS 1.5
# Leave this as FALSE if you are using PostgreSQL 9.1 and PostGIS 2.0

USE_POSTGIS_1_5="FALSE"

dropdb -U $USERNAME $DBNAME # if necessary

createdb -U $USERNAME --encoding=UTF8 $DBNAME --template template0

### Note that plpgsql is usually already installed for postgres 8.4+
# createlang -U $USERNAME plpgsql $DBNAME

if [ "$USE_POSTGIS_1_5" == "TRUE" ]; then

    echo "using 1.5"

    ### For postgres 9.1+ we don't load these here. Instead, we will
    ### add PostGIS as an extension, below
    psql -U $USERNAME -d $DBNAME -f $PG_SHARE_PATH_1_5/postgis.sql
    psql -U $USERNAME -d $DBNAME -f $PG_SHARE_PATH_1_5/spatial_ref_sys.sql

else

    echo "using 2.0"

    ### Using the new 9.1+ extension method:
    psql -U $USERNAME -d $DBNAME -c "CREATE EXTENSION postgis;" 

    ### And we need legacy functions (currently)
    psql -U $USERNAME -d $DBNAME -f $PG_SHARE_PATH_2_0/legacy.sql

fi

psql -U $USERNAME -d $DBNAME -f $DYCAST_APP_PATH/postgres_init.sql

psql -U $USERNAME -d $DBNAME -f $DYCAST_INIT_PATH/dumped_dist_margs.sql
psql -U $USERNAME -d $DBNAME -f $DYCAST_INIT_PATH/dumped_county_codes.sql
psql -U $USERNAME -d $DBNAME -f $DYCAST_INIT_PATH/dumped_effects_polys.sql
psql -U $USERNAME -d $DBNAME -f $DYCAST_INIT_PATH/dumped_effects_poly_centers.sql

# create inbox, outbox (as maildir) but test for existence first
mkdir $DYCAST_PATH/inbox
mkdir $DYCAST_PATH/outbox
mkdir $DYCAST_PATH/outbox/tmp
mkdir $DYCAST_PATH/outbox/cur
mkdir $DYCAST_PATH/outbox/new
