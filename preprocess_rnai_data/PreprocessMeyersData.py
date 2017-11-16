'''
This script gets the Meyers 2017 scores (Meyers et al) into a format usable by the R scripts.
   Paper: https://www.nature.com/ng/journal/vaop/ncurrent/full/ng.3984.html
   Data:  https://ndownloader.figshare.com/files/9197923
This uses the HGNC download to map the Gene names (symbols) to Entrez_ids.
'''

# After running this script, can run the R analysis, using:
#   setwd("/Users/sbridgett/Documents/DjangoApps/cancergd/R_scripts/")
#   source("run_intercell_analysis.R")

import pandas as pd
import sys, csv
from collections import defaultdict


# Read HGNC data to map Gene names (symbols) to Entrez_ids:
# The following were found manually by going to: https://www.ncbi.nlm.nih.gov/gene/?term=(HDGFRP3%5BGene+Name%5D)+AND+human%5BOrganism%5D
# And using Gene search expression: (HDGFRP3[Gene Name]) AND human[Organism]
common_to_entrez_hgnc = {  # Added some not currently in the hgnc downloaded file (as updated on entrez on Sept 2017):
  'HDGFRP2': '84717',
}
"""
  'HDGFL2' : '84717',
  'HDGFL3' : '50810',
  'SF3B6'  : '51639',
  'SBK3'   : '100130827',
  'POMK'   : '84197',
  'PRAG1'  : '157285',
  'SF3B6'  : '51639',
  'SBK3'   : '100130827',
  'HDGFRP2': '84717', --
  'SGK494' : '124923',  
"""

prevsymbol_to_common_hgnc = {}
aliassymbol_to_common_hgnc = {}

with open("../input_data/hgnc_complete_set.txt", "rU") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for line in reader:
        common_to_entrez_hgnc[line['symbol']] = line['entrez_id']

        if line['prev_symbol'] != "":
          for prev in line['prev_symbol'].split('|'):  # as can be several, eg: "NCRNA00181|A1BGAS|A1BG-AS" (Note the quotes, and pipe-delimiter)
            if prev[0] == '"': print("**** prev_symbol has quote at start still ******", prev)
            if prev in prevsymbol_to_common_hgnc:
                #print("WARNING: prev_symbol %s = %s is already used for %s" %(prev,line['symbol'],prevsymbol_to_common_hgnc[prev]))
                prevsymbol_to_common_hgnc[prev] += '|'+line['symbol']
            else: 
                prevsymbol_to_common_hgnc[prev] = line['symbol']

        if line['alias_symbol'] != "":
          for alias in line['alias_symbol'].split('|'):  # as can be several, eg: "NCRNA00181|A1BGAS|A1BG-AS" (Note the quotes, and pipe-delimiter)
            if alias[0] == '"': print("**** alias_symbol has quote at start still ******", alias)
            if alias in aliassymbol_to_common_hgnc:
                #print("WARNING: alias_symbol %s = %s is already used for %s" %(alias,line['symbol'],aliassymbol_to_common_hgnc[alias]))
                aliassymbol_to_common_hgnc[alias] += '|'+line['symbol']
            else: 
                aliassymbol_to_common_hgnc[alias] = line['symbol']


alias_to_hgnc = {
'HDGFRP3'  : 'HDGFL3',
'SGK223'   : 'PRAG1',
}
"""
# For mm7.xlsx:
'C11orf30' : 'EMSY',    #  56946
'C17orf70' : 'FAAP100', #  80233 
'C17orf89' : 'NDUFAF8', # 284184
'MLLT4'    : 'AFDN',    #   4301
'GC11orf35': 'C11orf35', # (ie. no "G" at the start). 'C11orf35' is 'LMNTD2'

'HDGFRP3'  : 'HDGFL3',  --
'SGK196'   : 'POMK',
'SGK223'   : 'PRAG1', --
'SF3B14'   : 'SF3B6',
'SGK110'   : 'SBK3',
"""
# 'STRA13' : 'MHF2',  # Probably.




cellines_in_cancergd = []
with open("../preprocess_genotype_data/genotype_output/GDSC1000_cnv_exome_all_muts_v1.txt", "rU") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for line in reader:
        cellines_in_cancergd.append(line['Gene'])  # The cellines are listed below 'Gene' header.
