#!/usr/bin/env python

""" Script to import the CGD data into the database tables """
import sys, os, csv, re
import gzip  # To directly the compressed string db files without needing to uncompress them first.
from collections import defaultdict
import django
from django.db import  connection, transaction
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
import warnings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cgdd.settings")
django.setup()
from gendep.models import Study, Gene, Dependency 
from django.conf import settings  # To get the current database engine type (sqlite or mysql).

# Set input data file  names:
AlterationDetailsFile    = "./input_data/AlterationDetails.csv"
EntrezSummariesFile      = "./input_data/entrez_summaries.txt"
HgncCompleteSetFile      = "./input_data/hgnc_complete_set.txt"
ScreenDescriptionsFile   = "./input_data/ScreenDescriptions.txt"
StringDbEntrezGeneIdFile = "./input_data/entrez_gene_id.vs.string.v10.28042015.tsv"
StringDbProteinAliasFile = "./input_data/9606.protein.aliases.v10.5.txt"
StringDbProteinLinksFile = "./input_data/9606.protein.links.v10.5.txt"
DgiDrugTargetsFile       = "./input_data/dgi_drug_targets.txt"


"""In the SQLite database (used for development locally), the max_length parameter for fields
is ignored as the "numeric arguments in parentheses that following the type name (ex: "VARCHAR(255)")
are ignored by SQLite - SQLite does not impose any length restrictions (other than the large global
SQLITE_MAX_LENGTH limit) on the length of strings, ...." (unless use sqlites CHECK contraint option)
BUT MySQL does enforce max_length, so MySQL will truncate strings that are too long, (including keys
so loss of unique primary key) so need to check for data truncation, as it jsut gives a warning NOT an exception.
To convert the MySQL data truncation (due to field max_length being too small) into raising an exception
we use :"""

warnings.filterwarnings('error', 'Data truncated .*')

def progress(message): 
    """ To print progress messages to both stdout, and to stderr, as stdout usually redirected to a log file as large volume of output """ 
    if not sys.stdout.isatty(): print(message, file=sys.stderr)
    print("\n")
    print(message)


# Doing "bulk_create()" in smaller batches of 200 as on MySQL on PythonAnwhere.com, as trying to bulk insert many gives error: django.db.utils.OperationalError: (2006, 'MySQL server has gone away').
# 999 is the default for the bulk_create() batch_size parameter in Sqlite.
DB_BATCH_SIZE = 999 if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3' else 200   # 'django.db.backends.mysql'
print("** DB_BATCH_SIZE=",DB_BATCH_SIZE)

def db_bulk_insert(table, rows) :
    """
    Uses one SQL query to add multiple rows, so is faster than individual inserts.
    From Django docs: 
        The batch_size parameter controls how many objects are created in single query. 
        The default is to create all objects in one batch, except for SQLite where the default is such that at most 999 variables per query are used.
    """
    print("** STARTING BULK_CREATE of ",len(rows),"rows....")
    try:
        if isinstance(rows, dict): # Dictionary of lists
            table.objects.bulk_create(rows.values())
            #rows = {}
        else: # Assume is list or tuple
            table.objects.bulk_create(rows)
            #rows = []
    except Warning as warning:  # To report the row causing any data truncation error.
        # From the warning should be able to retrieve the row number, then just output that row:  Error: 1265 SQLSTATE: 01000 (WARN_DATA_TRUNCATED)  Message: Data truncated for column '%s' at row %ld
        # eg. regexp: "Data truncated for column '[^']+' at row \d+"   into vars: colname, irow
        # But just output all the rows array/dict for now:
        progress("\n***ERROR***:"+warning)
        print(warning.args)     # arguments stored in .args
        matches = re.match(r"Data truncated for column '([^']+)' at row (\d+)", warning, flags=0)
        if matches:
          print( "data truncation: Column %s Row %s" % (matches.group(1),matches.group(2)) )
          
        #for key,val in row.items():
        #    progress(key + ":" + val)
        for row in rows:
            progress(row)
        progress("\n")
        raise warning
    except Exception as exception:  # To report the row causing any data truncation error.        
        progress("\n***ERROR***:"+str(exception))
        print(exception.args)     # arguments stored in .args
        for row in rows:
           progress(row)
        progress("\n")
        raise exception

    
