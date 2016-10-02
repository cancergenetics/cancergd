""" Script to import the CGD data into the database tables """
import sys, os, csv, re
import gzip  # To directly the compressed string db files without needing to uncompress them first.
import django
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
import warnings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cgdd.settings")
django.setup()
from gendep.models import Study, Gene, Dependency 

"""In the SQLite database (used for development locally), the max_length parameter for fields
is ignored as the "numeric arguments in parentheses that following the type name (ex: "VARCHAR(255)")
are ignored by SQLite - SQLite does not impose any length restrictions (other than the large global
SQLITE_MAX_LENGTH limit) on the length of strings, ...." (unless use sqlites CHECK contraint option)
BUT MySQL does enforce max_length, so MySQL will truncate strings that are too long, (including keys
so loss of unique primary key) so need to check for data truncation, as it jsut gives a warning NOT an exception.
To convert the MySQL data truncation (due to field max_length being too small) into raising an exception
we use :"""

warnings.filterwarnings('error', 'Data truncated .*')

def add_gene_details() :
    """
    Populates the Gene table of the database. Adds names / symbols
    and a variety of IDs for different DBs (Ensembl / Uniprot / HGNC).
    Data is sourced from the HGNC complete set.
    """
    entrez_to_symbol = {}
    # The hgnc_complete_set.txt file contains unicode characters in the 'name' column, eg. the Greek symbols for Alpha and Beta, etc, so need to open it with utf-8 encoding:
    with open("./input_data/hgnc_complete_set.txt","rU", encoding='utf-8') as f :
        reader = csv.DictReader(f,delimiter="\t")
        for row in reader :
            if row['entrez_id'] and row['symbol']:
                synonyms = synonyms=='' ? [] : row['alias_symbol'].split("|")
                prev_names = prev_names=='' ? [] : row['prev_symbol'].split("|") # Need to check for empty prev_names, otherwise get [ '' ] then synonym_string becomes, eg: " | RHEB2 " or "PI3K | "
                synonym_string = " | ".join(list(set(synonyms).union(prev_names)))
                g = Gene.objects.create(
                         gene_name = row['symbol'], # eg. ERBB2
                         full_name  = row['name'], # eg. erb-b2 receptor tyrosine kinase 2
                         prevname_synonyms = synonym_string, # eg: NGL  (plus)  NEU|HER-2|CD340|HER2
                         entrez_id  = row['entrez_id'], # eg: 2064
                         ensembl_id = row['ensembl_gene_id'], # eg: ENSG00000141736
                         vega_id = row['vega_id'], # eg: OTTHUMG00000179300
                         hgnc_id = row['hgnc_id'].split(':')[1],
                         omim_id = row['omim_id'],
                         cosmic_id = row['cosmic'],
                         uniprot_id = row['uniprot_ids'].split('|')[0]
                         )
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
                print("ERROR updating driver", row)
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
    
def add_dependency_file(study, filename, duplicates=False) :
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
        print("ERROR, STUDY ",study," does not exist")
        return
    dependencies = {}
    with open("./R_scripts/outputs/%s" % filename,"rU") as f :
        reader = csv.DictReader(f,delimiter="\t")
        for row in reader :
            marker_entrez = row['marker'].split('_')[1]
            target_entrez = row['target'].split('_')[1]
            wilcox_p = float(row['wilcox.p'])
            cles = float(row["CLES"])
            zdiff = float(row["ZDiff"])
            za = float(row["zA"])
            zb = float(row["zB"])
            tissue = row.get("tissue", "PANCAN") # As PANCAN data has no "tissue" column, so set to "PANCAN"
            try :
                driver = Gene.objects.get(entrez_id = marker_entrez)
                target = Gene.objects.get(entrez_id = target_entrez)
                key = "%s_%s_%s" % (marker_entrez,target_entrez, tissue)
                if duplicates and (key in dependencies) :
                    existing_cgd = dependencies[key]
                    if existing_cgd.wilcox_p > wilcox_p :
                        existing_cgd.za = za
                        existing_cgd.zb = zb
                        existing_cgd.wilcox_p = wilcox_p
                        existing_cgd.zdiff = zdiff
                        existing_cgd.effect_size = cles
                        existing_cgd.boxplot_data = row["boxplot_data"]
                else :
                    # driver_name = driver, target_name = target,
                    dependencies[key] = Dependency(driver = driver, target = target, wilcox_p = wilcox_p, effect_size=cles, za = za,
                        zb = zb, zdiff = zdiff, histotype = tissue, study = study, boxplot_data = row["boxplot_data"])
            except ObjectDoesNotExist :
                print("Skipping row",row['marker'],row['target'])
        Dependency.objects.bulk_create(dependencies.values()) # Much quicker than individual creation of objects     
    return

def add_dependencies() :
    """
    Reads the screens file which contains a list of screens and 
    associated dependency files. Then calls add_dependency_file
    to add each file to the database
    """
    with open("input_data/ScreenDescriptions.txt","rU") as f :
        reader = csv.DictReader(f,delimiter="\t")
        for row in reader :
            pmid = row["PMID"]
            screens = row["CGD_files"].split(';')
            duplicates = row["DuplicateGenes"] == "1"
            for s in screens :
                print("Adding dependencies",s,duplicates)
                add_dependency_file(pmid,s,duplicates)
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
    
    with open_file("./input_data/9606.protein.links.v10.txt") as f:
        f.readline()
        reader = csv.reader(f,delimiter=" ")
        for r in reader :
            score = float(r[2])
            if score >= 400 :
                gene1 = r[0].split('.')[1]
                gene2 = r[1].split('.')[1]
                if gene1 in driver_ids or gene2 in driver_ids :
                    stored_interactions[(gene1, gene2)] = score  # Would gene1+'_'+gene2 be faster as the key?
    
    for d in Dependency.objects.all() :
        driver_id = d.driver.ensembl_protein_id
        target_id = d.target.ensembl_protein_id
        if (driver_id, target_id) in stored_interactions :
            d.interaction = get_string_confidence(stored_interactions[(driver_id, target_id)])
            d.save()
        if (target_id, driver_id) in stored_interactions :   # Ask Colm, would elif be quicker here ?
            d.interaction = get_string_confidence(stored_interactions[(target_id, driver_id)])
            d.save()
        if target_id == driver_id :
            d.interaction = get_string_confidence(1000) 
            d.save()
    print(Dependency.objects.filter(interaction = "Highest").count(), "Highest confidence interactions")
    print(Dependency.objects.filter(interaction = "High").count(), "High confidence interactions")
    print(Dependency.objects.filter(interaction = "Medium").count(), "Medium confidence interactions")
    return
    
if __name__ == "__main__":
    with transaction.atomic(): 
        print("\nEmptying database tables")
        for table in (Dependency, Study, Gene): 
            table.objects.all().delete()
        add_studies()
        
        # Add details to gene table
        mapped_genes = add_gene_details()
        add_driver_details()
        add_ensembl_proteinids()
        add_inhibitor_details()
        add_entrez_summaries()
        
        # Add dependencies
        add_dependencies()        
        add_string_interactions()