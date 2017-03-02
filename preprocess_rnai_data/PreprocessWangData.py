'''
This processes the data from Wang (2017): http://www.cell.com/cell/abstract/S0092-8674(17)30061-2
which is CRISPR-based screens identify essential genes in 14 human AML cell lines

Cell line names are changed to CCLE format, Entrez IDs are appended to Gene Names,
and a tissue_map file created describing the tissue type of each cell line name


Creates a mapping from Campbell style IDs (Symbol_ENSGXXX) to that used by CancerGD
(Symbol_ENTREZ). Also updates gene names to current symbols from HGNC
'''

import csv

common_to_entrez_hgnc = {}
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
# For mm7.xlsx:
'C11orf30' : 'EMSY',    #  56946
'C17orf70' : 'FAAP100', #  80233 
'C17orf89' : 'NDUFAF8', # 284184
'MLLT4'    : 'AFDN',    #   4301
'GC11orf35': 'C11orf35', # (ie. no "G" at the start). 'C11orf35' is 'LMNTD2'
}
# 'STRA13' : 'MHF2',  # Probably.


"""
# Aliases still needing found for mm3.xlsx:

Missing entrez_id for  AQPEP
Missing entrez_id for  GC11orf35
Missing entrez_id for  CONTROL
Missing entrez_id for  HDGFRP2
Missing entrez_id for  HDGFRP3
Missing entrez_id for  HMP19
Missing entrez_id for  KIAA1804
Missing entrez_id for  LOC100127983
Missing entrez_id for  LOC100130480
Missing entrez_id for  LOC100133267
Missing entrez_id for  LOC100287177
Missing entrez_id for  LOC100505679
Missing entrez_id for  LOC100507003
Missing entrez_id for  LOC100653515
Missing entrez_id for  LOC100996485
Missing entrez_id for  LOC147646
Missing entrez_id for  LOC643669
Missing entrez_id for  LOC81691
Missing entrez_id for  LPPR1
Missing entrez_id for  LPPR2
Missing entrez_id for  LPPR3
Missing entrez_id for  LPPR4
Missing entrez_id for  LPPR5
Missing entrez_id for  MST4
Missing entrez_id for  NARR
Missing entrez_id for  NIM1
Missing entrez_id for  NSG1
Missing entrez_id for  PAPL
Missing entrez_id for  PCDP1
Missing entrez_id for  SELK
Missing entrez_id for  SELM
Missing entrez_id for  SELO
Missing entrez_id for  SELT
Missing entrez_id for  SELV
Missing entrez_id for  SEP15
Missing entrez_id for  SF3B14
Missing entrez_id for  SGK223
Missing entrez_id for  SGK494
Missing entrez_id for  TARP
Missing entrez_id for  THEG5
Missing entrez_id for  WTH3DI
Missing entrez_id for  ZAK
Missing entrez_id for  ZHX1-C8ORF76

Count of the above missing EntrezIds: 43


Count of 'prev_symbol's used to obtain current gene symbol: 497
The following three 'prev_symbol's are ambigious:
  Prev_symbol B3GNT1 can be either: B3GNT2|B4GAT1
  Prev_symbol C11orf48 can be either: C11orf98|LBHD1
  Prev_symbol STRA13 can be either: BHLHE40|CENPX





"""

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
'SEM'      : 'SEM',
'SHI-1'    : 'SHI1',
'U937'     : 'U937',
# In file "mm3.xlsx":
'TF-1'     : 'TF1',
}

"""
# Cellines not in CancerGD's: ../preprocess_genotype_data/genotype_output/GDSC1000_cnv_exome_all_muts_v1.txt:
HPB-ALL
KE-97,
KMS-26,
KMS-28BM,
Mino,      (MINO)
MonoMac1,  (MONOMAC1)
SEM,
SHI-1,
U937,
"""


tissue_dict = {
"KE97"    : "STOMACH",
"ML1"     : "THYROID",
"default" : "HAEMATOPOIETIC_AND_LYMPHOID_TISSUE",    # as rest are "HAEMATOPOIETIC_AND_LYMPHOID_TISSUE"
}

tissue_list = sorted(list(set(tissue_dict.values())))

m = [["cell.line",],] # 2D array to store data to transpose later.
n = ["cell.line",] # 1D array of position of the tissue in tissue_list

delim="," # or "\t"

# "mmc7.xlsx" file from that Wang et al Cell paper, which is table:
#   "Table 8. CRISPR Scores from focused library screens - 42 hematopoietic cancer cell lines"
#   (I ignored the "Isogenic cell lines" columns at the right of that table)
# inputScoresFile  = "./rnai_input/Wang_mmc7_without_table_description.csv"
# outputFilePrefix = "./rnai_output/Wang_mmc7_cancergd"
# NumIsoCols = 5 # To Ignore these "Isogenic cell line" columns at right of table "mm7.xlsx" (which are: SKM1-MEK1DD, SKM1-MEK1WT, SKM1-RAC1G12V, SKM1-RAC1WT, THP1-TIAM1)


