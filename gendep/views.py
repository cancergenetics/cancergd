import csv, time
import json # For ajax for the jquery autocomplete search box
import math # For ceil()
from urllib.request import Request, urlopen
from urllib.error import  URLError
from datetime import datetime # For get_timming() and log_comment()
import requests # for Enrichr and mailgun email server
import ipaddress # For is_valid_ip()
import subprocess, io, os  # Used for awstats_view()

from django.http import HttpResponse #, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache  # To cache previous results. NOTE: "To provide thread-safety, a different instance of the cache backend will be returned for each thread."
from django.core.urlresolvers import reverse
from django.utils import timezone # For log_comment(), with USE_TZ=True in settings.py, and istall "pytz"
from django.db.models import Q # Used for get_drivers()

from .models import Study, Gene, Dependency, Comment, News, Download  # Removed: Histotype,

from django.conf import settings # import the settings file for the Google analytics ID. Maybe better to use a context processor in the settings.py file: https://chriskief.com/2013/09/19/access-django-constants-from-settings-py-in-a-template/  and: http://www.nomadblue.com/blog/django/google-analytics-tracking-code-into-django-project/
# or use the settings export script: https://github.com/jkbrzt/django-settings-export   (see: http://stackoverflow.com/questions/433162/can-i-access-constants-in-settings-py-from-templates-in-django  and: http://stackoverflow.com/questions/629696/deploying-google-analytics-with-django and: https://github.com/montylounge/django-google-analytics )

# Optionally use Django logging during development and testing:
# This Django logging is configured in settings.py and is based on: http://ianalexandr.com/blog/getting-started-with-django-logging-in-5-minutes.html
#import logging
#logger = logging.getLogger(__name__)
#def log(): logger.debug("this is a debug message!")
#def log_error(): logger.error("this is an error message!!")

# Mime types for the responses:
html_mimetype = 'text/html; charset=utf-8'
json_mimetype = 'application/json; charset=utf-8'
csv_mimetype  = 'text/csv; charset=utf-8' # can be called: 'application/x-csv' or 'application/csv'
tab_mimetype  = 'text/tab-separated-values; charset=utf-8'
plain_mimetype ='text/plain; charset=utf-8'
#excel_minetype ='application/vnd.ms-excel'
excel_minetype ='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' # for xlsx format?

# Alternatively can use separate parameter in HtmlResponse: charset='UTF-8' instead of including 'charset=utf-8' in the content_type

# Enricher URL:
ENRICHR_BASE_URL = 'http://amp.pharm.mssm.edu/Enrichr/'

def post_or_get_from_request(request, name):
    if   request.method == 'POST': return request.POST.get(name, '')
    elif request.method == 'GET':  return request.GET.get(name, '')
    else:  return ''
    
def JsonResponse(data, safe=False):
    """ Could use the Django JsonResponse but less format options, so using HtmlResponse() """
    # eg: django.http.JsonResponse(data, safe=safe)
    return HttpResponse(json.dumps(data, separators=[',',':']), content_type=json_mimetype)

def PlainResponse(msg):
    return HttpResponse(msg, content_type=plain_mimetype)

def json_error(message, status_code='1'):
    """ Sends an error message to the browser in JSON format """
    return JsonResponse( {'success': False, 'error': status_code, 'message': message } ) # eg: str(exception)

def html_error(msg):
    return HttpResponse("<h2>Error:</h2>"+msg)

def plain_error(msg):
    return PlainResponse(msg)


def is_search_by_driver(search_by):
    """ Checks if the 'search_by' parameter is valid, returning True if the dependency search is by driver """
    if   search_by == 'driver': return True
    elif search_by == 'target': return False
    else: print("ERROR: **** Invalid search_by: '%s' ****" %(search_by))

def get_study_shortname_from_study_list(study_pmid, study_list):
    if (study_pmid is None) or (study_pmid == ''):
        return ''
    if study_pmid=="ALL_STUDIES":
        return "All studies"
    try:
        study = study_list.get(study_pmid=study.pmid)
#   Or iterate through the list:
#   for study in study_list:
#       if study_pmid == study.pmid:
        return study.short_name
    except ObjectDoesNotExist: # Not found by the objects.get()
        print("WARNING: '"+study_pmid+"' NOT found in database so will be ignored")
        return '' # ie. if study_pmid parameter value not found then ignore it.



def get_timing(start_time, name, time_list=None):
    """ Prints the time taken by functions, to help optimise the code and SQL queries.
    The start_time parameter value should be obtained from: datetime.now()
    Optionally if 'time_list' is passed then an array of timings is added to this list that can then be sent to Webbrowser console via JSON. A python list (array) is used (rather than a dictionary) so will preserve the order of elements. """
    duration = datetime.now() - start_time # This duration is in milliseconds
    # To print results in server log, use:
    # print( "%s: %s msec" %(name,str(duration)))  # or use: duration.total_seconds()
    if time_list is not None:
        if not isinstance(time_list, list):
            print("ERROR: get_timings() 'time_list' parameter is not a list")
        #if name in time_dict: print("WARNING: Key '%s' is already in the time_dict" %(name))
        time_list.append({name: str(duration)})
    return datetime.now()


def awstats_view(request):
    awstats_dir = "/home/cgenetics/awstats"
    awstats_script = os.path.join(awstats_dir, "wwwroot/cgi-bin/awstats.pl")
    # awstats_script = os.path.join(awstats_dir, "run_awstats.sh") # Test script for debugging.
        
    # Local test settings:
    #awstats_dir = "/Users/sbridgett/Documents/UCD/cgdd"
    #awstats_script = os.path.join(awstats_dir, "run_awstats.sh")