def add_gene_details() :
    """
    Populates the Gene table of the database. Adds names / symbols
    and a variety of IDs for different DBs (Ensembl / Uniprot / HGNC).
    Data is sourced from the HGNC complete set.
    """
    entrez_to_symbol = {}
    rows = []
    # The hgnc_complete_set.txt file contains unicode characters in the 'name' column, eg. the Greek symbols for Alpha and Beta, etc, so need to open it with utf-8 encoding:
    with open_file(HgncCompleteSetFile) as f :
        reader = csv.DictReader(f,delimiter="\t")
        for row in reader :
            if row['entrez_id'] and row['symbol']:
                synonyms = [] if row['alias_symbol']=='' else row['alias_symbol'].split("|")
                prev_names = [] if row['prev_symbol']=='' else row['prev_symbol'].split("|") # Need to check for empty prev_names, otherwise get [ '' ] then synonym_string becomes, eg: " | RHEB2 " or "PI3K | "
                synonym_string = " | ".join(list(set(synonyms).union(prev_names)))
                rows.append( Gene(
                    gene_name = row['symbol'], # eg. ERBB2
                    full_name  = row['name'], # eg. erb-b2 receptor tyrosine kinase 2
                    prevname_synonyms = synonym_string, # eg: NGL  (plus)  NEU|HER-2|CD340|HER2
                    entrez_id  = row['entrez_id'], # eg: 2064
                    ensembl_id = row['ensembl_gene_id'], # eg: ENSG00000141736
                    vega_id = row['vega_id'], # eg: OTTHUMG00000179300
                    hgnc_id = row['hgnc_id'].split(':')[1],
                    omim_id = row['omim_id'].split('|')[0], # eg. omim_id: 312095|465000
                    cosmic_id = row['cosmic'],
                    uniprot_id = row['uniprot_ids'].split('|')[0]
                    ) )
                if len(rows) >= DB_BATCH_SIZE:
                    db_bulk_insert(Gene, rows)  # Inserting in batches of eg. 100 is faster than one by one.
                    rows = []
                entrez_to_symbol[row['entrez_id']] = row['symbol']
                
        if len(rows)>0:
            db_bulk_insert(Gene, rows)  # Inserting any remaining as didn't reach 100.

    return entrez_to_symbol


def add_driver_details() :
    """
    Adds details of the alteration types considered for each driver
    """
    with open_file(AlterationDetailsFile) as f :
        reader = csv.DictReader(f, dialect='excel')
        for row in reader :
            entrez_id = row['Gene'].split('_')[1]
            mutation_type = row['Alterations Considered']
            try :
                g = Gene.objects.get(entrez_id=entrez_id)
                g.is_driver = True
                g.alteration_considered = mutation_type
                g.save()
            except ObjectDoesNotExist:
                progress("ERROR updating driver: %s" %(row))
    return            

    
def open_file(filename, mode='rt', encoding='utf-8'):
    """ Open file as gzipped if not already uncompressed. 'mode' is 'rt' for read the gzip files as Strings (instead of Bytes). Needs utf-8 encoding for protein.aliases file. """
    if os.path.exists(filename):
        f = open(filename, mode, encoding=encoding)
    elif os.path.exists(filename+'.gz'):
        f = gzip.open(filename+'.gz', mode, encoding=encoding)  # In earlier python versions (eg. python 3.2) need to wrap this as: f = io.TextIOWrapper(gzip.open(filename+'.gz', mode, encoding=encoding))
    else:
        raise FileNotFoundError("File '%s' file NOT found: " %(filename))
    return f
    
    