print("cellines_in_cancergd: %d" %(len(cellines_in_cancergd)))

cellline_to_cancergd = {
'EOL-1'    : 'EOL1CELL',
'Molm-13'  : 'MOLM13',
'MV4-11'   : 'MV411',
'MV4;11'   : 'MV411',  # As appears in the exported mcc3.csv file as ';' instead of '-'
'OCI-AML2' : 'OCIAML2',
'OCI-AML3' : 'OCIAML3',
'OCI-AML5' : 'OCIAML5',
'P31/FUJ'  : 'P31FUJ',
'PL-21'    : 'PL21',
'SKM-1'    : 'SKM1',
'THP-1'    : 'THP1',
'JJN-3'    : 'JJN3',
'KE-37'    : 'KE37',
'KM-H2'    : 'KMH2', #*** THYROID in CancerGD BUT is Lymphoma: https://www.dsmz.de/catalogues/details/culture/ACC-8.html and https://cansar.icr.ac.uk/cansar/cell-lines/KM-H2/
'KY-821'   : 'KY821',
'L-363'    : 'L363',
'L-428'    : 'L428',
'ML-1'     : 'ML1',  # ML1_THYROID  which is correct: follicular thyroid carcinoma: https://www.dsmz.de/catalogues/details/culture/ACC-464.html?tx_dsmzresources_pi5%5BreturnPid%5D=192
'ML-2'     : 'ML2',  # correctly: ML2_HAEMATOPOIETIC_AND_LYMPHOID_TISSUE: acute myelomonocytic leukemia: https://www.dsmz.de/catalogues/details/culture/ACC-15.html?tx_dsmzresources_pi5%5BreturnPid%5D=192
'Molt-16'  : 'MOLT16',
'NALM-6'   : 'NALM6',
'Nomo-1'   : 'NOMO1',
'RCH-ACV'  : 'RCHACV',
'SKM-1'    : 'SKM1',
'SU-DHL-4' : 'SUDHL4',
'SUP-T1'   : 'SUPT1',
'TALL-1'   : 'TALL1',

# Just capitalise:
'P31Fuj'   : 'P31FUJ',
'Jurkat'   : 'JURKAT',
'Reh'      : 'REH',

# The following cell-lines not in CancerGD's: ../preprocess_genotype_data/genotype_output/GDSC1000_cnv_exome_all_muts_v1.txt:
# But will reformat the name anyway:
# In file "mmc7.xlsx":
'HPB-ALL'  : 'HPBALL',
'KE-97'    : 'KE-97',
'KMS-26'   : 'KMS26',
'KMS-28BM' : 'KMS28BM',
'Mino'     : 'MINO',
'MonoMac1' : 'MONOMAC1',
#'SEM'      : 'SEM',  # <-- Only this is in the DRIVE_RSA data.
'SHI-1'    : 'SHI1',
#'U937'     : 'U937',
# In file "mm3.xlsx":
'TF-1'     : 'TF1',
}




inputScoresFile = "./rnai_input/avana_ceres_gene_effects.csv"
cellline_mapping_files = [ "./rnai_input/Hahn2017_name_mapping_cancergd.txt", "./rnai_input/MeyersToCancerGD.txt" ]  # Is same mappings as Hahn.
rnai_output_file= "./rnai_output/Meyers_cancergd.txt"
tissue_output_file='./rnai_output/Meyers_cancergd_tissues.txt'

scores = pd.read_csv(inputScoresFile, sep=",", quotechar='"', index_col=0)  # No need to skip any rows

name_dict = {}
# Note: Hahn2017_name_mapping_cancergd.txt includes: 'achilles_to_cancergd.txt' at end.
#   ie: cat  DepMap_name_mapping_cancergd.txt  NewLineChar.txt   achilles_to_cancergd.txt  >  Hahn2017_name_mapping_cancergd.txt