# Also added:  PLUGIN: DecodeUTFKeys
# REQUIRED MODULES: Encode and URI::Escape
# PARAMETERS: None
# DESCRIPTION: Allow AWStats to show correctly (in language charset)
# keywords/keyphrases strings even if they were UTF8 coded by the
# referer search engine.
#
# SJB enabled this plugin to cope with some server names in UTF8
# LoadPlugin="decodeutfkeys"
    perl5lib_for_decodeutfkeys = awstats_dir+"/URI-1.71/lib:"+awstats_dir+"/Encode-2.88/install_dir/lib/perl/5.18.2"
    
    perl5lib_for_geoip = awstats_dir+"/Geo-IP-1.50/install_dir/lib/perl/5.18.2"  # Path to the Geo-IP module used by awstats.pl. Could add:   +os.pathsep+os.environ['PERL5LIB']
    config = "awstats.cancergd.org.conf" # awstats config file (in awstats_dir/wwwroot/cgi-bin) for gathering and displaying the cancergd stats.

    cmd = [ awstats_script, '-config='+config ]
    env = dict(os.environ, PERL5LIB=perl5lib_for_geoip+':'+perl5lib_for_decodeutfkeys)
    # Alternatively copy the existing env and then modify it, so can add to any existing PERL5LIB:
    #  env = os.environ.copy()
    #  env['PERL5LIB'] = perl5lib_for_geoip + os.pathsep + env['PERL5LIB'] # note: os.pathsep is : or ;  whereas os.path.sep is \\ or /
    
        
    if len(request.GET.dict())==0:  # as just called with /stats so set default:
      cmd.append('-output')
    else:
      for key,val in request.GET.items():
        if key=='config': continue # Always set to this config option above (just in case accidentally or deliberately user tries a different config)
        cmd.append('-'+key+'='+val)   # eg: output, hostfilter, hostfilterex

        
    print("cmd",cmd)
          
    p = subprocess.Popen( cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # Optionally add: stderr=subprocess.PIPE, shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True
    # For 'shell=True' submit the whole command as one string, but this starts a new shell process (which is an expensive operation).
    # If submit the command with 'shell=False', give the command as a list of strings, with the command name in the first element of the list, the first argument in the next list element, etc.
    # But need 'shell=True' for eg: ls and rmdir which are not programs, but are internal commands within the shell program.
    # 'universal_newlines=True' means will return Strings (rather than Bytes)
    # Maybe 'bufsize=-1'

    # "This will deadlock when using stdout=PIPE or stderr=PIPE and the child process generates enough output to a pipe such that it blocks waiting for the OS pipe buffer to accept more data. Use Popen.communicate() when using pipes to avoid that.
    # "Use the communicate() method rather than .stdin.write, .stdout.read or .stderr.read to avoid deadlocks due to streams pausing reading or writing and blocking the child process.

    # awstats output seems to be in "iso-8859-1" rather than "uft-8"   see: https://sourceforge.net/p/awstats/discussion/43428/thread/b5cbb36c/
    # So can get error about: 
    # File "/home/cgenetics/cancergd/gendep/views.py", line 146, in awstats_view
    #    stdout, stderr = p.communicate(timeout=None)
    #  File "/usr/lib/python3.4/subprocess.py", line 960, in communicate
    #    stdout, stderr = self._communicate(input, endtime, timeout)
    #  File "/usr/lib/python3.4/subprocess.py", line 1659, in _communicate
    #    self.stdout.encoding)
    #  File "/usr/lib/python3.4/subprocess.py", line 888, in _translate_newlines
    #    data = data.decode(encoding)
    #  UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe7 in position 93349: invalid continuation byte

    stdout, stderr = p.communicate(timeout=None)
    # except TimeoutExpired:
    #       os.killpg(process.pid, signal)
    if p.returncode != 0:
      return html_error( "awstats failed with error code: %d  StdErr: %s" %(p.returncode, '' if stderr is None else stderr) )

    # For the 'AllowUpdatesFromBrowser=1' awstats config option, the update button link: http://www.cancergd.org/gendep/awstats/awstats?config=awstats.cancergd.org.conf&update=1
    # If there are any updates then will the stdout will start with:
    # Create/Update database for config "/home/cgenetics/awstats/awstats.cancergd.org.conf" by AWStats version 7.5 (build 20160301)
    # From data in log file "/home/cgenetics/awstats/tools/logresolvemerge.pl /var/log/*access.log* |"...
    # As if the "Update Now" is clicked with a subsection then the updated datta is returned.
    if "-update=1" in cmd and stdout[:len("Create/Update database")]=="Create/Update database":
      stdout = stdout.replace("\n","<br/>\n")
      stdout += '<br/><a href="' + reverse('stats') + '"><button>Display the updated stats</button></a>'

    # Could add logout link:  http://127.0.0.1:8000/admin/logout/ which is reverse( 'logout' ) or reverse( 'admin:logout' )
    logout_link = '<p align="right"><a href="' + reverse( 'admin:logout' ) + '">Admin LOG OUT</a></p>'
    return HttpResponse( ("" if stderr=="" else "ERROR:<br/>"+stderr+"<br/>\n\n") + logout_link +stdout )    
    # Could add to the update now link in the awstats.pl srcript: padding: 10px 20px;  

    awstats_dir = "/home/cgenetics/awstats"
    awstats_script = "${awstats_dir}/wwwroot/cgi-bin/awstats.pl"
    
    # awstats_script = os.path.join(awstats_dir, "run_awstats.sh") # Test script for debugging.
        
    # Local test settings:
    #awstats_dir = "/Users/sbridgett/Documents/UCD/cgdd"
    #awstats_script = os.path.join(awstats_dir, "run_awstats.sh")

    perl5lib_for_geoip = awstats_dir+"/Geo-IP-1.50/install_dir/lib/perl/5.18.2"  # Path to the Geo-IP module used by awstats.pl. Could add:   +os.pathsep+os.environ['PERL5LIB']
    config = "awstats.cancergd.org.conf" # awstats config file (in awstats_dir/wwwroot/cgi-bin) for gathering and displaying the cancergd stats.

    cmd = [ awstats_script, '-config='+config ]
    env = dict(os.environ, PERL5LIB=perl5lib_for_geoip)
    # Alternatively copy the existing env and then modify it, so can add to any existing PERL5LIB:
    #  env = os.environ.copy()
    #  env['PERL5LIB'] = perl5lib_for_geoip + os.pathsep + env['PERL5LIB'] # note: os.pathsep is : or ;  whereas os.path.sep is \\ or /
    
        
    if len(request.GET.dict())==0:  # as just called with /stats so set default:
      cmd.append('-output')
    else:
      for key,val in request.GET.items():
        if key=='config': continue # Always set to this config option above (just in case accidentally or deliberately user tries a different config)
        cmd.append('-'+key+'='+val)   # eg: output, hostfilter, hostfilterex

        
    print("cmd",cmd)
          
    p = subprocess.Popen( cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
    # Optionally add: stderr=subprocess.PIPE, shell=True, stdin=subprocess.PIPE, stderr=subprocess.STDOUT, close_fds=True
    # For 'shell=True' submit the whole command as one string, but this starts a new shell process (which is an expensive operation).
    # If submit the command with 'shell=False', give the command as a list of strings, with the command name in the first element of the list, the first argument in the next list element, etc.
    # But need 'shell=True' for eg: ls and rmdir which are not programs, but are internal commands within the shell program.
    # 'universal_newlines=True' means will return Strings (rather than Bytes)
    # Maybe 'bufsize=-1'

    # "This will deadlock when using stdout=PIPE or stderr=PIPE and the child process generates enough output to a pipe such that it blocks waiting for the OS pipe buffer to accept more data. Use Popen.communicate() when using pipes to avoid that.
    # "Use the communicate() method rather than .stdin.write, .stdout.read or .stderr.read to avoid deadlocks due to streams pausing reading or writing and blocking the child process.           

    # awstats output seems to be in "iso-8859-1" rather than "uft-8"   see: https://sourceforge.net/p/awstats/discussion/43428/thread/b5cbb36c/
    # So can get error about: 
    # File "/home/cgenetics/cancergd/gendep/views.py", line 146, in awstats_view
    #    stdout, stderr = p.communicate(timeout=None)
    #  File "/usr/lib/python3.4/subprocess.py", line 960, in communicate
    #    stdout, stderr = self._communicate(input, endtime, timeout)
    #  File "/usr/lib/python3.4/subprocess.py", line 1659, in _communicate
    #    self.stdout.encoding)
    #  File "/usr/lib/python3.4/subprocess.py", line 888, in _translate_newlines
    #    data = data.decode(encoding)
    #  UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe7 in position 93349: invalid continuation byte

    stdout, stderr = p.communicate(timeout=None)
    # except TimeoutExpired:
    #       os.killpg(process.pid, signal)
    if p.returncode != 0:
      return html_error( "awstats failed with error code: %d  StdErr: %s" %(p.returncode, '' if stderr is None else stderr) )

    # For the 'AllowUpdatesFromBrowser=1' awstats config option, the update button link: http://www.cancergd.org/gendep/awstats/awstats?config=awstats.cancergd.org.conf&update=1
    # If there are any updates then will the stdout will start with:
    # Create/Update database for config "/home/cgenetics/awstats/awstats.cancergd.org.conf" by AWStats version 7.5 (build 20160301)
    # From data in log file "/home/cgenetics/awstats/tools/logresolvemerge.pl /var/log/*access.log* |"...
    # As if the "Update Now" is clicked with a subsection then the updated datta is returned.
    if "-update=1" in cmd and stdout[:len("Create/Update database")]=="Create/Update database":
      stdout = stdout.replace("\n","<br/>\n")
      stdout += '<br/><a href="' + reverse('stats') + '"><button>Display the updated stats</button></a>'

    # Could add logout link:  http://127.0.0.1:8000/admin/logout/ which is reverse( 'logout' ) or reverse( 'admin:logout' )
    logout_link = '<p align="right"><a href="' + reverse( 'admin:logout' ) + '">Admin LOG OUT</a></p>'
    return HttpResponse( ("" if stderr=="" else "ERROR:<br/>"+stderr+"<br/>\n\n") + logout_link +stdout )    
    # Could add to the update now link in the awstats.pl srcript: padding: 10px 20px;  

#=======





# From: http://stackoverflow.com/questions/10340684/group-concat-equivalent-in-django
# Django doesn't have built-in support for GROUP_CONCAT (which is available in SQLite and MySQL), so create an Aggregate class for it:

from django.db.models import Aggregate, CharField, F

class Concat(Aggregate):
    # supports COUNT(distinct field)
    function = 'GROUP_CONCAT'
    
    engine = settings.DATABASES['default']['ENGINE']
    if engine == 'django.db.backends.sqlite3':
      template = '%(function)s(%(distinct)s%(expressions)s)'  # Added separator doesn't doesn't work in sqlite when DISTINCT. No order by within the GROUP_CONCAT in Sqlite
    elif engine == 'django.db.backends.mysql':
      template = '%(function)s(%(distinct)s%(expressions) ORDER BY s%(expressions) SEPARATOR ",")'  # but doesn't work in sqlite.
    elif engine == 'django.db.backends.postgresql':  # https://coderwall.com/p/eyknwa/postgres-group_concat
      template = 'string_agg(%(distinct)s%(expressions), "," ORDER BY %(expressions)s)'  # add order by after separator and without a comma before it: https://www.postgresql.org/docs/9.5/static/sql-expressions.html#SYNTAX-AGGREGATES
    else:
      html_error("Unexpected database engine: %s" %(engine))
    
    # template = '%(function)s(%(distinct)s%(expressions)s,";")'  # but doesn't work in sqlite.    
    # template = '%(function)s(%(distinct)s%(expressions)s,"%(sep)s")'
    # sep=sep
    # BUT get error: OperationalError: DISTINCT aggregates must have exactly one argument
    # it seems from web that cannot have both DISTINCT and a custom separator
    
    # In MySQL can add:    ORDER BY  DESC SEPARATOR ' '
     
    def __init__(self, expression, distinct=False, **extra):   # sep=';', BUT doesn't work in sqlite
        super(Concat, self).__init__(
            expression,
            distinct='DISTINCT ' if distinct else '',
            output_field=CharField(),
            **extra)
# use it simply as:

# query_set = Fruits.objects.values('type').annotate(count=Count('type'),
#                       name = Concat('name')).order_by('-count')


# OR:
# In the upcoming Django 1.8 you could just implement GroupConcat expression, and then the query would look like:
# Event.objects.values('slug').annotate(emails=GroupConcat('task__person__email'))
# The .values().annotate() combination sets the GROUP BY to slug, and of course the GroupConcat implementation does the actual aggregation.
# For how to write the GroupConcat implementation check out https://docs.djangoproject.com/en/dev/ref/models/expressions/#writing-your-own-query-expressions

def group_concat(column):
    engine = settings.DATABASES['default']['ENGINE']
    if engine == 'django.db.backends.sqlite3':
      return "GROUP_CONCAT(DISTINCT %s)" %(column)    # Added separator doesn't doesn't work in sqlite when DISTINCT. No ORDER BY within the GROUP_CONCAT in Sqlite
    elif engine == 'django.db.backends.mysql':
      return "GROUP_CONCAT(DISTINCT %s ORDER BY %s)" %(column,column)    # In MySQl can add:  SEPARATOR "," 
    elif engine == 'django.db.backends.postgresql':  # https://coderwall.com/p/eyknwa/postgres-group_concat
      return "string_agg(DISTINCT %s, ',' ORDER BY %s)" %(column,column)  # add order by after separator and without a comma before it: https://www.postgresql.org/docs/9.5/static/sql-expressions.html#SYNTAX-AGGREGATES
    else:
      html_error("Unexpected database engine: %s" %(engine))
      return "ERROR"


def build_driver_list(webpage):
    # An alternative to creating these concatenated histotype and study lists is:
    # for one driver:
    # select distinct pmid from gendep_dependency where driver='ERBB2' order by pmid;
    # select distinct histotype from gendep_dependency where driver='ERBB2' order by histotype;

    # or for all drivers:
    # select distinct driver, histotype from gendep_dependency order by driver,histotype;
    # select distinct driver, pmid from gendep_dependency order by driver,pmid;

    # For the full three-way data, so could set menus based on the other choices:
    # select distinct driver, histotype, pmid from gendep_dependency order by driver, histotype, pmid;


    # If the values() clause precedes the annotate(), the annotation will be computed using the grouping described by the values() clause:
    # query_seq = Dependency.objects.values('driver_id','driver__full_name','driver__prevname_synonyms').annotate(histotypes=Concat('histotype',distinct=True),studies=Concat('study_id',distinct=True)).order_by('driver_id')
                
    # SELECT "gendep_dependency"."driver", "gendep_gene"."full_name", "gendep_gene"."prevname_synonyms", GROUP_CONCAT(DISTINCT "gendep_dependency"."histotype") AS "histotypes", GROUP_CONCAT(DISTINCT "gendep_dependency"."pmid") AS "studies" FROM "gendep_dependency" INNER JOIN "gendep_gene" ON ("gendep_dependency"."driver" = "gendep_gene"."gene_name") GROUP BY "gendep_dependency"."driver", "gendep_gene"."full_name", "gendep_gene"."prevname_synonyms" ORDER BY "gendep_dependency"."driver" ASC driver histotypes study


    # (3) Use RAW SQL:
    if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
        histotype_order = ' ORDER BY D.histotype'
        pmid_order = ' ORDER BY D.pmid'
    else:
        histotype_order = ''
        pmid_order = ''
       
    if webpage == 'searchpage':
        # Three possible queries:
        # (1) With precomputed lists in model.py: 
        # driver_list = Gene.objects.filter(is_driver=True).only("gene_name", "full_name", "prevname_synonyms", "driver_histotype_list", "driver_study_list").order_by('gene_name')

        # (2) Using Django ORM
        #driver_list = Dependency.objects.values('driver_id').annotate(full_name=F('driver__full_name'),prevname_synonyms=F('driver__prevname_synonyms'), entrez_id=F('driver__entrez_id'), driver_histotype_list=Concat('histotype',distinct=True), driver_study_list=Concat('study_id',distinct=True) ).order_by('driver_id')
        # But this includes the full_name and synonyms in the GROUP BY list.
        # Could try querying using the Gene object - but this isn't working yet:
        # driver_list = Gene.objects.values('gene_name').annotate(full_name=F('full_name'),prevname_synonyms=F('prevname_synonyms'), entrez_id=F('entrez_id'), driver_histotype_list=Concat('histotype',distinct=True), driver_study_list=Concat('study_id',distinct=True) ).order_by('driver_id')
        
        driver_list = Gene.objects.raw("SELECT G.gene_name, G.entrez_id, G.full_name, G.prevname_synonyms, "
                                      + group_concat('D.histotype') + " AS driver_histotype_list, "             #   + "GROUP_CONCAT(DISTINCT D.histotype"+histotype_order+") AS driver_histotype_list, "
                                      + group_concat('D.pmid') + " AS driver_study_list "  # "GROUP_CONCAT(DISTINCT D.pmid"+pmid_order+") AS driver_study_list "
#                                      + "FROM gendep_dependency D INNER JOIN gendep_gene G ON (D.driver_entrez = G.entrez_id) "  # Now using Entrez_id as primary key for Gene
#                                      + "FROM gendep_dependency D INNER JOIN gendep_gene G ON (D.driver = G.gene_name) "
#                                      + "FROM gendep_dependency D INNER JOIN gendep_gene G ON (D.driver_name = G.gene_name) "  # Now using Entrez_id as primary key for Gene
                                      + "FROM gendep_dependency D INNER JOIN gendep_gene G ON (D.driver = G.entrez_id) "  # Now using Entrez_id as primary key for Gene
#                                      + "GROUP BY D.driver_entrez ORDER BY G.entrez_id ASC" # <-- Maybe should use this if always 1-to-1 mapping of entrez_id to driver_name
                                      + "GROUP BY D.driver ORDER BY G.gene_name ASC"   
                                      )
                                      
    elif webpage == 'driverspage':
        # (1) With precomputed lists in model.py:
        # driver_list = Gene.objects.filter(is_driver=True).order_by('gene_name')  # Needs: (is_driver=True), not just: (is_driver)

        driver_list = Gene.objects.raw("SELECT G.gene_name, G.entrez_id, G.full_name, G.prevname_synonyms, G.ensembl_id, G.hgnc_id, "
                                      + "COUNT(DISTINCT D.pmid) AS driver_num_studies, "
                                      + "COUNT(DISTINCT D.histotype) AS driver_num_histotypes, "
                                      + "COUNT(DISTINCT D.target) AS driver_num_targets, "
                                      + group_concat('D.histotype') + " AS driver_histotype_list, "
                                      + group_concat('D.pmid') + " AS driver_study_list "
#                                      + "FROM gendep_dependency D INNER JOIN gendep_gene G ON (D.driver = G.gene_name) "                                      
#                                      + "FROM gendep_dependency D INNER JOIN gendep_gene G ON (D.driver_entrez = G.entrez_id) "   # Now using Entrez_id as primary key for Gene
                                      + "FROM gendep_dependency D INNER JOIN gendep_gene G ON (D.driver = G.entrez_id) "   # Now using Entrez_id as primary key for Gene                                      
#                                      + "GROUP BY D.driver_entrez ORDER BY G.entrez_id ASC"
                                      + "GROUP BY D.driver ORDER BY G.gene_name ASC"                                      
                                      )
                                      
    else: html_error("build_driver_list() Unexpected page: '%s'" %(webpage))
    
    print(driver_list.query)
    
    return driver_list


def build_driver_histotype_study_list(webpage):
    if webpage == 'searchpage':
        driver_histotype_study_list = Gene.objects.raw("SELECT G.gene_name, D.driver AS entrez_id, D.histotype, "
                                      + group_concat('D.pmid') + " AS study_list "
                                      + "FROM gendep_dependency D INNER JOIN gendep_gene G ON (D.driver = G.entrez_id) "  # Now using Entrez_id as primary key for Gene
                                      + "GROUP BY D.driver, D.histotype ORDER BY G.gene_name, D.histotype ASC"
                                      )
    #elif webpage == 'driverspage':                                      
    else: html_error("build_driver_histotype_study_list() Unexpected page: '%s'" %(webpage))

    print(driver_histotype_study_list.query)
    #for d in driver_histotype_study_list:
    #    print(d.gene_name,d.entrez_id,d.histotype,d.study_list)
    return driver_histotype_study_list




def sort_list(list):
    return ','.join( sorted(list.split(',')) )
  

def index(request, search_by = 'driver', gene_name='', histotype_name='', study_pmid=''):   # Add entrez_id as parameter in future ?
    """ Sets the javascript arrays for driver, histotypes and studies within the main home/index page.
    As the index page can be called with specified values, eg: '.../driver/ERBB2/PANCAN/26947069/'
    Then calls the 'index.html' template to create the webpage.
    The 'search_by' is usually by driver, but for the "SearchByTarget" webpage, it will be set to 'target' """
    
    # Obtain the list of driver genes for the autocomplete box.
    # (Or for the 'Search-ByTarget' webpage, get the list of target genes).
    
    if is_search_by_driver(search_by):
        driver_list = build_driver_list('searchpage')
        driver_histotype_study_list = build_driver_histotype_study_list('searchpage')
        target_list = []
    else: 
        # This needs: (is_target=True), not just: (is_target)
        target_list = Gene.objects.filter(is_target=True).only("gene_name", "entrez_id", "full_name", "prevname_synonyms").order_by('gene_name')        
        driver_list = []
        driver_histotype_study_list = []

    # From testing the three different methods give the sample results
    #print(driver_list.query)
    #print("driver\tfullname\tsynonyms\thistotypes\tstudies")
    #with open("junk123.orm","w") as f:
    #  print("Writing .......")
    #  for d in driver_list:
        #print(d.gene_name,"\t",d.full_name,"\t",d.prevname_synonyms,"\t", sort_list(d.driver_histotype_list),"\t", sort_list(d.driver_study_list))  # print(row.driver_id, row.histotypes)  row['driver_id'],row['histotypes'],row["studies"]        
        #f.write("%s\t%s\t%s\t%s\t%s\n" %(d.gene_name, d.full_name, d.prevname_synonyms, sort_list(d.driver_histotype_list), sort_list(d.driver_study_list)) )  # print(row.driver_id, row.histotypes)  row['driver_id'],row['histotypes'],row["studies"]
        #f.write("%s\t%s\t%s\t%s\t%s\n" %(d['driver_id'], d['full_name'], d['prevname_synonyms'], sort_list(d['driver_histotype_list']), sort_list(d['driver_study_list'])) )  # print(row.driver_id, row.histotypes)  row['driver_id'],row['histotypes'],row["studies"]


    # Retrieve the tissue, experiment type, and study data:
    histotype_list = Dependency.HISTOTYPE_CHOICES
       # Alternatively if using histotype table (in the 'models.py' instead of 'choices' list):  histotype_list = Histotype.objects.order_by('full_name')
    experimenttype_list = Study.EXPERIMENTTYPE_CHOICES
    study_list = Study.objects.order_by('pmid')
    
    # As this page could in future be called from the 'drivers' or 'targets' page, with the gene_name as a standard GET or POST parameter (instead of the Django '/gene_name' parameter option in url.py):
    # if (gene_name is None) or (gene_name == ''):
    #    gene_name = post_or_get_from_request(request, 'gene_name')
        
    # Set the default histotype to display in the Tissues menu:
    # Previously this defaulted to PANCAN (or "ALL_HISTOTYPES"), BUT now the tissue menu is populated by javascript after the user selects driver gene:
    # if histotype_name=="": histotype_name="PANCAN"
    if histotype_name is None: histotype_name='' 
    
    # Get the study short name (to display as default in the studies menu) for the study_pmid:
    study_short_name = get_study_shortname_from_study_list(study_pmid,study_list)

    # Get host IP (or hostname) To display the host in title for developing on localhost or pythonanywhere server:
    # current_url = request.get_full_path()
    # current_url = request.build_absolute_uri()
    # current_url =  request.META['SERVER_NAME']
    current_url =  request.META['HTTP_HOST']

    # Set the context dictionary to pass to the template. (Alternatively could add locals() to the context to pass all local variables, eg: return render(request, 'app/page.html', locals())
    context = {'search_by': search_by, 'gene_name': gene_name, 'histotype_name': histotype_name, 'study_pmid': study_pmid, 'study_short_name': study_short_name, 'driver_list': driver_list, 'driver_histotype_study_list': driver_histotype_study_list, 'target_list': target_list, 'histotype_list': histotype_list, 'study_list': study_list, 'experimenttype_list': experimenttype_list, 'current_url': current_url , 'settings_GOOGLE_ANALYTICS_KEY': settings.GOOGLE_ANALYTICS_KEY}
    return render(request, 'gendep/index.html', context)


def get_drivers(request):
    """ Returns list of driver genes in JSON format for the jquery-ui autocomplete searchbox AJAX mode """
    
    # if request.is_ajax(): # Users can also access this from API scripts so not always AJAX
    name_contains = request.GET.get('name', '')
    # jQuery autocomplete sends the query as "name" and it expects back three fields: id, label, and value, eg:
    # [ {"id": "ERBB2", "value":"ERBB2","label":"ERBB2, ...."},
    #   {"id": "ERBB3", "value":"ERBB3","label":"ERBB3, ...."},
    # ]

    # For each driver gene, the autocomplete box with display the 'label' then the 'value'.
    
    if name_contains == '':
        # Needs: (is_driver=True), not just: (is_driver)
        drivers = Gene.objects.filter(is_driver=True)
    else:    
        # drivers = Gene.objects.filter(is_driver=True, gene_name__icontains=name_contains)
        # To search in both: 'gene_name' or 'prevname_synonyms', need to use the 'Q' object:
        drivers = Gene.objects.filter(is_driver=True).filter( Q(gene_name__icontains=name_contains) | Q(prevname_synonyms__icontains=name_contains) )  # could add: | Q(full_name__icontains=name_contains)

    results = []
    for d in drivers.order_by('gene_name'):
        results.append({
            'id':    d.gene_name,
            'value': d.gene_name,
            'label': d.gene_name + ' : ' + d.full_name + ' : ' + d.prevname_synonyms
        })        
        
    # For a simpler result set could use, eg: 
    # results = list(Gene.objects.filter(gene_name__icontains=name_contains).values('gene_name'))
    
    return JsonResponse(results, safe=False) # needs 'safe=false' as results is an array, not dictionary.






def is_valid_ip(ip_address):
    """ Check validity of an IP address """
    try:
        ip = ipaddress.ip_address(u'' + ip_address)
        return True
    except ValueError as e:
        return False
    
def get_ip_address_from_request(request):
    """ Makes the best attempt to get the client's real IP or return the loopback """    
    # Based on: "easy_timezones.utils.get_ip_address_from_request": https://github.com/Miserlou/django-easy-timezones
    
    # On PythonAnywhere the loadbalancer puts the IP address received into the "X-Real-IP" header, and also passes the "X-Forwarded-For" header as a comma-separated list of IP addresses. The 'REMOTE_ADDR' contains load-balancer address.
    
    PRIVATE_IPS_PREFIX = ('10.', '172.', '192.', '127.')
    ip_address = ''
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if x_forwarded_for and ',' not in x_forwarded_for:
        if not x_forwarded_for.startswith(PRIVATE_IPS_PREFIX) and is_valid_ip(x_forwarded_for):
            ip_address = x_forwarded_for.strip()
    else:
        ips = [ip.strip() for ip in x_forwarded_for.split(',')]
        for ip in ips:
            if ip.startswith(PRIVATE_IPS_PREFIX):
                continue
            elif not is_valid_ip(ip):
                continue
            else:
                ip_address = ip
                break
    if not ip_address:
        x_real_ip = request.META.get('HTTP_X_REAL_IP', '') # PythonAnywhere load-balancer puts the real IP in this 'HTTP_X_REAL_IP'.
        if x_real_ip:
            if not x_real_ip.startswith(PRIVATE_IPS_PREFIX) and is_valid_ip(x_real_ip):
                ip_address = x_real_ip.strip()
    if not ip_address:
        remote_addr = request.META.get('REMOTE_ADDR', '') # On PythonAnywhere this is the load-balancer address.
        if remote_addr:
            if not remote_addr.startswith(PRIVATE_IPS_PREFIX) and is_valid_ip(remote_addr):
                ip_address = remote_addr.strip()
    if not ip_address:
        ip_address = '127.0.0.1'
    return ip_address
    
    
    
def send_an_email(emailfrom, emailto, emailreplyto, subject, text):
    """ Uses the 'mailgun.com' service (as free  PythonAnywhere accounts don't have SMTP access) """
    # mailgun.com records email in your logs: https://mailgun.com/cp/log 
    # Better to keep this API auth key in a separate file, not on github:
    response = requests.post(
        "https://api.mailgun.net/v3/sandboxfb49cd4805584358bdd5ee8d96240a09.mailgun.org/messages",
        auth=("api", "key-ff52850192b21b271260779529ebd491"),
        data={"from": emailfrom,
              "to": emailto,
              "h:Reply-To": emailreplyto,
              "subject": subject,
              "text": text
              })
    if not response.ok: print("Failed to send email as:", response.content)
    return response.ok
    

    
def log_comment(request):
    """ Log and email comments/queries from the 'contacts' page """
    # The user's input data is send by an HTML POST, not by Django url parameters as the message can be long:
    name = request.POST.get('name', '')
    emailreplyto = request.POST.get('email', '')
    comment = request.POST.get('comment', '')
    
    # Optional fields, which are currently commented out on the html template:
    #   interest = request.POST.get('interest', '')
    #   human = request.POST.get('human', '')  # Result of a simple maths test, to check user is not a web spam robot.
    
    # To store the timezone: in "cgdd/settings.py" set: USE_TZ=True    
    date = timezone.now()
    
    ip = get_ip_address_from_request(request)
        
    c = Comment.objects.create(name=name, email=emailreplyto, comment=comment, ip=ip, date=date)
        
    # Should probably check for email header injection attacks:  https://www.reddit.com/r/Python/comments/15n6dw/sending_emails_through_python_and_gmail/
    # But mailgun probably checks for this.

    emailfrom=emailreplyto # Needs to be a valid email address or might give an exception?

    # The emailto address needs to be authorised on the mailgun.com     
    emailto="cancergenetics@ucd.ie" # or: "Cancer Genetics <cancergenetics@ucd.ie>"
    #emailto="sbridgett@gmail.com"  # or: "Stephen <sbridgett@gmail.com>" for testing.

    subject="Cgenetics Comment/Query: "+str(c.id)

    # Datetime formatting: https://docs.python.org/3.5/library/datetime.html#strftime-strptime-behavior
    text = "From: "+name+" "+emailreplyto+"\nDate: " + date.strftime("%a %d %b %Y at %H:%M %Z") + "\n\n"+comment
    # https://docs.djangoproject.com/en/1.9/topics/i18n/timezones/
    
    email_sent = "Email sent to cgenetics" if send_an_email(emailfrom=emailfrom, emailto=emailto, emailreplyto=emailreplyto, subject=subject, text=text) else "Failed to send email, but your message was saved in our comments database."  # To the email could add: interest=interest

    context = {'name': name, 'email': emailreplyto, 'comment': comment, 'date': date, 'email_sent': email_sent}
    return render(request, 'gendep/log_comment.html', context, content_type=html_mimetype)
    

def get_histotype_full_name(histotype_name):
    """ Returns the human readable proper-case tissue name, eg: 
        if input is 'PANCAN' returns 'Pan cancer', or if input 'SOFT_TISSUE' returns 'Soft tissue' """
    if histotype_name == "ALL_HISTOTYPES":
        return "All tissues"
    else:
        return Dependency.histotype_full_name(histotype_name)


def get_study(study_pmid):
    """ Returns short study name (First author and year), for an imput Pub-Med Id """
    if study_pmid == "ALL_STUDIES":
        return "ALL_STUDIES"
    try:
        study = Study.objects.get(pmid=study_pmid)
    except ObjectDoesNotExist: # Not found by the objects.get()
        study = None
    return study        


# def get_gene(gene_name):
def get_gene(entrez_id):
    """ Returns the Gene object (row from the Gene table) for the input gene_name (eg. 'ERBB2') """
    # gene = None if gene_name == '' else Gene.objects.get(gene_name=gene_name)            
    # if gene_name=='':
    if entrez_id=='':
        return None
    try:
        #gene = Gene.objects.get(gene_name=gene_name)
        gene = Gene.objects.get(entrez_id=entrez_id)
    except ObjectDoesNotExist: # gene_name not found by the Gene.objects.get()
        gene = None
    return gene
    
    
def build_dependency_query(search_by, entrez_id, histotype_name, study_pmid, wilcox_p=0.05, order_by='wilcox_p', select_related=None):  # Now replaced by rawSQL query below.
    """ Builds the query used to extract the requested dependencies.
          search_by:      'driver' or 'target'
          entrez_id:      must be sepcified and in the Genes table
          histotype_name: can be "ALL_HISTOTYPES" or a histotype in the model
          study_pmid:     can be "ALL_STUDIES" or a study pubmed id in the Study table
          wilcox_p:       the Dependency table only contains the rows with wilcox_p <=0.05 so must be same or less than 0.05
          order_by:       defaults to wilcox_p, but could be 'target_id' or 'effect_size', etc
          select_related: can be None, or a string, or a list of strings (eg: ['driver__inhibitors', 'driver__ensembl_protein_id'] to efficiently select the inhibitors and protein_ids from the related Gene table in the one SQL query, rather than doing multiple SQL sub-queries later)
    """
    error_msg = ""

    # Now changed to using entrez_id in the Dependency table so need to check Gene table for name (or send entrez_id from browser):    
    if entrez_id == "":
        error_msg += 'Gene name is empty, but must be specified'
        return error_msg, None

    # Using driver_id=entrez_id (or target_id=entrez_id) avoids table join of (driver = gene):
    q = Dependency.objects.filter(driver_id=entrez_id) if is_search_by_driver(search_by) else Dependency.objects.filter(target_id=entrez_id)
        
    # As Query Sets are lazy, so can incrementally build the query, then it is evaluated once at end when it is needed:
    if histotype_name != "ALL_HISTOTYPES":
        q = q.filter( histotype = histotype_name ) # Correctly uses: =histotype_name, not: =histotype_full_name

    if study_pmid != "ALL_STUDIES":
        q = q.filter( study_id = study_pmid )  # Could use: (study = study) but using study_id should be more efficiewnt as no table join needed.

    # As the results are already filtered by R for wilcox_P<=0.05 then don't actually need to filter on this wilcox_p <= 0.05:
    # q = q.filter(wilcox_p__lte = wilcox_p) # Only list significant hits (ie: p<=0.05). '__lte' means 'less than or equal to'

    print("build_dependency Query SQL:",q.query)
    print("build_dependency select_related:",select_related)
        
    if select_related is not None: 
        if isinstance(select_related, str) and select_related != '':
            q = q.select_related(select_related)
        elif isinstance(select_related, list) or isinstance(select_related, tuple):
            for column in select_related:
                q = q.select_related(column)
        else:
            error_msg += " ERROR: *** Invalid type for 'select_related' %s ***" %(type(select_related))
            print(error_msg)
     
    if order_by != None and order_by != '':
        q = q.order_by(order_by)  # usually 'wilcox_p', but could be: order_by('target_id') to order by target gene name

    return error_msg, q


# Show entrez_id be the filter now instead of gene_name?
def build_rawsql_dependency_query(search_by, entrez_id, histotype_name, study_pmid, query_type, order_by='wilcox_p'): # wilcox_p=0.05, select_related=None): 
    """ Builds raw SQL query, which permits use of AS in SQL, and more efficient. https://docs.djangoproject.com/en/1.10/topics/db/sql/ 
    and overcomes problem that the latest Django 1.10 has with 'selected_related': https://code.djangoproject.com/ticket/24687 
    and http://eboreimeoikeh.com/zealcreationz.com/django/docs/releases/1.10.txt and http://fossies.org/diffs/Django/1.9.8_vs_1.10/tests/select_related/tests.py-diff.html """
    # As the results are already filtered by R for wilcox_P<=0.05 then don't actually need to filter on this wilcox_p <= 0.05

    error_msg = ''

    filter = "D.%s = %%s" %(search_by)  # AND D.wilcox_p <= %%s
    # Now changed to using entrez_id in the Dependency table so need to check Gene table for name (or send entrez_id from browser):
    # params = [gene_name] # , wilcox_p
    params = [entrez_id] # , wilcox_p

    # filter = "D.gene_name = %%s"   # AND D.wilcox_p <= %%s

    if histotype_name != "ALL_HISTOTYPES":
        filter += " AND D.histotype = %s" # Correctly uses: =histotype_name, not: =histotype_full_name        
        params.append(histotype_name)

    if study_pmid != "ALL_STUDIES":
        filter += " AND D.pmid = %s"  # Could use: (study = study) but using study_id should be more efficient as no table join needed.
        params.append(study_pmid)

    select = 'target' if search_by=='driver' else 'driver'

    columns = "D.id, D.%s AS entrez_id, D.wilcox_p, D.effect_size, D.zdiff, D.interaction, D.pmid, D.multi_hit" %(select)  # Raw query must include the primary key (D.id). Should entrez_id be added now as is primary key to Gene table now?

    # related_columns = ", G.inhibitors, G.ensembl_protein_id"
    # related_join = " INNER JOIN gendep_gene G ON (D.%s = G.gene_name)" %(select) # Used for both query_types.
    related_columns = ", G.gene_name, G.inhibitors, G.ensembl_protein_id"
    related_join = " INNER JOIN gendep_gene G ON (D.%s = G.entrez_id)" %(select) # Used for both query_types.

    if query_type == 'dependency_gene_study':
#        related_columns += ", G.full_name, G.entrez_id, G.ensembl_id, G.prevname_synonyms, S.short_name, S.experiment_type, S.title"  # don't need 'study__pmid' (as is same as d.study_id)
        related_columns += ", D.histotype, G.full_name, G.ensembl_id, G.prevname_synonyms, S.short_name, S.experiment_type, S.title"  # don't need 'study__pmid' (as is same as d.study_id)
        related_join += " INNER JOIN gendep_study S ON (D.pmid = S.pmid)"
    elif query_type != 'dependency_gene':
        error_msg += " ERROR: *** Invalid 'query_type': %s ***" %(query_type)

    # Not searching for: gendep_dependency.driver, gendep_dependency.mutation_type, gendep_dependency.boxplot_data, etc

    rawsql = ("SELECT " + columns + related_columns +
              " FROM gendep_dependency D" + related_join +
              " WHERE (%s) ORDER BY D.%s ASC") %(filter, order_by)

    print("build_rawsql:",rawsql)
    return error_msg, Dependency.objects.raw(rawsql, params)

        

def gene_ids_as_dictionary(gene):
    """ To return info about alternative gene Ids as dictionary, for an JSON object for AJAX """
    return {
        'gene_name': gene.gene_name,
        'entrez_id': gene.entrez_id,
        'ensembl_id': gene.ensembl_id,
        'ensembl_protein_id': gene.ensembl_protein_id,
        'vega_id': gene.vega_id,
        'omim_id': gene.omim_id,
        'hgnc_id': gene.hgnc_id,
        'cosmic_id': gene.cosmic_id,
        'uniprot_id': gene.uniprot_id
        }

def gene_info_as_dictionary(gene):
    """ To return info about the gene as a JSON object for AJAX """
    return {    
        'gene_name': gene.gene_name,
        'full_name': gene.full_name,
        'synonyms': gene.prevname_synonyms,
        'ids': gene_ids_as_dictionary(gene),
        }
    

# Should entrez_id be a parameter now, as is primary key?    
def get_dependencies(request, search_by, entrez_id, histotype_name, study_pmid):
    """ Fetches the dependency data from cache (if recent same query) or database, for the main search result webpage.
    After "Search" button on the "index.html" page is pressed an AJAX requst sends four fields: search_by, entrez_id, histotype, and study_pmid.
    For paginated table, could add [start_row, and number_of_rows to return]
    Returns JSON formatted data for the dependency search result table, or an error message in JSON format.
    GET request is faster than POST, as POST makes two http requests, GET makes one, the Django url parameters are a GET request.
    """
    print("In get_dependencies: ",request, search_by, entrez_id, histotype_name, study_pmid)
    
    timing_array = []  # Using an array to preserve order of times on output.
    start = datetime.now()
    
    ajax_results_cache_version = '3' # version of the data in the database and of this JSON format. Increment this on updates that change the database data or this JSON format. See: https://docs.djangoproject.com/en/1.9/topics/cache/#cache-versioning
    
    # Avoid storing a 'None' value in the cache as then difficult to know if was a cache miss or is value of the key
    # cache_key = search_by+'_'+gene_name+'_'+histotype_name+'_'+study_pmid+'_v'+ajax_results_cache_version
    cache_key = search_by+'_'+entrez_id+'_'+histotype_name+'_'+study_pmid+'_v'+ajax_results_cache_version
    cache_data = cache.get(cache_key, 'not_found') # To avoid returning None for a cache miss.
    if cache_data != 'not_found': 
        # start = get_timing(start, 'Retrieved from cache', timing_array)
        # The 'timings': timing_array in the cached version is saved from the actual previous query execution, is not the timing for retrieving from the cache.
        return HttpResponse(cache_data, json_mimetype) # version=ajax_results_cache_version)

    search_by_driver = is_search_by_driver(search_by) # otherwise is by target
    select_related = [ 'target__inhibitors', 'target__ensembl_protein_id' ] if search_by_driver else [ 'driver__inhibitors', 'driver__ensembl_protein_id' ]

    #print("build_dependency_query:", "search_by:",search_by, "gene_name:",gene_name, "histotype_name:",histotype_name, "study_pmid:",study_pmid, "select_related:",select_related)
    print("build_dependency_query:", "search_by:",search_by, "entrez_id:",entrez_id, "histotype_name:",histotype_name, "study_pmid:",study_pmid, "select_related:",select_related)    

    RAW = True
    if RAW:
      error_msg, dependency_list = build_rawsql_dependency_query(search_by, entrez_id, histotype_name, study_pmid, order_by='wilcox_p', query_type='dependency_gene') 
    else:
      # Specify 'select_related' columns on related tables, otherwise the template will do a separate SQL query for every dependency row to retrieve the driver/target data (ie. hundreds of SQL queries on the Gene table)
      # Can add more select_related columns if needed, eg: for target gene prevname_synonyms: target__prevname_synonyms    
      # error_msg, dependency_list = build_dependency_query(search_by, gene_name, histotype_name, study_pmid, order_by='wilcox_p', select_related=select_related) 
      error_msg, dependency_list = build_dependency_query(search_by, entrez_id, histotype_name, study_pmid, order_by='wilcox_p', select_related=select_related)
      
    if error_msg != '': return json_error("Error: "+error_msg)
      
    
    print("Query SQL:",dependency_list.query)
    
    # gene = get_gene(gene_name)
    gene = get_gene(entrez_id)
    # if gene is None: return json_error("Error: Gene '%s' NOT found in Gene table" %(gene_name))
    if gene is None: return json_error("Error: Gene entrez_id '%s' NOT found in Gene table" %(entrez_id))
    
    # Only need current_url to include it in title/browser tab on hoover, for testing.
    #current_url =  request.META['HTTP_HOST']  # or: request.META['SERVER_NAME']

    start = get_timing(start, 'Query setup', timing_array)
        
    results = []
    csv = ''
    div = ';' # Using semicolon as the div, as comma may be used to separate the inhibitors
    count = 0
    
    # "The 'iterator()' method ensures only a few rows are fetched from the database at a time, saving memory, but aren't cached if needed again in this function. This iteractor version seems slightly faster than non-iterator version.
#    for d in dependency_list.iterator(): <-- RawQuery doesn't have iterator()
    for d in dependency_list:
      count += 1
      if RAW:
        #interaction = d.interaction
        #if interaction is None: interaction = ''  # shouldn't be None, as set by ' add_ensembl_proteinids_and_stringdb.py' script to ''.
        
        #interation_protein_id = d.target.ensembl_protein_id if search_by_driver else d.driver.ensembl_protein_id
        #if interation_protein_id is None: interation_protein_id = ''  # The ensembl_protein_id might be empty.
        #interaction += '#'+interation_protein_id  # Append the protein id so can use this to link to string-db.org

        #inhibitors = d.target.inhibitors if search_by_driver else d.driver.inhibitors
        #if inhibitors is None: inhibitors = '' # shouldn't be None, as set by 'drug_inhibitors.py' script to ''.
        
        # For driver or target below, the '_id' suffix gets the underlying gene name, rather than the foreign key Gene object, so more efficient as no SQL join needed: https://docs.djangoproject.com/en/1.9/topics/db/optimization/#use-foreign-key-values-directly
        # Similarily 'study_id' returns the underlying pmid number from Dependency table rather than the Study object.
        # wilcox_p in scientific format with no decimal places (.0 precision), and remove python's leading zero from the exponent.
        results.append([
                    d.gene_name,  # WAS:  d.target_id if search_by_driver else d.driver_id,
                    # Optionally could add: d.entrez_id,
                    format(d.wilcox_p, ".0e").replace("e-0", "e-"),
                    format(d.effect_size*100, ".1f"),  # As a percentage with 1 decimal place
                    format(d.zdiff,".2f"), # Usually negative. two decomal places
                    # d.histotype,
                    d.study_id,
                    d.multi_hit,
                    d.interaction + '#' + d.ensembl_protein_id,
                    d.inhibitors
                    ])
                            
      else: # Not RAW sql        
        interaction = d.interaction
        if interaction is None: interaction = ''  # shouldn't be None, as set by ' add_ensembl_proteinids_and_stringdb.py' script to ''.
        
        interation_protein_id = d.target.ensembl_protein_id if search_by_driver else d.driver.ensembl_protein_id
        if interation_protein_id is None: interation_protein_id = ''  # The ensembl_protein_id might be empty.
        interaction += '#'+interation_protein_id  # Append the protein id so can use this to link to string-db.org

        inhibitors = d.target.inhibitors if search_by_driver else d.driver.inhibitors
        if inhibitors is None: inhibitors = '' # shouldn't be None, as set by 'drug_inhibitors.py' script to ''.
        
        # For driver or target below, the '_id' suffix gets the underlying gene name, rather than the foreign key Gene object, so more efficient as no SQL join needed: https://docs.djangoproject.com/en/1.9/topics/db/optimization/#use-foreign-key-values-directly
        # Similarily 'study_id' returns the underlying pmid number from Dependency table rather than the Study object.
        # wilcox_p in scientific format with no decimal places (.0 precision), and remove python's leading zero from the exponent.
        results.append([
                    d.target_id if search_by_driver else d.driver_id,
                    format(d.wilcox_p, ".0e").replace("e-0", "e-"),
                    format(d.effect_size*100, ".1f"),  # As a percentage with 1 decimal place
                    format(d.zdiff,".2f"), # Usually negative. two decomal places
                    # d.histotype,
                    d.study_id,
                    d.multi_hit,
                    interaction,
                    inhibitors # Formatted above
                    ])
                    

    start = get_timing(start, 'Dependency results', timing_array)
    
    # results_column_names = ['Target','Wilcox_p','Effect_size','ZDiff','Histotype','Study_pmid','Inhibitors','Interactions'] # Could add this to the returned 'query_info'

    query_info = {'search_by': search_by,
                  'gene_entrez': entrez_id,
                  'gene_name': gene.gene_name,
                  'gene_full_name': gene.full_name,
                  'gene_synonyms': gene.prevname_synonyms,
                  'gene_alteration_considered': gene.alteration_considered,  # alteration_considered only applies to driver genes.
                  'histotype_name': histotype_name,
                  'study_pmid': study_pmid,
                  'dependency_count': count, # should be same as: dependency_list.count(), but dependency_list.count() could be another SQL query. # should be same as number of elements passed in the results array.
                  }
                  # 'current_url': current_url # No longer needed.
                
    data = json.dumps({
        'success': True,
        'timings': timing_array,
        'query_info': query_info,
        'gene_ids': gene_ids_as_dictionary(gene),
        'results': results
        }, separators=[',',':']) # The default separators=[', ',': '] includes whitespace which I think make transfer to browser larger. As ensure_ascii is True by default, the non-asciii characters are encoded as \uXXXX sequences, alternatively can set ensure_ascii to false which will allow unicode I think.
    
    start = get_timing(start, 'Json dump', timing_array) # Although too late to add this time to the json already encoded above.

    cache.set(cache_key, data, version=ajax_results_cache_version) # could use the add() method instead, but better to update anyway.
    # Could gzip the cached data (using GZip middleware's gzip_page() decorator for the view, or in code https://docs.djangoproject.com/en/1.9/ref/middleware/#module-django.middleware.gzip )
    # GZipMiddleware will NOT compress content if any of the following are true:
    #  - The content body is less than 200 bytes long.
    #  - The response has already set the Content-Encoding header.
    #  - The request (the browser) hasn’t sent an Accept-Encoding header containing gzip.
    # Another option is using cache_control() permit browser caching by setting the Vary header: https://docs.djangoproject.com/en/1.9/topics/cache/#using-vary-headers
    # "(Note that the caching middleware already sets the cache header’s max-age with the value of the CACHE_MIDDLEWARE_SECONDS setting. If you use a custom max_age in a cache_control decorator, the decorator will take precedence, and the header values will be merged correctly.)"
    # https://www.pythonanywhere.com/forums/topic/376/
    # and example of gzip using flask: https://github.com/closeio/Flask-gzip
    #  https://github.com/closeio/Flask-gzip/blob/master/flask_gzip.py

    #print(timing_array) # To django console/server log
    return HttpResponse(data, content_type=json_mimetype) # As data is alraedy in json format, so not using JsonResponse(data, safe=False) which would try to convert it to JSON again.
    


def get_boxplot(request, dataformat, driver_name, target_name, histotype_name, study_pmid):
    """ Returns data for plotting the boxplots, in JSON or CSV format
    The 'target_variant' parameter is no longer used for the Achilles data, as only the target_variant with the best wilcox_p value is stored in the Dependency table """
    try:    
        # d = Dependency.objects.get(driver_id=driver_name, target_id=target_name, histotype=histotype_name, study_id=study_pmid)
        d = Dependency.objects.get(driver__gene_name=driver_name, target__gene_name=target_name, histotype=histotype_name, study_id=study_pmid)
        
    except ObjectDoesNotExist: # ie. not found by the objects.get()
        error_msg = "Error, Dependency: driver='%s' target='%s' tissue='%s' study='%s' NOT found in Dependency table" %(driver_name, target_name, histotype_name, study_pmid)
        if dataformat[:4] == 'json': # for request 'jsonplot' or 'jsonplotandgene'
          return json_error(error_msg)
        else:  
          return plain_error(error_msg)
          
    if dataformat == 'csvplot':
        return HttpResponse(d.boxplot_data, content_type=csv_mimetype)

    if dataformat == 'jsonplot':
        return JsonResponse({'success': True, 'boxplot': d.boxplot_data}, safe=False)
   
    if dataformat == 'jsonplotandgene': # when browser doesn't already have target gene_info and ncbi_summary cached.
        try:
            gene = Gene.objects.get(gene_name=target_name)
            gene_info = gene_info_as_dictionary(gene);
            gene_info['ncbi_summary'] = gene.ncbi_summary  # To include the gene's ncbi_summary
            return JsonResponse( { 'success': True,
                                   'gene_info': gene_info,
                                   'boxplot': d.boxplot_data },
                                 safe=False )
        except ObjectDoesNotExist: # Not found by the objects.get()                    
            return json_error( "Error, Gene: target='%s' NOT found in Gene table" %(target_name) )

    elif dataformat=='csv' or dataformat=='download': 
        # 'csv' is for users to request the boxplot data via API
        # 'download' to for the 'Download as CSV' button on the SVG boxplots
        lines = d.boxplot_data.split(';')
        
        lines[0] = "Tissue,CellLine,Zscore,Altered";
        # This first line is the count, range, and boxplot_stats.
        
        # As this range and boxplot_stats are now calculated by the Javasscript in svg_boxplots.js, this line can be removed from future R output, so in future we need to prepend to the list, rather than replacing the first line here:
        #  lines.insert(0, "Tissue,CellLine,Zscore,Altered")
        # or just: 
        #  response = HttpResponse("Tissue,CellLine,Zscore,Altered\n" + (d.boxplot_data.replace(";","\n")), content_type=csv_mimetype)
        response = HttpResponse("\n".join(lines), content_type=csv_mimetype)
        if dataformat=='download':
            # Add to the HttpResponse object with the CSV/TSV header and downloaded filename:
            dest_filename = ('%s_%s_%s_pmid%s.csv' %(driver_name,target_name,histotype_name,study_pmid)).replace(' ','_') # To also replace any spaces with '_'
            # NOTE: Using .csv as Windows (and Mac) file associations will then know to open file with Excel, whereas if is .tsv then Windows won't open it with Excel.
            response['Content-Disposition'] = 'attachment; filename="%s"' %(dest_filename)
        return response
            
    else:
        print("*** Invalid dataformat requested for get_boxplot() ***")
        return html_error("Error, Invalid dataformat '"+dataformat+"' requested for get_boxplot()")
        
        
    
def stringdb_interactions(required_score, protein_list):
    """ Retrieve list of protein_ids with interaction of >=required_score
         'required_score' is typically 400, or 700 (for 40% or 70% confidence)
         'protein_list' is ensembl protein_ids separated with semicolons ';'
    NOTE: The pythonanywhere.com free account blocks requests to servers not on their whitelist. String-db.org has now been added to their whitelist, so this function works ok on free or paid accounts.
    This function creates a request in format: http://string-db.org/api/psi-mi-tab/interactionsList?network_flavor=confidence&limit=0&required_score=700&identifiers=9606.ENSP00000269571%0D9606.ENSP00000357883%0D9606.ENSP00000345083
    """
    
    stringdb_options="network_flavor=confidence&species=9606&limit=0&required_score="+required_score;    
    # The online interactive stringdb uses: "required_score" 400, and "limit" 0 (otherwise by default string-db will add 10 more proteins).  Optionally add parameter:  &additional_network_nodes=0
    
    protein_list = protein_list.replace(';', '%0D')  # Replace semicolon with the url encoded newline character that String-db expects between protein ids.

    url = "http://string-db.org/api/psi-mi-tab/interactionsList?"+stringdb_options+"&identifiers="+protein_list;
    
    # For very large result sets could use streaming: http://stackoverflow.com/questions/16870648/python-read-website-data-line-by-line-when-available
    # import requests
    # r = requests.get(url, stream=True)
    # for line in r.iter_lines():
    #   if line: print line

    req = Request(url)
    try:
        response = urlopen(req)
    except URLError as e:
        if hasattr(e, 'reason'):   # The reason for this error. It can be a message string or another exception instance.
            if isinstance(e.reason, str):
                return False, "We failed to reach a server: " + e.reason
            else:    
                raise e.reason
        elif hasattr(e, 'code'):
            return False, "The server couldn't fulfill the request. Error code: " + e.code
    else:  # response is fine
        return True, response.read().decode('utf-8').rstrip().split("\n") # read() returns 'bytes' so need to convert to python string


def get_stringdb_interactions(request, required_score, protein_list=None):
    """ Returns the subset of protein protein_list that string-db reports have interactions with at least one other protein in the protein_list. This is to remove the unconnected proteins from the image """
    
    # The request can be optionally be sent by an HTML GET or POST. POST means no limit to number of proteins sent, whereas GET or Django url() params are limited by length of the URL the webbrowser permits.
    if (protein_list is None) or (protein_list == ''):
        protein_list = post_or_get_from_request(request,'protein_list')    
    
    # Fetch the subset of protein_list that  have actual interactions with other proteins in the list:
    success, response = stringdb_interactions(required_score, protein_list)

    if not success: return plain_error('ERROR: '+response)

    if response=='': return PlainResponse("") # No interacting proteins.
    # was: or response=="\n", but the newline in empty response is rstrip'ed in stringdb_interactions()
    
    # Dictionary to check later if returned protein was in original list:
    initial_protein_dict = dict((protein,True) for protein in protein_list.split(';'))
    
    err_msg = ''        
    final_protein_dict = dict()
    for line in response:
        if line == '': continue
        cols = line.rstrip().split("\t")
        if len(cols)<2: err_msg+="\nNum cols = %d (but expected >=2) in line: '%s'" %(len(cols),line.rstrip())
         
        for i in (0,1): # col[0] and col[1] are the pair of interacting proteins
            protein = cols[i].replace('string:', '') # as returned ids are prefixed with 'string:'
            if protein in initial_protein_dict: final_protein_dict[protein] = True
            else: err_msg+="\n*** Protein%d returned '%s' is not in original list ***" %(i+1,protein)
            
    if err_msg != '':
        print(err_msg)
        return plain_error('ERROR:'+err_msg)
            
    protein_list2 = ';'.join(final_protein_dict.keys())
    return PlainResponse(protein_list2)

    
    
def cytoscape(request, required_score, protein_list=None, gene_list=None):
    """ Displays the cytoscape network of protein interactions.
    This receives the protein_list (eg: "9606.ENSP00000363021;9606.ENSP00000364815;9606.ENSP00000379888") and their corresponding gene_names as gene_list (eg. "RPA2;VARS;RPS8").
    Could just receive:
      - receive protein_list and lookup the corresponding gene_names in Gene table
      - or receive gene_list and lookup the corresponding protein ids in the Gene table
    NOTE: There is a {% csrf_token %} in the index.html template for this cytoscape post form, so may beed to add a @csrf_protect decorator.
    """
    if (protein_list is None) or (protein_list == ''):
        protein_list = post_or_get_from_request(request,'protein_list')

    if (gene_list is None) or (gene_list == ''):
        gene_list = post_or_get_from_request(request,'gene_list')
       
    success, response = stringdb_interactions(required_score, protein_list) # Fetches list of actual interactions
    
    if not success: return plain_error('ERROR: '+response)

    protein_list = protein_list.split(';')
    gene_list = gene_list.split(';')
    if len(protein_list) != len(gene_list):
        return plain_error('ERROR: lengths of gene_list and protein_list are different')

    # Create a dictionary to check later if returned protein was in original list, and what the gene_name was for that protein_id:            
    initial_nodes = dict()
    for i in range(0, len(protein_list)):
        initial_nodes[protein_list[i]] = gene_list[i]
    
    nodes = dict() # The protein nodes for cytoscape
    edges = dict() # The edges for cytoscape
    err_msg = ''
    for line in response:
      # if line:
        cols = line.rstrip().split("\t")
        if len(cols)<2: err_msg += "\nNum cols = %d (expected >=2) in line: '%s'" %(len(cols),line.rstrip())
        
        protein1 = cols[0].replace('string:', '') # as ids are prefixed with 'string:'
        if protein1 in initial_nodes:
            nodes[ protein1.replace('9606.', '') ] = True # remove the human tax id
        else: err_msg += "\n*** Protein1 returned as '%s' is not in original list ***" %(protein1)

        protein2 = cols[1].replace('string:', '')
        if protein2 in initial_nodes:
            nodes[ protein2.replace('9606.', '') ] = True
        else: err_msg += "\n*** Protein2 returned as '%s' is not in original list ***" %(protein2)

        edge = protein1+'#'+protein2
        edge_reversed = protein2+'#'+protein1
        if edge not in edges and edge_reversed not in edges:
            edges[edge] = True

    # node_list = sorted(nodes)

    # Convert node list of protein_ids, to list of gene_names:
    for protein in protein_list: # Can't use 'initial_nodes' here as it will be updated
        initial_nodes[protein.replace('9606.', '')] = initial_nodes.pop(protein)
        
    node_list = []
    for protein in nodes:
        node_list.append(initial_nodes[protein])
        
    edge_list = [] # Will be an array of tuples.
    for edge in edges:
        proteins = edge.split('#')
        if len(proteins) != 2:
            err_msg += "\n**** Expected two proteins in edge, but got: "+edge
        elif proteins[0].replace('9606.', '') not in initial_nodes:
            err_msg += "\n**** Protein1 %s in edge %s, isn't in the initial_nodes: %s" %(proteins[0],edge,initial_nodes)
        elif proteins[1].replace('9606.', '') not in initial_nodes:
            err_msg += "\n**** Protein2 %s in edge %s, isn't in the initial_nodes: %s" %(proteins[1],edge,initial_nodes)
        else:    
            node1 = initial_nodes[proteins[0].replace('9606.', '')]
            node2 = initial_nodes[proteins[1].replace('9606.', '')]
            edge_list.append( ( node1, node2 ) )

    if err_msg != '':
        print(err_msg)
        return plain_error('ERROR:'+err_msg)
    
    context = {'node_list': node_list, 'edge_list': edge_list}
    return render(request, 'gendep/cytoscape.html', context)


    
def gene_info(request, gene_name):
    try:        
        data = gene_info_as_dictionary( Gene.objects.get(gene_name=gene_name) )
        data['success'] = True # Add success: True to the json response.
        return JsonResponse(data, safe=False)
        
    except ObjectDoesNotExist: # Not found by the objects.get()
        return json_error("Gene '%s' NOT found in Gene table" %(gene_name))

        
def show_study(request, study_pmid):
    requested_study = get_object_or_404(Study, pk=study_pmid)
    # requested_study = get_object_or_404(Study, pk='Pending001') # Temportary for now.
    return render(request, 'gendep/study.html', {'study': requested_study})

def about(request):
    return render(request, 'gendep/about.html')

def tutorial(request):
    return render(request, 'gendep/tutorial.html')


def drivers(request):
    driver_list = build_driver_list('driverspage')
    histotype_list = Dependency.HISTOTYPE_CHOICES
    study_list = Study.objects.order_by('pmid')    
    context = {'driver_list': driver_list, 'histotype_list': histotype_list, 'study_list': study_list}
    return render(request, 'gendep/drivers.html', context)

def targets(request):
    target_list = Gene.objects.filter(is_target=True).order_by('gene_name')  # Needs: (is_driver=True), not just: (is_target)    
    context = {'target_list': target_list}
    return render(request, 'gendep/targets.html', context)
    
def tissues(request):
    histotype_list = Dependency.HISTOTYPE_CHOICES
    context = {'histotype_list': histotype_list}
    return render(request, 'gendep/tissues.html', context)
    
def studies(request):
    # study_list = Study.objects.order_by('pmid')
    # Could also add driver names lists in this query:
    study_list = Study.objects.raw("SELECT S.pmid, S.title, S.authors, S.experiment_type, S.journal, S.pub_date, S.num_targets, "
                                 + "COUNT(DISTINCT D.driver) AS num_drivers, "  # Or change to driver_entrez ?
                                 + "COUNT(DISTINCT D.histotype) AS num_histotypes, "                                 
                                 + group_concat('D.histotype') + " AS histotype_list, "
                                 + "COUNT(DISTINCT D.target) AS num_targets_in_db "  # Not displayed at present
                                 + "FROM gendep_dependency D INNER JOIN gendep_study S ON (D.pmid = S.pmid) "
                                 + "GROUP BY D.pmid ORDER BY S.pmid ASC"
                                 )
    histotype_list = Dependency.HISTOTYPE_CHOICES                                 
    context = {'study_list': study_list, 'histotype_list': histotype_list}
    return render(request, 'gendep/studies.html', context)

def faq(request):
    current_url =  request.META['HTTP_HOST'] # See download_dependencies_as_csv_file() for other, maybe better, ways to obtain currrent_url
    context = {'current_url': current_url}
    return render(request, 'gendep/faq.html', context)
    
def contact(request):
    return render(request, 'gendep/contact.html')

def news(request):
    # news_list = News.objects.filter(deleted=False).order_by('-id')    # for reverse id order (ie. most recently posted is first.
    
    # news_list = News.objects.order_by('-id')    # for reverse id order (ie. most recently posted is first.
    # Unused code for news template:   {% if news.img_filename not empty %}{% if news.img_link %}<a href="{{ news.img_link }}">{% endif %}<img src="{{ MEDIA_URL }}{{ news.img_filename }}" style="float: {{ news.img_align }};" />{% if news.img_link %}</a>{% endif %}{% endif %}
    # Want list in reverse order:
    news_list = (
    {'id':'2', 'content':'Data added from the <a href="https://www.ncbi.nlm.nih.gov/pubmed/28753431" target="_blank">McDonald(2017) [Project DRIVE ATARiS]</a> and <a href="https://www.ncbi.nlm.nih.gov/pubmed/28753430" target="_blank">Tsherniak(2017) [Project Achilles v2.20.2]</a> studies.', 'first_posted':'16-Oct-2017', 'last_edited':'16-Oct-2017'},
    {'id':'1', 'content':'The manuscript describing CancerDG.org is available <a href="http://www.cell.com/cell-systems/fulltext/S2405-4712(17)30230-2" target="_blank">here</a>.', 'first_posted':'14-July-2014', 'last_edited':'14-July-2014'},
    )

    context = {'news_list': news_list}
    return render(request, 'gendep/news.html', context)
    # If in admin mode then can edit the above news items? - ie. pass an extra parameter

def download(request):
    # download_list = Download.objects.filter(deleted=False).order_by('-id')    # for reverse id order (ie. most recently posted is first.
    
    # download_list = Download.objects.order_by('-id')    # for reverse id order (ie. most recently posted is first.
    # Unused code for news template:   {% if news.img_filename not empty %}{% if news.img_link %}<a href="{{ news.img_link }}">{% endif %}<img src="{{ MEDIA_URL }}{{ news.img_filename }}" style="float: {{ news.img_align }};" />{% if news.img_link %}</a>{% endif %}{% endif %}
    
    # Want list in reverse order:
    download_list = (
    {'id':'6', 'type':'SQLite Database of All dependencies',     'filename':'all_dependencies_17Oct2017.sqlite3',  'date_created':'17-Oct-2017', 'changes':'Added McDonald(2017) and Tsherniak(2017) data'},
    {'id':'5', 'type':'CSV text file of All dependencies',       'filename':'all_dependencies_17Oct2017.csv',      'date_created':'17-Oct-2017', 'changes':'Added McDonald(2017) and Tsherniak(2017) data'},
    {'id':'4', 'type':'CSV text file of Multi-hit dependencies', 'filename':'multihit_dependencies_17Oct2017.csv', 'date_created':'17-Oct-2017', 'changes':'Added McDonald(2017) and Tsherniak(2017) data'},
    {'id':'3', 'type':'SQLite Database of All dependencies',     'filename':'all_dependencies_1Apr2017.sqlite3',   'date_created':'1-Apr-2017',  'changes':'Original data'},
    {'id':'2', 'type':'CSV text file of All dependencies',       'filename':'all_dependencies_1Apr2017.csv',       'date_created':'1-Apr-2017',  'changes':'Original data'},
    {'id':'1', 'type':'CSV text file of Multi-hit dependencies', 'filename':'multihit_dependencies_1Apr2017.csv',  'date_created':'1-Apr-2017',  'changes':'Original data'},
    )

    context = {'download_list': download_list}
    return render(request, 'gendep/download.html', context)
    # If in admin mode then can edit the above news items? - ie. pass an extra parameter

"""
def edit_news(request):
    news_list = News.objects.filter(deleted=False).order_by('-id')    # for reverse id order (ie. most recently posted is first.
    # Unused code for news template:   {% if news.img_filename not empty %}{% if news.img_link %}<a href="{{ news.img_link }}">{% endif %}<img src="{{ MEDIA_URL }}{{ news.img_filename }}" style="float: {{ news.img_align }};" />{% if news.img_link %}</a>{% endif %}{% endif %}
    context = {'news_list': news_list}
    return render(request, 'gendep/news.html', context)
"""


search_by_driver_column_headings_for_download = ['Dependency', 'Dependency description', 'Entez_id',  'Ensembl_id', 'Ensembl_protein_id', 'Dependency synonyms', 'Wilcox P-value', 'Effect size', 'Z diff', 'Tissue', 'Study', 'PubMed Id', 'Experiment Type', 'Multiple hit', 'String interaction', 'Inhibitors', 'Boxplot link']                                 
search_by_target_column_headings_for_download = ['Driver', 'Driver description', 'Entez_id',  'Ensembl_id', 'Ensembl_protein_id', 'Driver synonyms', 'Wilcox P-value', 'Effect size', 'Z diff', 'Tissue',  'Study', 'PubMed Id', 'Experiment Type', 'Multiple hit', 'String interaction', 'Inhibitors', 'Boxplot link']


def download_dependencies_as_csv_file(request, search_by, entrez_id, histotype_name, study_pmid, delim_type='csv'):
    """ Creates then downloads the current dependency result table as a tab-delimited file.
    The download get link needs to contain: serach_by, gene, tissue, study parameters.

    In Windows at least, 'csv' files are associated with Excel, so will be opened by Excel. 
    To also associate a '.tsv' file with excel: In your browser, create a helper preference associating file type 'text/tab-separated values' and file extensions 'tsv' with application 'Excel'. Pressing Download will then launch Excel with the '.tsv' data file.
    
    ***** Remember to add to the select_related lists below if other columns are required for output.
    """
    
    # mimetype = html_mimetype # was: 'application/json'
    
    # see: http://stackoverflow.com/questions/6587393/resource-interpreted-as-document-but-transferred-with-mime-type-application-zip
    
    # For downloading large csv files, can use streaming: https://docs.djangoproject.com/en/1.9/howto/outputting-csv/#streaming-large-csv-files
    
    # request_method = request.method # 'POST' or 'GET'
    # if request_method != 'GET': return HttpResponse('Expected a GET request, but got a %s request' %(request_method), html_mimetype)
    # search_by = request.GET.get('search_by', "")  # It's an ajax POST request, rather than the usual ajax GET request
    # gene_name = request.GET.get('gene', "")
    # histotype_name = request.GET.get('histotype', "ALL_HISTOTYPES")
    # study_pmid = request.GET.get('study', "ALL_STUDIES")

    search_by_driver = is_search_by_driver(search_by) # Checks is valid and returns true if search_by='driver'

    # *** Remember to add to these select_related lists if other columns are required for output:
    RAW = True
    if RAW:
        error_msg, dependency_list = build_rawsql_dependency_query(search_by, entrez_id, histotype_name, study_pmid, order_by='wilcox_p', query_type='dependency_gene_study') 
    else:                
        select = 'target' if search_by_driver else 'driver'        
        # select_related = [ 'target__inhibitors', search_by, 'study' ] if search_by_driver else [ 'driver__inhibitors', search_by, 'study' ]   # Could add 'target__ensembl_protein_id' or 'driver__ensembl_protein_id'    
        # But for a more precise query (and so faster as retrieves fewer columns) is:
        select_related = [ select+'__gene_name', select+'__full_name', select+'__entrez_id', select+'__ensembl_id', select+'__ensembl_protein_id', select+'__prevname_synonyms', 
                         'study__short_name', 'study__experiment_type', 'study__title' ]  # don't need 'study__pmid' (as is same as d.study_id)
        error_msg, dependency_list = build_dependency_query(search_by, entrez_id, histotype_name, study_pmid, order_by='wilcox_p', select_related=select_related) # using 'select_related' will include all the Gene info for the target/driver in one SQL join query, rather than doing multiple subqueries later.
    
    if error_msg != '': return html_error("Error: "+error_msg)

    # print("Query SQL:",dependency_list.query)
    """
Query SQL:

Raw SQL would be:

SELECT 
  "gendep_dependency"."id", "gendep_dependency"."driver_name", "gendep_dependency"."target_name", "gendep_dependency"."mutation_type", "gendep_dependency"."wilcox_p", "gendep_dependency"."effect_size", "gendep_dependency"."za", "gendep_dependency"."zb", "gendep_dependency"."zdiff", "gendep_dependency"."interaction", "gendep_dependency"."pmid", "gendep_dependency"."study_table", "gendep_dependency"."histotype", "gendep_dependency"."boxplot_data",
  T3."gene_name", T3."original_name", T3."is_driver", T3."is_target", T3."full_name", T3."ensembl_id", T3."ensembl_protein_id", T3."entrez_id", T3."cosmic_id", T3."cancerrxgene_id", T3."omim_id", T3."uniprot_id", T3."vega_id", T3."hgnc_id", T3."prevname_synonyms", T3."driver_num_studies", T3."driver_study_list", T3."driver_num_histotypes", T3."driver_histotype_list", T3."driver_num_targets", T3."target_num_drivers", T3."target_num_histotypes", T3."inhibitors", T3."ncbi_summary",
  "gendep_study"."pmid", "gendep_study"."code", "gendep_study"."short_name", "gendep_study"."title", "gendep_study"."authors", "gendep_study"."experiment_type", "gendep_study"."abstract", "gendep_study"."summary", "gendep_study"."journal", "gendep_study"."pub_date", "gendep_study"."num_drivers", "gendep_study"."num_histotypes", "gendep_study"."num_targets"
FROM "gendep_dependency"
INNER JOIN "gendep_gene" T3 ON ("gendep_dependency"."target" = T3."gene_name")
INNER JOIN "gendep_study" ON ("gendep_dependency"."pmid" = "gendep_study"."pmid")
WHERE ("gendep_dependency"."driver_name" = ERBB2 AND "gendep_dependency"."histotype" = PANCAN AND "gendep_dependency"."wilcox_p" <= 0.05)
ORDER BY "gendep_dependency"."wilcox_p"
ASC

[08/Jun/2016 01:19:49] "GET /gendep/download_csv/xlsx/driver/ERBB2/PANCAN/ALL_STUDIES/ HTTP/1.1" 200 91646
    """

# ** Warning: If you are performing queries on MySQL, note that MySQL’s silent type coercion may cause unexpected results when mixing types. If you query on a string type column, but with an integer value, MySQL will coerce the types of all values in the table to an integer before performing the comparison. For example, if your table contains the values 'abc', 'def' and you query for WHERE mycolumn=0, both rows will match. To prevent this, perform the correct typecasting before using the value in a query.
#    from: https://docs.djangoproject.com/en/1.9/topics/db/sql/
    
    
    histotype_full_name = get_histotype_full_name(histotype_name)
    if histotype_full_name is None: return html_error("Error: Tissue '%s' NOT found in histotype list" %(histotype_name))
    
    study = get_study(study_pmid)
    if study is None: return html_error("Error: Study pmid='%s' NOT found in Study table" %(study_pmid))

    # Retrieve the host domain for use in the boxplot file links:
    # current_url =  request.META['HTTP_HOST']

    # Set the deliminators
    #   Another alternative would be: csv.unix_dialect
    #   csv.excel_tab doesn't display well.
    if delim_type=='csv':
        dialect = csv.excel
        content_type = csv_mimetype # can be called: 'application/x-csv' or 'application/csv'
    elif delim_type=='tsv':
        dialect = csv.excel_tab
        content_type = tab_mimetype
    elif delim_type=='xlsx':   # A real Excel file.
        content_type = excel_minetype
    else:
        return html_error("Error: Invalid delim_type='%s', as must be 'csv' or 'tsv' or 'xlsx'"%(delim_type))

    timestamp = time.strftime("%d-%b-%Y") # To add time use: "%H:%M:%S")

# Maybe better to fetch the gene_name here ....

    dest_filename = ('dependency_%s_%s_%s_%s_%s.%s' %(search_by,entrez_id,histotype_name,study_pmid,timestamp,delim_type)).replace(' ','_') # To also replace any spaces with '_' 
    # NOTE: Is '.csv' so that Windows will then know to open Excel, whereas if is '.tsv' then won't.

    # Create the HttpResponse object with the CSV/TSV header and downloaded filename:
    response = HttpResponse(content_type=content_type) # Maybe use the  type for tsv files?    
    response['Content-Disposition'] = 'attachment; filename="%s"' %(dest_filename)

    count = 0
    if not RAW: count = dependency_list.count()
    
    study_name = "All studies" if study_pmid=='ALL_STUDIES' else study.short_name
    # Using 'and' rather than comma below as a comma would split the line in csv files:
    # query_text = "%s='%s' and Tissue='%s' and Study='%s'" % (search_by.title(), gene_name, histotype_full_name, study_name)    
    query_text = "%s entrez_id='%s' and Tissue='%s' and Study='%s'" % (search_by.title(), entrez_id, histotype_full_name, study_name)
    
    file_download_text = "Downloaded from cancergd.org on %s" %(timestamp)
    
    column_headings = search_by_driver_column_headings_for_download if search_by_driver else search_by_target_column_headings_for_download

    if delim_type == 'csv' or delim_type == 'tsv':
        write_csv_or_tsv_file(response, dependency_list, search_by_driver, query_text, column_headings, file_download_text, delim_type, dialect)
    else: # elif delim_type=='xlsx': # Real excel file
        write_xlsx_file(response, dependency_list, search_by_driver, query_text, column_headings, file_download_text)
    
    return response
    


def write_csv_or_tsv_file(response, dependency_list, search_by_driver, query_text, column_headings, file_download_text, delim_type, dialect):
    # delim_type is:'csv' or 'tsv'
    
    import io
    # writer = csv.writer(response, dialect=dialect)
    response_stringio = io.StringIO()
    writer = csv.writer(response_stringio, dialect=dialect)
        # Maybe: newline='', Can add:  quoting=csv.QUOTE_MINIMAL, or csv.QUOTE_NONE, or csv.QUOTE_NONNUMERIC;  Dialect.delimiter,  Dialect.lineterminator

    writer.writerows([
    #     ["",file_description,], # Added extra first column so Excel knows from first row that is CSV. BUT don't know the row count here, so will prepend this at end to the html response.
        ["",file_download_text,],
        ["",],
    ]) # Note needs the comma inside each square bracket to make python interpret each line as list than that string

    writer.writerow(column_headings)  # The writeheader() with 'fieldnames=' parameter is only for the DictWriter object.

    # Now write the dependency rows:
    count = 0
    for d in dependency_list:  # Not using iteractor() as count() above will already have run the query, so is cached, as the rawsql doesn't support iterator()
        count+=1        
        # If could use 'target AS gene' or 'driver AS gene' in the django query then would need only one output:
        # Cannot use 'gene_id' as variable, as that will refer to the primary key of the Gene table, so returns a tuple.
#        gene_symbol = d.target_id if search_by_driver else d.driver_id  # d.target_id but returns name as a tuple, # same as: d.target.gene_name
#        gene_symbol = d.target_name_id if search_by_driver else d.driver_name_id  # d.target_id but returns name as a tuple, # same as: d.target.gene_name        
        
# As using RawSQL then the following aren't needed:        
#            gene_symbol= d.target.gene_name # d.target_id but returns name as a tuple, # same as: d.target.gene_name
#            full_name  = d.target.full_name
#            entrez_id  = d.target.entrez_id
#            ensembl_id = d.target.ensembl_id
#            protein_id = d.target.ensembl_protein_id
#            synonyms   = d.target.prevname_synonyms
#            inhibitors = d.target.inhibitors
#        else:  # search_by target
#            gene_symbol= d.driver.gene_name # d.driver_id, # same as: d.driver.gene_name
#            full_name  = d.driver.full_name
#            entrez_id  = d.driver.entrez_id
#            ensembl_id = d.driver.ensembl_id
#            protein_id = d.driver.ensembl_protein_id
#            synonyms   = d.driver.prevname_synonyms
#            inhibitors = d.driver.inhibitors
        #print(gene_symbol, d.target.gene_name)
        
#        print(help(d))

#        for x in d.__dict__.keys():
#            if not x.startswith('_'):
#                print(x,d.__dict__[x])
#        print("")                

        writer.writerow([
            d.gene_name, d.full_name, d.entrez_id, d.ensembl_id, d.ensembl_protein_id, d.prevname_synonyms,
            format(d.wilcox_p, ".1e").replace("e-0", "e-"),
            format(d.effect_size*100, ".1f"),  # As a percentage with 1 decimal place
            format(d.zdiff,".2f"), # Usually negative
            Dependency.histotype_full_name(d.histotype),  # was: d.get_histotype_display()
            d.short_name,  d.study_id,  d.experiment_type,
            d.multi_hit,            
            d.interaction,
            d.inhibitors
        ])
                # d.study_id is same as 'd.study.pmid'        
        # Could add weblinks to display the SVG boxplots by pasting link into webbrowser:
        # this 'current_url' is a temporary fix: (or use: StaticFileStorage.url )
        # 'http://'+current_url+'/static/gendep/boxplots/'+d.boxplot_filename()

        
    # Finally slose the StringIO file:
    file_description = "A total of %d dependencies were found for: " %(count) + query_text
    # Start with a comma or tab to add an extra first column so Excel knows from first row that is CSV.
    # The "\n" could be "\r\n" if windows dialect of csv writer was used:
    response.write( ("," if delim_type=='csv' else "\t") + file_description + "\n" + response_stringio.getvalue() )   # getvalue() similar to:  response_stringio.seek(0); response_stringio.read()
    response_stringio.close() # To free the memory.

           
           

def write_xlsx_file(response, dependency_list, search_by_driver, query_text, column_headings, file_download_text):    
#    elif delim_type=='xlsx': # Real excel file

    import xlsxwriter # need to install this 'xlsxwriter' python module

    # An advantage of Excel format is if import tsv file Excel changes eg. MARCH10 or SEP4 to a date, whereas creating the Excle file doesn't
    # Also can add formatting, better url links, and include box-plot images.
    # Can write directly to the response which is a file-like object. (Alternatively can write to io.stringio first.
    workbook = xlsxwriter.Workbook(response, {'in_memory': True})
    # As output is small, {'in_memory': True} avoids using temp files on server, and avoids the error: "HttpResponse has no attribute seek"
    # or: with xlsxwriter.Workbook(iobytes_output, {'in_memory': True}) as workbook: (then don't need to close() it)
        
    # From: https://groups.google.com/forum/#!topic/python-excel/0vWPLht7K64
    # Change the default font from Calibri 11 to Arial 10 (as Mac Numbers app doesn't have Calibri so needs to convert to MS font):
    workbook.formats[0].font_name = 'Arial'
    workbook.formats[0].font_size = 10
           
    ws = workbook.add_worksheet() # can have optional sheet_name parameter
    yellow = '#FFFFEE' # a light yellow
    bold = workbook.add_format({'bold': True}) # Add a bold format to use to highlight cells.
    # bold_cyan = workbook.add_format({'bold': True, 'bg_color': 'cyan'}) # Add a bold blue format.
    # bold_yellow = workbook.add_format({'bold': True, 'bg_color': yellow}) # Add a bold blue format.
    # bg_yellow = workbook.add_format({'bg_color': yellow})
    # But when use background colour then hides the vertical grid lines that separate the cells
    align_center = workbook.add_format({'align':'center'})
    exponent_format = workbook.add_format({'num_format': '0.00E+00', 'align':'center'}) # For wilcox_p (eg 1 x 10^-4).
    percent_format = workbook.add_format({'num_format': '0.00"%"', 'align':'center'}) # For effect_size.
    two_decimal_places = workbook.add_format({'num_format': '0.00', 'align':'center'}) # For Z-diff.

        
    # can also set border formats using:    set_bottom(), set_top(), set_left(), set_right()
    # also can set cell bg colours (eg: 'bg_color'), etc http://xlsxwriter.readthedocs.org/format.html

    description_row = 1 # As create the description at end when count is available.
    # ws.write_string( description_row, 1, file_description )
    ws.write_string( 2, 1, file_download_text )
    ws.write_row   ( 4, 0, column_headings, bold)
    #  ws.set_row(row, None, bold) # To make title row bold - but already set to bold above in write_row
    ws.set_column(0, 0, 12) # To make Gene name column (col 0) a bit wider
    ws.set_column(1, 1, 35) # To make Description column (col 1) wider
    ws.set_column(3, 4, 16) # To make ensembl ids (col 3 and 4) wider
    ws.set_column(5, 5, 35) # To make Synonyms column (col 5) wider
    ws.set_column(6, 13, 11) # To make columns 6 to 13 a bit wider
    ws.set_column(14, 14, 14) # To make Experiment_type (col 14) a bit wider
    row = 4 # The last row to writen

    # Now write the dependency rows:
    count = 0
    for d in dependency_list:  # Not using iteractor() as count() above will already have run the query, so is cached, as the rawsql doesn't support iterator()
        count+=1
        # If could use 'target AS gene' or 'driver AS gene' in the django query then would need only one output:        
        # Cannot use 'gene_id' as variable, as that will refer to the primary key of the Gene table, so returns a tuple.
        # gene_symbol = d.target_id if search_by_driver else d.driver_id  # d.target_id but returns name as a tuple, # same as: d.target.gene_name
                
        row += 1

        ws.write_string(row,   0, d.gene_name, bold)
        ws.write_string(row,   1, d.full_name)
        ws.write_string(row,   2, d.entrez_id)
        ws.write_string(row,   3, d.ensembl_id)
        ws.write_string(row,   4, d.ensembl_protein_id)
        ws.write_string(row,   5, d.prevname_synonyms)
        ws.write_number(row,   6, d.wilcox_p,    exponent_format)
        ws.write_number(row,   7, d.effect_size, percent_format)
        ws.write_number(row,   8, d.zdiff,       two_decimal_places)
        ws.write_string(row,   9, Dependency.histotype_full_name(d.histotype))
        ws.write_string(row,  10, d.short_name)
        ws.write_url(   row,  11, url=Study.url(d.study_id), string=d.study_id, tip='PubmedId: '+d.study_id+' : '+d.title)  # cell_format=bg_yellow  # d.study_id is same as 'd.study.pmid'
        # WAS:  ws.write_url(   row,  11, url=d.study.url(), string=d.study_id, tip='PubmedId: '+d.study_id+' : '+d.study.title)  # cell_format=bg_yellow  # d.study_id is same as 'd.study.pmid'
        ws.write_string(row,  12, d.experiment_type)
        ws.write_string(row,  13, d.multi_hit)
        ws.write_string(row,  14, d.interaction, align_center)
        ws.write_string(row,  15, d.inhibitors)
        # WAS: ws.write_string(row, 16, d.study.summary)
        
        # ADD THE FULL STATIC PATH TO THE url = .... BELOW:
        # ws.write_url(   row, 14, url = 'gendep/boxplots/'+d.boxplot_filename, string=d.boxplot_filename, tip='Boxplot image')
        # ws.insert_image(row, col, STATIC.....+d.boxplot_filename [, options]) # Optionally add the box-plots to excel file.

    # Finally: 
    file_description = "A total of %d dependencies were found for: " %(count) + query_text

    # Close the Excel file:
    ws.write_string( description_row, 1, file_description )
    workbook.set_properties({
        'title':    file_description,
        'subject':  'Cancer Genetic Dependencies',
        'author':   'CancerGD.org',
        'manager':  'Dr. Colm Ryan',
        'company':  'Systems Biology Ireland',
        'category': '',
        'keywords': 'Sample, Example, Properties',
        'comments': 'Created with Python and XlsxWriter. '+file_download_text,
        'status': '',
        'hyperlink_base': '',
    })
    workbook.close() # must close to save the contents.
    
    # xlsx_data = output.getvalue()
    # response.write(iobytes_output.getvalue())    # maybe add: mimetype='application/ms-excel'
    # or:
    # output.seek(0)
    # response = HttpResponse(output.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