def add_ensembl_proteinids() :
    """
    Adds ENSEMBL Protein IDs for as many genes as possible. These are used for STRING.
    STRING-DB provides a mapping from ENTREZ IDs to ENSEMBL protein ids. However many 
    genes are not present in this mapping, including drivers, so we try to map them 
    using their ENSEMBL gene IDs or UNIPROT IDs using an additional 'alias' file provided 
    by STRING. 
    """
    entrez_to_ensemblpid = {}    
    ensemblg_to_ensemblpid = {}
    uniprot_to_ensemblpid = {}
    with open_file(StringDbEntrezGeneIdFile) as f:
        f.readline()
        reader = csv.reader(f,delimiter="\t")
        for r in reader :
            entrez = r[0]
            ensembl_pid = r[1].split('.')[1]
            entrez_to_ensemblpid[entrez] = ensembl_pid
    with open_file(StringDbProteinAliasFile) as f:
        for line in f :
            if 'ENSG' in line :
                parts = line.split("\t")
                ensemblg_to_ensemblpid[parts[1]] = parts[0].split('.')[1]
            elif 'BLAST_UniProt_AC' in line :
                parts = line.split("\t")
                uniprot_to_ensemblpid[parts[1]] = parts[0].split('.')[1]
    for gene in Gene.objects.all() :
        if gene.entrez_id in entrez_to_ensemblpid :
            gene.ensembl_protein_id = entrez_to_ensemblpid[gene.entrez_id]
            gene.save()
        elif gene.ensembl_id in ensemblg_to_ensemblpid :
            gene.ensembl_protein_id = ensemblg_to_ensemblpid[gene.ensembl_id]
            gene.save()
        elif gene.uniprot_id in uniprot_to_ensemblpid :
            gene.ensembl_protein_id = uniprot_to_ensemblpid[gene.uniprot_id]
            gene.save()
    return 

def add_inhibitor_details() :
    """
    Adds inhibitors for each gene, sourced from DGIdb
    """
    entrez_to_inhibitor = {}
    with open_file(DgiDrugTargetsFile) as f :
        reader = csv.DictReader(f,delimiter="\t")
        for row in reader :
            entrez_to_inhibitor[row['EntrezID']] = row['Inhibitors']
            
    for gene in Gene.objects.all() :
        if gene.entrez_id in entrez_to_inhibitor :
            gene.inhibitors = entrez_to_inhibitor[gene.entrez_id]
            gene.save()
    return

def add_entrez_summaries() :
    """
    Adds entrez summaries for each gene
    """
    entrez_to_summary = {}
    with open_file(EntrezSummariesFile) as f :
        reader = csv.DictReader(f,delimiter="\t")
        for row in reader :
            entrez_to_summary[row['EntrezID']] = row['Summary']
            
    for gene in Gene.objects.all() :
        if gene.entrez_id in entrez_to_summary :
            gene.ncbi_summary = entrez_to_summary[gene.entrez_id]
            gene.save()
    return

def add_studies() :
    """
    Adds details of the screens included
    """
    rows=[]
    with open(ScreenDescriptionsFile,"rU") as f :
        reader = csv.DictReader(f,delimiter="\t")
        for row in reader :
            if row['Study'][0] == '#':
                print("Skipping sudy '%s' as is commented out." %(row['Study']))
                continue # To skip commented out lines.
            rows.append( Study(pmid=row["PMID"], code = row['Code'], short_name = row['ShortName'], title = row["Title"], 
                authors = row["Authors"], abstract = row["Abstract"], summary = row["Summary"], experiment_type = row["Type"], 
                journal = row["Journal"], pub_date = row["Date"], num_targets = row["Targets"]) )
    if len(rows)>0: db_bulk_insert(Study, rows)
    return 
    
def add_dependency_file(study, filename, duplicates=False, exclude_tissues=[]) :
    """
    Reads the dependencies stored in 'filename' and associates
    them with the study PMID provided. Duplicates indicates whether
    a given source of depednencies contains multiple variants of a single
    gene. An example of this is the Achilles data (Cowley et al) which
    contains multiple distinct gene-level scores for a handful of genes.
    For these studies we store the CGD with the lower p-value (and 
    consequently must check if the CGD exists in the DB already).
    """
    try :
        study = Study.objects.get(pmid=study)
    except ObjectDoesNotExist :
        progress("ERROR, STUDY %s does not exist" %(study))
        return
    
    rows = []  # For bulk inserts.
    cgd_dict = {} # For tracking duplicates without needing slower sql db query.
    with open("./R_scripts/outputs/%s" % filename,"rU") as f :
        reader = csv.DictReader(f,delimiter="\t")
        for row in reader :
            wilcox_p = float(row['wilcox.p'])
            cles = float(row["CLES"])
            if wilcox_p >= 0.05 or cles < 0.65 :
               continue  # ie. only include dependencies if wilcox_p < 0.05 and cles >= 0.65
            tissue = row.get("tissue", "PANCAN") # As PANCAN data has no "tissue" column, so set to "PANCAN"
            if tissue in exclude_tissues :
               continue
            marker_entrez = row['marker'].split('_')[1]
            target_entrez = row['target'].split('_')[1]
            zdiff = float(row["ZDiff"])
            za = float(row["zA"])
            zb = float(row["zB"])
            
            try :
                driver = Gene.objects.get(entrez_id = marker_entrez)
                if not driver.is_driver :
                    print("Gene %s %s should have is_driver=True, but is %s" %(driver.gene_name, marker_entrez, driver.is_driver))
                target = Gene.objects.get(entrez_id = target_entrez)

                # if study=="28753430" and driver=="KRAS" and target=="A2M" and tissue=="HAEMATOPOIETIC_AND_LYMPHOID_TISSUE" :
                print("FOUND: %s %s %s %s" %(study,driver,target,tissue))

                if not target.is_target :
                    target.is_target=True
                    target.save()
            except ObjectDoesNotExist :
                print("Skipping row",row['marker'],row['target']) # As driver or marker not in the HGNC list of genes that were inserted into Gene table.
                continue

            if duplicates: # Check if this dependency exists already