# "mmc3.xlsx" file from that Wang et al Cell paper, which is table:
#   "Table 3. CRISPR Scores from AML cell lines"
#   (I manually changed cell-lines: "NB4 (replicate 1)" and "NB4 (replicate 2)" to just be: "NB4" and "NB4Rep2", and removed column 2 "sgRNAs included", using: cut -d, -f1,3-  Wang_mmc3_without_table_description.csv > Wang_mmc3_without_table_description_and_column2.csv)
# Used NB4Rep as otherwise R "run_Intercell_analysis.R" complains: "duplicate 'row.names' are not allowed"
inputScoresFile  = "./rnai_input/Wang_mmc3_without_table_description_and_column2.csv"
outputFilePrefix = "./rnai_output/Wang_mmc3_cancergd"
NumIsoCols = 0 # To Ignore these "Isogenic cell line" columns at right of table (are in "mm7.xlsx" but not in "mm3.xlsx")

countPrevSymbolsUsed = 0
countAliasSymbolsUsed = 0
countMissingEntrezIds = 0

with open(inputScoresFile, "rU") as f:
    header = f.readline().strip().split(delim)
    for i in range(1,len(header)-NumIsoCols):  # ignore position 0, which is 'Gene' and is converted above to 'cell.line'
        if header[i] in cellline_to_cancergd:
            header[i] = cellline_to_cancergd[header[i]]
        tissue = tissue_dict.get(header[i], tissue_dict["default"])
        n.append(tissue_list.index(tissue))
        m[0].append(header[i] + "_" + tissue)

    for line in f:
        c = line.strip().split(delim)
        if len(c) != len(header): print("WARNING: Number of columns different from number of header names:",c)
        if c[0] in alias_to_hgnc:   # c[0] is the gene_symbol
            c[0] = alias_to_hgnc[c[0]]
        
        if c[0] in common_to_entrez_hgnc:
            c[0] += '_'+common_to_entrez_hgnc[c[0]]
            
        elif c[0] in prevsymbol_to_common_hgnc:
            if '|' in prevsymbol_to_common_hgnc[c[0]]:
                print("Prev_symbol %s can be either: %s" %(c[0],prevsymbol_to_common_hgnc[c[0]]))
                c[0] += '_NoEntrezId'                
            else:    
                #print("INFO: Using %s for prev_symbol %s" %(prevsymbol_to_common_hgnc[c[0]],c[0]))
                countPrevSymbolsUsed += 1
                c[0] = prevsymbol_to_common_hgnc[c[0]]
                c[0] += '_'+common_to_entrez_hgnc[c[0]]

        elif c[0] in aliassymbol_to_common_hgnc:
            if '|' in aliassymbol_to_common_hgnc[c[0]]:
                print("Alias_symbol %s can be either: %s" %(c[0],aliassymbol_to_common_hgnc[c[0]]))
                c[0] += '_NoEntrezId'                
            else:    
                print("INFO: Using %s for alias_symbol %s" %(aliassymbol_to_common_hgnc[c[0]],c[0]))
                countAliasSymbolsUsed += 1
                c[0] = aliassymbol_to_common_hgnc[c[0]]
                c[0] += '_'+common_to_entrez_hgnc[c[0]]
                                
        else:
            countMissingEntrezIds += 1
            print("Missing entrez_id for:",c[0])
            c[0] += '_NoEntrezId'
            #print("'"+c[0]+"'  : '',")

        if NumIsoCols==0: m.append(c)
        else: m.append(c[:-NumIsoCols])

print("\ncountPrevSymbolsUsed: %d\ncountAliasSymbolsUsed: %d\ncountMissingEntrezIds %d\n" %(countPrevSymbolsUsed,countAliasSymbolsUsed,countMissingEntrezIds))

if len(m[0]) != len(n): print("ERROR: len(m[0]) != len(n)")

# Transpose. Assumes all rows are the same length (otherwise zip() truncates to the shortest row), which was checked above using: if len(c) != len(header) ...
m = list(zip(*m))

# Write files:
with open(outputFilePrefix+".txt",'w') as f:
    for row in m:
       f.write("\t".join(row) + "\n")

with open(outputFilePrefix+"_tissues.txt",'w') as f:
    f.write(n[0] + "\t" + "\t".join(tissue_list) + "\n")
    for i in range(1,len(m)):
        f.write(m[i][0] + "\t0"*n[i] + "\t1" + "\t0"*(len(tissue_list)-n[i]-1) + "\n")


print("Finished.\n")
