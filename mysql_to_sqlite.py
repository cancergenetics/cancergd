#!/usr/bin/env python

import sys, os, sqlite3
from django.db import connection, transaction

PROJECT = 'cgdd'
# Part based on PHP code in: http://stackoverflow.com/questions/18671/quick-easy-way-to-migrate-sqlite3-to-mysql

# This works as long as we don't depend on the auto-increment values in the dependency table.

# BUT MySQL does enforce max_length, so will truncate dtrings that are too long, so need to check for data truncation
import warnings # To convert the MySQL data truncation (due to field max_length being too small) into raising an exception."

# To use the warning category  below, might need to use: import MySQLdb
# Also see: http://www.nomadjourney.com/2010/04/suppressing-mysqlmysqldb-warning-messages-from-python/
# warnings.filterwarnings('error', category=MySQLdb.Warning) # Raises exceptions on a MySQL warning. From: http://stackoverflow.com/questions/2102251/trapping-a-mysql-warning
 # or:  warnings.filterwarnings('ignore', 'Unknown table .*')
warnings.filterwarnings('error', 'Data truncated .*') # regular expression to catch: Warning: Data truncated for column 'gene_name' at row 1

# Build paths inside the project like this: os.path.join(PROJECT_DIR, ...)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__)) # Full path to my django project directory, which is: "C:/Users/HP/Django_projects/cgdd/"  or: "/home/sbridgett/cgdd/"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PROJECT+".settings")

# Needs the following django.setup(), otherwise get exception about: django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
# From google search, this django.setup() is called in the 'execute_from_command_line(sys.argv)' in the manage.py script
#    http://stackoverflow.com/questions/25537905/django-1-7-throws-django-core-exceptions-appregistrynotready-models-arent-load
#    http://grokbase.com/t/gg/django-users/14acvay7ny/upgrade-to-django-1-7-appregistrynotready-exception
import django
django.setup()
from django.conf import settings


# from gendep.models import Study, Gene, Drug, Dependency  # Removed: Histotype, 
SQLITE_DBNAME='db.sqlite3'
conn = sqlite3.connect(SQLITE_DBNAME)
sqlite_cursor = conn.cursor()

mysql_cursor = connection.cursor() # Django
    
# was PHP code:  
#$tables = $sq->query( 'SELECT name FROM sqlite_master WHERE type="table"' );

# Using the django connection (alternatively could use the mysqlclient directly: https://pypi.python.org/pypi/mysqlclient )

DB = settings.DATABASES['default']  # or: DB = getattr(settings, "DATABASE", None); DB = DB['default']
print("\nDATABASE NAME: %s\nENGINE: %s\nvendor: %s\n" %(DB['NAME'],DB['ENGINE'],connection.vendor))

if connection.vendor == 'sqlite' or DB['ENGINE'][-7:] == 'sqlite3':  # ENGINE: "django.db.backends.sqlite3"
    print("ERROR: In '%s/settings.py' the default DATABASE is sqlite, but this script expects MySQL (or Postrges)" %(PROJECT))
    sys.exit()
      
print("\n** WARNING: This will delete all data from SQLite database '%s' **" %(SQLITE_DBNAME))
# print("\n** WARNING: This will delete all data from SQLite database '%s' **" %(DB['NAME']))
if input("\nContinue (y/n)?").lower() != 'y':
    print("Exiting")
    sys.exit() # input() removes the trailing newline.

print("NOT FINISHED YET")
sys.exit()


# *** The following was added for MySql to Sqlite:
print("Deleting data from the Sqlite database %s ..." %(SQLITE_DBNAME))
print(sqlite_cursor.execute("SET FOREIGN_KEY_CHECKS=0; TRUNCATE `gendep_dependency`; TRUNCATE `gendep_study`; TRUNCATE `gendep_gene`; SET FOREIGN_KEY_CHECKS=1;")) # maybe add "IF EXISTS", eg: "TRUNCATE `gendep_gene` IF EXISTS;"
print(sqlite_cursor.execute("ALTER TABLE `gendep_dependency` AUTO_INCREMENT=1;"))     


# Get exclusive lock on the tables first ideally..

# empty the mysql table - after asking first !!!!
# for table in (Dependency, Study, Gene, Drug): table.objects.all().delete()  # removed: Histotype,
#? and reset autoincrement counters ???
#DELETE FROM tablename
#ALTER TABLE tablename AUTO_INCREMENT=1  # or =0
#TRUNCATE TABLE is faster: https://dev.mysql.com/doc/refman/5.0/en/truncate-table.html
#delete the dependency table first as it has foreign keys.


if connection.vendor == 'mysql':
     print("\nReading data from MySQL database '%s'" %(DB['NAME']))