for mapping_file in cellline_mapping_files:
    with open(mapping_file, "rU") as f:  # <-- May need to add to this cell line list.
        line = f.readline().strip()     # Ignore the first line which is: "DepMap Name	CancerGD Name"
        if line != "DepMap Name\tCancerGD Name":
            print("Expected header line at start of '%s'" %(mapping_file))
            sys.exit(1)
        print("Cell-line mappings to CancerGD:")
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) <2 or parts[1]=='':  # To skip the lines that don't have the second column
                continue
            if len(parts)>2:
                print("More than two columns: '%s'" %(line))
                sys.exit(2)
            if parts[0] in name_dict:
                print("Cell-line name '%s' already in name_dict" %(parts[0]))
            name_dict[parts[0]] = parts[1]
            print("'%s' => '%s'" %(parts[0], parts[1]))

# NOTE: That 786O_KIDNEY 7860_KIDNEY are different as the first incorrectly has an "O" instead of a zero.

#scores.dropna(thresh=2)  # To keep only rows with at least two no NA values.
#scores.dropna(how='any')  # To remove any rows that have one or more NA values.  - but doesn't actually remove the 'NA' rows 

scores.rename(columns=name_dict, inplace=True)
scores = scores.T

# scores.drop('Description', inplace=True)   # Description column is same as Name column.

# Manually remapped ENTREZ IDs (from Stephen)
entrez_ids_renamed = {}
"""
    '244': '728113',   # confirmed on entrez ANXA8L2 -> ANXA8L1
    '9503': '653067',   # confirmed on entrez XAGE1D -> XAGE1E
    # confirmed on entrez LOC90462 is withdrawn as redundant in assembly
    # (renaming 100289635 as ZNF605).
    '90462': '100289635',
    '164022': '653505',   # confirmed on entrez PPIAL4A -> PPIAL4A
    '399753': '414224',   # confirmed on entrez LOC399753 -> AGAP12P
    '554045': '100288711',  # confirmed on entrez DUX4L9 -> DUX4L9
    '653048': '653067',   # confirmed on entrez XAGE1C -> XAGE1E
    '653219': '653220',   # confirmed on entrez XAGE1A -> XAGE1B
    '653501': '401509',   # confirmed on entrez LOC653501 -> ZNF658B
    '727787': '3812',     # confirmed on entrez LOC727787 -> KIR3DL2
    '728127': '653234',   # confirmed on entrez AGAP10 -> AGAP10P
    '100036519': '349334',   # confirmed on entrez FOXD4L2 -> FOXD4L4
    '100131392': '729384',   # confirmed on entrez LOC100131392 -> TRIM49D2
    '100131530': '5435',     # confirmed on entrez LOC100131530 -> POLR2F
    # confirmed on entrez KIR3DL3 -> KIR3DL3 (ie. same symbol)
    '100133046': '115653',
    '100170939': '11039',    # confirmed on entrez LOC100170939 -> SMA4
    '100287534': '3805',     # confirmed on entrez LOC100287534 -> KIR2DL4
    #  '100288687': '22947',    # *not* same on entrez nor on NGNC. DUX4 (HGNC:50800; also known as DUX4L) different record from DUX4L1 (HGNC:3082; also known previously as DUX4; DUX10)
    '100505503': '6218',     # confirmed on entrez RPS17L -> RPS17
    '100505793': '10772',    # confirmed on entrez LOC100505793 -> SRSF10
    '100506499': '196913',   # confirmed on entrez LOC100506499 -> LINC01599
    '100506859': '341676',   # confirmed on entrez LOC100506859 ->
    '100507018': '101927612',  # confirmed on entrez RNF139-AS1 -> RNF139-AS1
    '100507699': '728806',   # confirmed on entrez LOC100507699 -> NSFP1
    '100509575': '280657',   # confirmed on entrez LOC100509575 -> SSX6
    '100509582': '3126',     # confirmed on entrez LOC100509582 -> HLA-DRB4
    '100653070': '11026',    # confirmed on entrez LOC100653070 -> LILRA3
    '100653112': '266722'    # confirmed on entrez LOC100653112 -> HS6ST3
"""