#                existing_cgd = None
                key="%s:%s:%s:%s" %(driver, target, tissue, study)
#                if key in cgd_dict:  # in the batch update dictionary
#                    existing_cgd = cgd_dict[key]
#                elif Dependency.objects.filter(driver=driver, target=target, histotype=tissue, study=study).exists(): # or saved in the table
#                    existing_cgd = Dependency.objects.get(driver=driver, target=target, histotype=tissue, study=study)
                existing_cgd = cgd_dict.get(key, None)
                if existing_cgd is not None:
                    progress("Duplicate: "+key)
                    if existing_cgd.wilcox_p > wilcox_p :
                        existing_cgd.za = za
                        existing_cgd.zb = zb
                        existing_cgd.wilcox_p = wilcox_p
                        existing_cgd.zdiff = zdiff
                        existing_cgd.effect_size = cles
                        existing_cgd.boxplot_data = row["boxplot_data"]
                        
                        if existing_cgd.pk is not None: # Only save if already previously saved (ie. bulk_insert()'ed already) in the database (ie. has a primary key)
#                        if key not in cgd_dict:
                            existing_cgd.save()
                    continue
                    
            #print(key)
            dep = Dependency(driver = driver, target = target, wilcox_p = wilcox_p, za = za, zb = zb, zdiff = zdiff,
                            effect_size=cles, histotype = tissue, study = study, boxplot_data = row["boxplot_data"])
            if duplicates: cgd_dict[key] = dep
            rows.append(dep)
            if len(rows) >= DB_BATCH_SIZE:
                db_bulk_insert(Dependency, rows)  # Inserting in batches of eg. 100 is faster than one by one.
                rows = []
                
    if len(rows) >= 0:
        db_bulk_insert(Dependency, rows) # Inserting any remaining rows.
        #rows = []
        
    return



def add_dependencies() :
    """
    Reads the screens file which contains a list of screens and 
    associated dependency files. Then calls add_dependency_file
    to add each file to the database
    The 'exclude_tissues' is for excluding BREAST dependencies
    in the Marcotte2012 data as already these are a subset of the
    Marcotte (2016) data.
    """
    with open(ScreenDescriptionsFile,"rU") as f :
        reader = csv.DictReader(f,delimiter="\t")
        for row in reader :
            if row['Study'][0] == '#' : continue  # To skip commented out studies.
            pmid = row["PMID"]
            screens = row["CGD_files"].split(';')
            duplicates = row["DuplicateGenes"] == "1"
            exclude_tissues = row['ExcludeTissues'].strip()
            exclude_tissues = [] if exclude_tissues == '' else exclude_tissues.split(';')
            for s in screens :
                progress("   %s, Duplicates: %s, ExcludeTissues: %s" %(s,duplicates,exclude_tissues) )
                add_dependency_file(pmid,s,duplicates,exclude_tissues)
    return
        
def get_string_confidence(score) :
    """
    Converts STRING scores to a text description
    of the confidence of the interaction
    """
    if score >= 900 :
        return "Highest"
    elif score >= 700 :
        return "High"
    elif score >= 400 :
        return "Medium"
    else :
        return "Low"

  