# *** The following was commented out for MySql to Sqlite:
#    print("Deleting data from the MySQL database %s ..." %(DB['NAME']))    
#    print(mysql_cursor.execute("SET FOREIGN_KEY_CHECKS=0; TRUNCATE `gendep_dependency`; TRUNCATE `gendep_study`; TRUNCATE `gendep_gene`; SET FOREIGN_KEY_CHECKS=1;")) # maybe add "IF EXISTS", eg: "TRUNCATE `gendep_gene` IF EXISTS;"    
#    # The following AUTO_INCREMENT=1 reset needs to be in a separate mysql execute statement, otherwise get error about: #        django.db.utils.ProgrammingError: (2014, "Commands out of sync; you can't run this command now")
#    print(mysql_cursor.execute("ALTER TABLE `gendep_dependency` AUTO_INCREMENT=1;"))     
#    
elif connection.vendor == 'postgres':
     print("\nReading data from Postgres database '%s'" %(DB['NAME']))
# *** The following was commented out for MySql to Sqlite:     
#    print("Deleting data from the Postgres database %s ..." %(DB['NAME']))
#    # Need to test if this Postgres works, maybe need to disable foreign key trigger on other tables too:
#    print(mysql_cursor.execute("ALTER ALTER TABLE 'gendep_dependency' DISABLE TRIGGER ALL; TRUNCATE `gendep_dependency` TRUNCATE TABLE tablename RESTART IDENTITY; TRUNCATE `gendep_study`; TRUNCATE `gendep_gene`; ALTER ALTER TABLE 'gendep_dependency' ENABLE TRIGGER ALL;"))
else:
    print("Unexpected database type: ",connection.vendor)
    sys.exit()

# In Postgres use: TRUNCATE TABLE tablename RESTART IDENTITY;
#              or: TRUNCATE TABLE tablename; ALTER SEQUENCE seq_name START 1;
#              or: TRUNCATE TABLE tablename; ALTER SEQUENCE seq_name RESTART WITH 1;

#SET FOREIGN_KEY_CHECKS=0;   (This will  disable  FOREIGN KEY check)
#Truncate your tables and change it back to
#SET FOREIGN_KEY_CHECKS=1;

for table in ( 'study', 'gene', 'dependency'):   # Not used: 'drug',
    table = 'gendep_'+table # As table names are prefixed with the app name.

# *** The following was commented out for MySql to Sqlite:
#    rows = sqlite_cursor.execute( "SELECT * FROM '%s'" %(table) )
    rows = mysql_cursor.execute( "SELECT * FROM '%s'" %(table) )

    colnames = [c[0] for c in rows.description] # eg: (('gene_name', None, None, None, None, None, None),...
    
    insert_statement = "INSERT INTO `%s` (%s) VALUES (%s)" %(table, ','.join(colnames), ','.join(["%s"]*len(colnames)))
    
    print(insert_statement)    

    # empty the mysql table - after asking first !!!!
    
    # Use custom SQL directly: https://docs.djangoproject.com/en/1.9/topics/db/sql/#executing-custom-sql-directly
    
    # Using prepared statement might be faster: http://stackoverflow.com/questions/15856604/django-mysql-prepared-statements
    # or: https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursorprepared.html
    
    # Using Django custom SQL. Note: Django expects the "%s" placeholder, (not the "?" placeholder, which is used by the SQLite Python bindings).   
    with transaction.atomic():
        for row in rows:
            # These double omim_id's (eg. ....|.....) are now fixed in load_data.py
            #if table == 'gendep_gene' and len(row[10])>9:
            #    pos = row[10].find('|')
            #    if pos > -1:
            #        row = list(row) # As cannot change elements with a tuple
            #        row[10] = row[10][:pos]
#                print(row[10])
# *** The following was commented out for MySql to Sqlite:
#            mysql_cursor.execute(insert_statement, row) # using parameters will safely escape the strings.
            sqlite_cursor.execute(insert_statement, row) # using parameters will safely escape the strings.            
    
#       printf( "INSERT INTO '%s' VALUES( %s );\n", $table,  ','.join(values) )

# Maybe:
# transaction.set_dirty()        
# transaction.commit()
# Save (commit) the changes

# *** The following commit() was added out for MySql to Sqlite:
conn.commit()
# Close the sqlite connection:
conn.close()

# Close the mysql cursor:
mysql_cursor.close()

# *** The following was commented out for MySql to Sqlite:
# print("Finished loading data from sqlite to mysql")
print("Finished loading data from MySQL to Sqlite '%s'" %(SQLITE_DBNAME))

# Alternatively could use: https://github.com/motherapp/sqlite_sql_parser



"""        
    printf( "-- %s\n", $table );
    while ( $row = $result->fetchArray( SQLITE3_ASSOC ) ) {
        $values = array_map( function( $value ) {
            return sprintf( "'%s'", mysql_real_escape_string( $value ) )
        }, array_values( $row ) );
        
        col_names = ...
"""