"""
# "shrna_mapping_20150312.tsv" format is:
# Barcode Sequence        Gene Symbol     Gene ID Transcript
# AAAAATGGCATCAACCACCAT   RPS6KA1 6195    NM_001006665.1
# AAAAATGGCATCAACCACCAT   RPS6KA1 6195    NM_002953.3
# AAAAATGGCATCAACCACCAT   RPS6KA1 6195    XM_005245966.2
# AAAAATGGCATCAACCACCAT   RPS6KA1 6195    XM_005245967.2

symbol_to_id_map = {}  # MAPS Gene symbols to Entrez_ids
num_no_current = 0
with open("./rnai_input/shrna_mapping_20150312.tsv", "rU") as f:   # WAS: CP0004_20131120_19mer_trans_v1.chip", "rU") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for r in reader:
        gene_symbol = r['Gene Symbol']
        if gene_symbol[0:11] == "NO_CURRENT_":
            num_no_current += 1
            continue
        entrez_id = entrez_ids_renamed.get( r['Gene ID'].strip(), r['Gene ID'].strip() )
        
        if gene_symbol in symbol_to_id_map:
            if symbol_to_id_map[gene_symbol] != entrez_id:
                print("Different entrez_ids for:", gene_symbol, entrez_id, symbol_to_id_map[gene_symbol])
        else:
            symbol_to_id_map[gene_symbol] = entrez_id

print("In input file 'shrna_mapping_20150312.tsv', ignoring %d rows with gene_symbol starting with 'NO_CURRENT_'" % (num_no_current))
"""

"""
ATARIS_map = {}

# Achilles_QC_v2.4.3.rnai.shRNA.table.txt was:
# shRNA   gene.symbol     isUsed  sol.number      sol.name        sol.id  cscore  pval    qval
# CAGTGACAGAAGCAGCCATAT_A1BG      A1BG    FALSE   NA      NA      NA      0.453   0.352   0.715
# CCGCCTGTGCTGATGCACCAT_A1BG      A1BG    FALSE   NA      NA      NA      0.191   0.644   0.87

with open("./rnai_input/Achilles_QC_v2.4.3.rnai.shRNA.table.txt", "rU") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for r in reader:
        if r['isUsed'] == 'TRUE':
            ATARIS_map[r['sol.name']] = shRNA_map[r['shRNA']]
"""
name_dict = {}
cols_to_drop = []
for x in scores.columns.values:
    # name, solution_id, ataris_string = x.split('_')  # As format was: "A2ML1_1_01110",  but is now just: RPS6KA1
    if x in common_to_entrez_hgnc:
        name_dict[x] = x + '_' + common_to_entrez_hgnc[x]
    elif x in prevsymbol_to_common_hgnc:
        name_dict[x] = x + '_' + prevsymbol_to_common_hgnc[x]
    elif x in aliassymbol_to_common_hgnc:
        name_dict[x] = x + '_' + aliassymbol_to_common_hgnc[x]
    elif x in alias_to_hgnc:
        y = alias_to_hgnc[x]
        name_dict[x] = y + '_' + common_to_entrez_hgnc[y]
    else:
        print("**ERROR: Entrez_id not found in common_to_entrez_hgnc for gene_symbol='%s'" %(x))
        cols_to_drop.append(x)
        # sys.exit(1)

#for x in cols_to_drop:
#    scores.drop(x, axis=1, inplace=True)   # Remove that column.
scores.drop(cols_to_drop, axis=1, inplace=True)   # Remove that column.

scores.index.names = ['cell.line']

scores.rename(columns=name_dict, inplace=True)

scores.to_csv(rnai_output_file, sep="\t")


# Create Tissue Map
cell_lines = scores.index.values

numMissingCelllines = 0 
tissue_types = defaultdict(set)
for c in cell_lines:
    if c not in cellines_in_cancergd:
        print("Cellline not found in cancergd celllines: '%s' " %(c))
        numMissingCelllines += 1
        cellname = c.split('_', 1)[0]
        if cellname in cellline_to_cancergd:
            print("BUT could use cancergd cellline '%s' for Meyers cellline '%s'" %(cellline_to_cancergd[cellname],c))
            # cellline = cellline_to_cancergd[cellname]+'_'+tissue
    tissue_types[c.split('_', 1)[1]].add(c)
print("Number of missing cell-lines: %d" %(numMissingCelllines))
    
ordered_tissues = sorted(tissue_types.keys())
with open(tissue_output_file, 'w') as f:
    f.write("cell.line\t")
    f.write("\t".join(ordered_tissues))
    f.write("\n")
    for c in cell_lines:
        f.write("%s\t" % c)
        f.write("\t".join([str(int(c in tissue_types[x]))
                           for x in ordered_tissues]))
        f.write("\n")