def add_string_interactions() :
    """
    For every CGD we store details of whether it involves a gene pair
    known to functionally interact according to STRING. Only medium 
    confidence (score >= 400) or higher interactions are stored. We 
    manually set all self-self interactions to 'highest confidence'
    """
    driver_ids = set()
    drivers = Gene.objects.filter(is_driver = True)
    for d in drivers :
        if d.ensembl_protein_id :
            driver_ids.add(d.ensembl_protein_id)
    
    stored_interactions = {}

    progress("   Loading protein links ...")
    with open_file(StringDbProteinLinksFile) as f:
        f.readline()
        reader = csv.reader(f,delimiter=" ")
        for r in reader :
            score = float(r[2])
            if score >= 400 :
                gene1 = r[0].split('.')[1]
                gene2 = r[1].split('.')[1]
                if gene1 in driver_ids or gene2 in driver_ids :
                    # As each gene pair appears in protein.links as both geneA,geneB and as geneB,geneA, then sort the gene pair (so always geneA,geneB) and store the score once instead of twice to reduce memory needed, and then test just once below.
                    genes = (gene1, gene2) if gene1 < gene2 else (gene2, gene1)  # or: genes = tuple(sorted((gene1,gene2)))
                    if genes in stored_interactions and stored_interactions[genes] != score :
                        progress("Scores differ %d != %d for reversed occurance of gene_pair (%s %s)" %(stored_interactions[genes], score, gene1, gene2))
                    stored_interactions[genes] = score  # Would gene1+'_'+gene2 be faster as the key?
                    
    progress("   Num stored_interaction: %d.  Adding interactions to table ..." %(len(stored_interactions)) )
    # for d in Dependency.objects.select_related("driver", "target").all() :  # Use select_related() so that doesn't do a separate SQL query for each d to find the ensemble_protein_id's.
    for d in Dependency.objects.select_related("driver", "target").only("interaction","driver__ensembl_protein_id","target__ensembl_protein_id",).iterator() :  # Use select_related() so that doesn't do a separate SQL query for each d to find the ensemble_protein_id's.  Use only() as otherwise query data grows to ver 500Mb
        gene1 = d.driver.ensembl_protein_id
        gene2 = d.target.ensembl_protein_id
        if gene1 == gene2 :
            d.interaction = get_string_confidence(1000)
            d.save()
        else :
            genes = (gene1, gene2) if gene1 < gene2 else (gene2, gene1)  # or: genes = tuple(sorted((gene1,gene2)))
            if genes in stored_interactions :
                d.interaction = get_string_confidence(stored_interactions[genes])
                d.save()

    progress("   Counting interactions ...")
    progress("   %d Highest confidence interactions" %(Dependency.objects.filter(interaction = "Highest").count()) )
    progress("   %d High confidence interactions" %(Dependency.objects.filter(interaction = "High").count()) )
    progress("   %d Medium confidence interactions" %(Dependency.objects.filter(interaction = "Medium").count()) )
    return


def delete_unused_genes() :
    """ Remove the unused genes from Gene table. Then remove the empty space and optimize """
    Gene.objects.filter(is_driver=False, is_target=False).delete() # is_driver AND is_target are both False
    # Alternatively if not using is_driver and is_target columns:
    # select * FROM gendep_gene WHERE NOT EXISTS (SELECT * FROM gendep_dependency AS D WHERE D.target = gendep_gene.entrez_id OR D.driver = gendep_gene.entrez_id);



def optimize_database() :
    """ To recover unused space in database file and optimise access """

    if connection.vendor == 'sqlite' : # Alternatively use:  from django.conf import settings; if settings.DATABASES['default']['ENGINE'][-7:] == 'sqlite3':   # as ENGINE is "django.db.backends.sqlite3"
        connection.isolation_level = None  # To enable AUTOCOMMIT, as VACUUM needs to be outside a transaction.
        cursor = connection.cursor()
        cursor.execute("VACUUM") # Data modifying operation - commit required.  The autocommit mode is useful to execute commands requiring to be run outside a transaction, such as CREATE DATABASE or VACUUM.

    elif connection.vendor == 'mysql':
        connection.cursor().execute("OPTIMIZE TABLE gendep_study, gendep_gene, gendep_dependency;")
    
    elif connection.vendor == 'postgres':  # In Postgres (VACUUM cannot be executed inside a transaction block):
        connection.cursor().execute("VACUUM FULL")  # or to avoid rewriting the file: "VACUUM ANALYZE"
    else:
        progress("Unexpected database type: %s" %(connection.vendor))


