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
# from django.conf import settings

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
    print("\n"+message)
    

def add_gene_details() :
    """
    Populates the Gene table of the database. Adds names / symbols
    and a variety of IDs for different DBs (Ensembl / Uniprot / HGNC).
    Data is sourced from the HGNC complete set.
    """
    entrez_to_symbol = {}
    # The hgnc_complete_set.txt file contains unicode characters in the 'name' column, eg. the Greek symbols for Alpha and Beta, etc, so need to open it with utf-8 encoding:
    with open_file("./input_data/hgnc_complete_set.txt") as f :
        reader = csv.DictReader(f,delimiter="\t")
        for row in reader :
            if row['entrez_id'] and row['symbol']:
                synonyms = [] if row['alias_symbol']=='' else row['alias_symbol'].split("|")
                prev_names = [] if row['prev_symbol']=='' else row['prev_symbol'].split("|") # Need to check for empty prev_names, otherwise get [ '' ] then synonym_string becomes, eg: " | RHEB2 " or "PI3K | "
                synonym_string = " | ".join(list(set(synonyms).union(prev_names)))
                try:
                    g = Gene.objects.create(
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
                         )
                except Warning as warning:  # To report the row causing any data truncation error.
                    progress("\nERROR:")
                    for key,val in row.items():
                        progress(key + ":" + val)
                    progress("\n")
                    raise warning
                    
                entrez_to_symbol[row['entrez_id']] = row['symbol']
    return entrez_to_symbol

def add_driver_details() :
    """
    Adds details of the alteration types considered for each driver
    """
    with open("./input_data/AlterationDetails.csv","r") as f :
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
    with open("./input_data/entrez_gene_id.vs.string.v10.28042015.tsv","r") as f:
        f.readline()
        reader = csv.reader(f,delimiter="\t")
        for r in reader :
            entrez = r[0]
            ensembl_pid = r[1].split('.')[1]
            entrez_to_ensemblpid[entrez] = ensembl_pid
    with open_file("./input_data/9606.protein.aliases.v10.txt") as f:
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
    with open("./input_data/dgi_drug_targets.txt","r") as f :
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
    with open("./input_data/entrez_summaries.txt","r") as f :
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
    with open("input_data/ScreenDescriptions.txt","rU") as f :
        reader = csv.DictReader(f,delimiter="\t")
        for row in reader :
            Study.objects.create(pmid=row["PMID"], code = row['Code'], short_name = row['ShortName'], title = row["Title"], 
                authors = row["Authors"], abstract = row["Abstract"], summary = row["Summary"], experiment_type = row["Type"], 
                journal = row["Journal"], pub_date = row["Date"], num_targets = row["Targets"])
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
                if not target.is_target :
                    target.is_target=True
                    target.save()
                if duplicates and Dependency.objects.filter(driver=driver, target=target, histotype=tissue, study=study).exists() :
                    existing_cgd = Dependency.objects.get(driver=driver, target=target, histotype=tissue, study=study)
                    if existing_cgd.wilcox_p > wilcox_p :
                        existing_cgd.za = za
                        existing_cgd.zb = zb
                        existing_cgd.wilcox_p = wilcox_p
                        existing_cgd.zdiff = zdiff
                        existing_cgd.effect_size = cles
                        existing_cgd.boxplot_data = row["boxplot_data"]
                        existing_cgd.save()
                else :
                    # No longer using "bulk_update" as with MySQL, can get error: django.db.utils.OperationalError: (2006, 'MySQL server has gone away') because try to add too many at once. Could add in batches of 500 but adds extra complexity.
                    dependency = Dependency.objects.create(driver = driver, target = target, wilcox_p = wilcox_p, za = za, zb = zb, zdiff = zdiff,
                        effect_size=cles, histotype = tissue, study = study, boxplot_data = row["boxplot_data"])
                        
            except ObjectDoesNotExist :
                print("Skipping row",row['marker'],row['target'])

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
    with open("input_data/ScreenDescriptions.txt","rU") as f :
        reader = csv.DictReader(f,delimiter="\t")
        for row in reader :
            pmid = row["PMID"]
            screens = row["CGD_files"].split(';')
            duplicates = row["DuplicateGenes"] == "1"
            exclude_tissues = row['ExcludeTissues'].strip()
            exclude_tissues = [] if exclude_tissues == '' else exclude_tissues.split(';')
            for s in screens :
                progress("Adding dependencies from %s, Duplicates: %s, ExcludeTissues: %s" %(s,duplicates,exclude_tissues) )
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
    with open_file("./input_data/9606.protein.links.v10.txt") as f:
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
    for d in Dependency.objects.select_related("driver__ensembl_protein_id", "target__ensembl_protein_id").all() :  # Use select_related() so that doesn't do a separate SQL query for each d to find the ensemble_id.
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


def add_multihit_interactions() :
    """
    Test counts:
    Cowley multi 1146
    Wang 178 
    Marcotte 970
    Campbell 144
    """
    cgds = defaultdict(set)
    for d in Dependency.objects.all() :
        cgd = ( d.driver_id, d.target_id, d.histotype )
        cgds[cgd].add( d.study_id )
    
    shortnames = {}
    for s in Study.objects.all() :
        shortnames[s.pmid] = s.short_name
    
    for d in Dependency.objects.all() :
        cgd = ( d.driver_id, d.target_id, d.histotype )
        
        if len(cgds[cgd]) > 1  :
            studies = cgds[cgd].difference( d.study_id )
            # d.multi_hit = ";".join(studies)            
            d.multi_hit = ";".join( sorted( [shortnames[pmid] for pmid in studies] ) )
            d.save()
    return


def add_multihit_interactions1() :
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
        progress("Adding Dependencies")
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
        add_multihit_interactions()

        
    progress("Optmizing database")
    optimize_database() # Is outside the transaction.atomic()
        
    progress("Finished.")
