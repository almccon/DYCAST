The Dynamic Continuous-Area Space-Time (DYCAST) system is a biologically based spatiotemporal model that uses public reports of dead birds to identify areas at high risk for West Nile virus (WNV) transmission to humans.

The original version was written by Constandinos Theophilides at the [Center for Analysis and Research of Spatial Information (CARSI)](http://www.geography.hunter.cuny.edu/~carsi/) at Hunter College, the City University of New York. That version was written in the Magik programming language for GE SmallWorld GIS. 

The current version was ported to Python and PostGIS by [Alan McConchie](https://github.com/almccon). It is very much a work-in-progress, and some parts of the original system have not been ported yet.

## Requirements

DYCAST has been tested on Microsoft Windows [which versions?] and Mac OS X (versions 10.6 and 10.7). 

DYCAST depends on the following software:

* 	[PostgreSQL](http://www.postgresql.org/) (tested on version 8.4 and 9.1)
* 	[PostGIS](http://postgis.refractions.net/) (tested on version 1.5 and 2.0)
* 	[Python](http://www.python.org/)

For Windows, download and install these requirements from the links provided, following the instructions on the respective web pages. For OS X, we recommend installing the pre-compiled binaries from [William Kyngesburye](http://www.kyngchaos.com/)

## Setup

### Extracting files

This repository contains sample data sufficient to get you started. (To understand the purpose of these datasets, please read the section below titled "About the DYCAST algorithm"). Included data:

* 	A .5 mile analysis grid for the state of California
* 	Monte Carlo simulations

Unzip file *init.zip* which creates the folder *DYCAST/init*

Unzip file *birds.zip* which creates the folder *DYCAST/inbox*

### Initializing database

For Windows, execute: 

	DYCAST\application\setup_db.bat
	
For OS X:

	DYCAST/application/setup_db.sh

*setup_db.bat* will create the necessary PostgreSQL database and populate the DYCAST tables with the contents of the init folder. This may take some time.

If there are any errors connecting to the database and locating files, you may have to quit and modify *DYCAST\application\dycast.config* (use a simple text editor such as WordPad) before trying again.

*setup_db.bat* will also create an inbox and outbox folder, if they do not already exist.

### Loading birds

You must populate the database with the locations of dead birds before you can run the analysis.

The dead bird data must be in TSV (tab separated values) files, in the following format:

	id	report_date	longitude	latitude	species
	479414	03/27/2008	-119.01529100 35.30386000 Mourning Dove
	479415	03/27/2008	-119.04693200 35.36288600 American Robin
	479416	03/27/2008	-119.14695300 35.39921000 European Starling

Once you have your dead bird data files in the correct format, there are two ways you can load them:

* 	Open *C:\DYCAST\application\ui.bat* (double-click it)

	In the DYCAST control window that opens, click “select birds”. Select one or more dead bird export file and click “Open”. Then click “load birds”. Wait until loading is complete before running any analysis. Consult *C:\DYCAST\dycast_log.txt* to see detailed results of the bird load.

* 	Alternatively, open a command prompt (from the start menu), change directory to *C:\DYCAST\application* and execute:

     	C:\DYCAST\application> load_birds.py ..\inbox\dycast_export_2007.tsv

	(replace “..\inbox\dycast_export_2007.tsv” with the filename of a dead bird export)
	
Repeat for any other .tsv files of dead birds.
Using either method, any birds that already exist in the database (according to their ID) will be skipped, not overwritten.

## Directory structure

	C:\DYCAST
		\inbox
		\outbox
		\application
		\init

### Inbox and outbox

The inbox is where the automated dycast program looks to find new dead birds. It expects the file will always be called *dycast_export.tsv*. On a weekly basis, the automated program will make a backup of the current *dycast_export.tsv* file. Backups will be stored in the same folder, with filenames of the format *dycast_export_YYYY-MM-DD.tsv*

The outbox is based on the “maildir” directory structure. These subfolders are where the automated dycast program deposits DBF files of risk data. DBFs are filed in the “tmp” subdirectory while the program is actively writing to the file. The completed risk DBFs are then moved to the “new” subdirectory of the outbox, and are then moved to the “cur” subdirectory after they have been FTPed to the mapping server.

### Application

The “application” folder contains the Python scripts and libraries.


Useful applications:

	load_birds.py birdfile.tsv
		(load dead birds into the database)
	daily_risk.py YYYY-MM-DD
		(run the DYCAST Knox Test for a day, generating risk)
    export_risk.py
		(exports DBF files for previously generated risk)
    daily_tasks.py
		(includes all the above for current day, plus uploading and downloading)
    ui.py
    	(graphical user interface for loading birds, generating risk and exporting risk)

Useful files:

	dycast.config
		(controls all the default DYCAST settings)

### Init

The “init” folder contains the SQL files to initialize the database with pre- calculated monte carlo distributions and the California analysis grid

### dycast_log.txt

The “dycast_log.txt” file contains detailed reports of each DYCAST operation executed.

## Automation of daily tasks

On Windows, go to Start > Control Panel > Scheduled Tasks to open the Scheduled Task Wizard.

First, create a task. You will be prompted to Browse for the program you want to run. Choose C:\DYCAST\application\daily_tasks.py (daily_tasks.py includes FTPing and risk for 3 previous days)

If the above does not work, try the following more descriptive command

	C:\Python25\python.exe C:\DYCAST\application\download_birds.py -c C:\DYCAST\application\dycast.config

Give the task a name, and choose the desired scheduling (in previous years, we would run daily tasks at 7pm PT, to give sufficient time for all of the new birds for the day to be included in the input file.)

Or use individual tasks, if you are not using FTP to fetch and send data: 

    load_birds.py (if you are placing them in inbox manually, not via FTP) 

    daily_risk.py (generates risk, but does not input or output) 

    export_risk.py (will place files in outbox, but not FTP them)

To check the status of the system, open the log file: DYCAST\dycast_log.txt

## Manual workflow

Manual operation of the system is possible as an alternative to running it as a scheduled task, or can be used in addition, as long as a DYCAST scheduled task is not currently running.  

### Graphical User Interface

*ui.py* (simple graphical user interface). This application allows a more user-friendly method of loading bird data, running daily risk, and exporting risk. More detailed reports of the system status will continue to be reported in C:\DYCAST\dycast_log.txt

### Viewing Results

Resulting DBF files can be joined to a shapefile of effects_polys. 

PostgreSQL tables can be viewed and manipulated using PgAdminIII.

## Post-season analysis

  [under construction]

### Hit rates

### The Kappa test

## About the DYCAST algorithm and parameters

*	TODO: Explain the principles
*	TODO: Explain the ecological parameters
*	TODO: Explain the Kappa parameters

## Peer-reviewed articles about the DYCAST system:

Theophilides, C. N., S. C. Ahearn, S. Grady, and M. Merlino. 2003. Identifying West Nile virus risk areas: the dynamic continuous-area space-time system. American Journal of Epidemiology 157, no. 9: 843–854. http://aje.oxfordjournals.org/content/157/9/843.short.

Theophilides, C. N., S. C. Ahearn, E. S. Binkowski, W. S. Paul, and K. Gibbs. 2006. First evidence of West Nile virus amplification and relationship to human infections. International Journal of Geographical Information Science 20, no. 1: 103–115. http://www.tandfonline.com/doi/abs/10.1080/13658810500286968.

Carney, Ryan, Sean C. Ahearn, Alan McConchie, Carol Glaser, Cynthia Jean, Chris Barker, Bborie Park, et al. 2011. Early Warning System for West Nile Virus Risk Areas, California, USA. Emerging Infectious Diseases 17, no. 8 (August): 1445–1454. http://www.cdc.gov/eid/content/17/8/100411.htm.

## Contact

Maintained by [Alan McConchie](https://github.com/almccon)