def add_multihit_interactions2() :
    """" Avoid table joins is faster """
    cgds = defaultdict(set)
    for d in Dependency.objects.iterator() :
        cgd = ( d.driver_id, d.target_id, d.histotype )
        cgds[cgd].add( d.study_id )
    
    shortnames = {}
    for s in Study.objects.iterator() :
        shortnames[s.pmid] = s.short_name
    
    for d in Dependency.objects.iterator() :
        cgd = ( d.driver_id, d.target_id, d.histotype )
        
        if len(cgds[cgd]) > 1  :
            studies = cgds[cgd].difference( d.study_id )
            # d.multi_hit = ";".join(studies)            
            d.multi_hit = ";".join( sorted( [shortnames[pmid] for pmid in studies] ) )
            d.save()
    return

def add_multihit_interactions3() :
    """ Using SQL GROUP_CONCAT() is fastest, but in sqlite cannot order the study names within the concatinated group, whereas can order in MySQL """ 

    """" Avoid table joins is faster """
    shortnames = {}
    for s in Study.objects.iterator() :
        shortnames[s.pmid] = s.short_name
    
    # multi_hits = Dependency.objects.raw("""SELECT D.id,
    #    COUNT(DISTINCT D.pmid) AS num_studies,
    #    GROUP_CONCAT(DISTINCT D.pmid) AS studies
    #    FROM gendep_dependency D
	#	GROUP BY D.driver, D.target, D.histotype
	#	HAVING num_studies > 1
	#	ORDER BY D.id ASC;""")
    # To put the studies list in order by short_name, need to do a split, convert pmids to short_names, sort and join:
    # for m in multi_hits : 
    #    Dependency.objects.filter(id = m.id).update(multi_hit= ",".join( sorted( [shortnames[pmid] for pmid in m.studies.split(',')] ) ))

    # BUT: Testing for: Driver: 6502, Target: 1871, only id=191774 is annotated with the multi-hit column, but should also be added in id=128389
    # id: 128389  study: 28753430  multihit "" 
    # id: 191774  study: 28753431  multihit: "McDonald(2017),Tsherniak(2017)"
    
    # The 'D.id' isn't actually needed, as we are grouping by D.driver, D.target, D.histotype
    # BUT in Django we must include the primary key in the raw query, otherwise error: "InvalidQuery: Raw query must include the primary key"
    multi_hits = Dependency.objects.raw("""SELECT D.id,
        COUNT(DISTINCT D.pmid) AS num_studies,
        GROUP_CONCAT(DISTINCT D.pmid) AS studies
        FROM gendep_dependency D
		GROUP BY D.driver, D.target, D.histotype
		HAVING num_studies > 1""")
    # To put the studies list in order by short_name, need to do a split, convert pmids to short_names, sort and join:
    num_multi_hits=0
    for m in multi_hits :
        multi_hit_studies = ",".join( sorted( [shortnames[pmid] for pmid in m.studies.split(',')] ) )
        Dependency.objects.filter(driver = m.driver, target = m.target, histotype = m.histotype).update(multi_hit = multi_hit_studies)
        num_multi_hits += 1
    # An alternative way would be to also: GROUP_CONCAT(D.id) AS dids, then do the update using then dids.
    print("%d multi-hit dependencies were found and marked." %(num_multi_hits))



def test() :
    rawsql = """SELECT 
        E.gene_name AS driver_genename,
		D.driver AS driver_entrez,
		T.gene_name AS target_genename, 
		D.target AS target_entrez,
		D.interaction AS interaction, 
		D.histotype AS tissue, 
		E.ensembl_id AS driver_ensembl, 
        T.ensembl_id AS target_ensembl,
		T.ensembl_protein_id AS target_ensembl_protein,
		T.inhibitors AS inhibitors, 
		COUNT(DISTINCT D.pmid) AS num_studies,
        GROUP_CONCAT(DISTINCT S.short_name) AS studies
        FROM gendep_dependency D INNER JOIN gendep_study S ON (D.pmid = S.pmid)
	    INNER JOIN gendep_gene E ON (D.driver = E.entrez_id)
		INNER JOIN gendep_gene T ON (D.target = T.entrez_id)
		GROUP BY D.driver, D.target, D.histotype
		HAVING num_studies > 1
		ORDER BY D.driver, D.target, D.histotype ASC;"""

        
    # In SQLite, to put the studies in order, need to do a sub select ordered by study short_name:
    # Perhaps having an index on the short_name might make this sub query slightly faster?
    rawsql = """SELECT
        E.gene_name AS driver_genename,
		D.driver AS driver_entrez,
		T.gene_name AS target_genename, 
		D.target AS target_entrez,
		D.interaction AS interaction, 
		D.histotype AS tissue, 
		E.ensembl_id AS driver_ensembl, 
        T.ensembl_id AS target_ensembl,
		T.ensembl_protein_id AS target_ensembl_protein,
		T.inhibitors AS inhibitors, 
		COUNT(DISTINCT D.pmid) AS num_studies,
        GROUP_CONCAT(DISTINCT D.short_name) AS studies
        FROM (
            SELECT
	            D1.driver,
	            D1.target,
	            D1.interaction,
                D1.histotype,
                D1.pmid,
	            S.short_name
            FROM gendep_dependency D1 INNER JOIN gendep_study S ON (D1.pmid = S.pmid)
            ORDER BY S.short_name
            ) D
        INNER JOIN gendep_gene E ON (D.driver = E.entrez_id)
	    INNER JOIN gendep_gene T ON (D.target = T.entrez_id)
	    GROUP BY D.driver, D.target, D.histotype
	    HAVING num_studies > 1
	    ORDER BY D.driver, D.target, D.histotype ASC;"""
    
    # Can't do join with an update in sqlite, so culd try CLE instead, but need to se the last where clause the following is incorrect as updates multi_hit in all rows with the same value:
    """ WITH B(driver,target,histotype,num_studies,studies) AS (SELECT 
		D.driver,
		D.target,
		D.histotype,
		COUNT(DISTINCT D.pmid) AS num_studies,
        GROUP_CONCAT(DISTINCT S.short_name) AS studies
        FROM gendep_dependency D INNER JOIN gendep_study S ON (D.pmid = S.pmid)
		GROUP BY D.driver, D.target, D.histotype
		HAVING num_studies > 1)
UPDATE gendep_dependency
  SET multi_hit = (select studies from B where driver=gendep_dependency.driver AND target=gendep_dependency.target AND histotype=gendep_dependency.histotype)
  WHERE driver=1029 and target=11338 and histotype='HAEMATOPOIETIC_AND_LYMPHOID_TISSUE';"""
  
    


    

def add_multihit_interactions1() :
    """ Using select_related() to avoid a separate SQL query being run for each dependency row """
    cgds = defaultdict(set)
    for d in Dependency.objects.select_related("driver__entrez_id", "target__entrez_id", "study__short_name").all() :
        driver = d.driver.entrez_id
        target = d.target.entrez_id
        tissue = d.histotype
        study = d.study.short_name                
        cgd = (driver, target, tissue)
        cgds[cgd].add(study)
    
    for d in Dependency.objects.select_related("driver__entrez_id", "target__entrez_id", "study__short_name").all() :
        driver = d.driver.entrez_id
        target = d.target.entrez_id
        tissue = d.histotype
        study = d.study.short_name
        
        if len(cgds[(driver, target, tissue)]) > 1  :
            studies = cgds[(driver, target, tissue)].difference(study)
            d.multi_hit = ";".join(studies)
            d.save()
    return
    
if __name__ == "__main__" :

    with transaction.atomic():
        
        progress("Emptying database tables")
        for table in (Dependency, Study, Gene):
            table.objects.all().delete()
        progress("Adding Studies to Database")
        add_studies()
        
        # Add details to gene table
        progress("Adding Genes")
        mapped_genes = add_gene_details()
        add_driver_details()

        # Add dependencies
        progress("Adding Dependencies:")
        add_dependencies()

        progress("Deleting unused genes")
        delete_unused_genes()

        progress("Adding Ensembl protein IDs to Gene table")
        add_ensembl_proteinids()
        progress("Adding Inhibitor drugs to Gene table")
        add_inhibitor_details()
        progress("Adding Entrez summaries to Gene table")
        add_entrez_summaries()
        
        progress("Adding String-DB Interactions to Dependency table")
        add_string_interactions()
        
        progress("Adding multi-hit interactions to Dependency table")
        add_multihit_interactions3()

        
    progress("Optmizing database")
    optimize_database() # Is outside the transaction.atomic()
        
    progress("Finished.")
