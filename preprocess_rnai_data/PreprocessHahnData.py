'''
This script gets the Achilles ATARIS 2017 scores (Hahn et al) into a format usable by the R scripts.
   Paper: http://www.cell.com/cell/fulltext/S0092-8674(17)30651-7
This is quite convoluted as the Achilles data uses gene names rather than IDs. Mapping from gene name 
to Entrez ID is non-trivial as there is not a one-to-one mapping. To address this here we use two 
mappings - one going from shRNA clone ID to Entrez ID and another going from Ataris Solution IDs to 
shRNA clone IDs. Combining the two allows us to map from ATARIS solution ID to Entrez ID.
'''

# After running this script, can run the R analysis, using:
#   setwd("/Users/sbridgett/Documents/DjangoApps/cancergd/R_scripts/")
#   source("run_intercell_analysis.R")

import pandas as pd
import csv
from collections import defaultdict


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



rna_input_file = "./rnai_input/Achilles_v2.20.2_GeneSolutions.gct"
# rna_input_file = "./rnai_input/Achilles_v2.20.2_GeneSolutions.gct_without_NA_rows"

achilles = pd.read_csv(rna_input_file,   # was: Achilles_QC_v2.4.3.rnai.Gs.gct",
                       skiprows=(0, 1), sep="\t", index_col=0)  # Skip first two rows which are: #1.2  and: 17098   501
name_dict = {}
# Note: Hahn2017_name_mapping_cancergd.txt includes: 'achilles_to_cancergd.txt' at end.
#   ie: cat  DepMap_name_mapping_cancergd.txt  NewLineChar.txt   achilles_to_cancergd.txt  >  Hahn2017_name_mapping_cancergd.txt
with open("./rnai_input/Hahn2017_name_mapping_cancergd.txt", "rU") as f:  # <-- May need to add to this cell line list.
    line = f.readline().strip()     # Ignore the first line which is: "DepMap Name	CancerGD Name"
    if line != "DepMap Name\tCancerGD Name":
        print("Expected header line at start of 'Hahn2017_name_mapping_cancergd.txt'")
        sys.exit(1)
    print("Cell-line mappings to CancerGD:")
    for line in f:
        parts = line.strip().split("\t")
        if len(parts) <2 or parts[1]=='':  # To skip the lines that don't have the second column
            continue
        if len(parts)>2:
            print("More than two columns: '%s'" %(line))
            sys.exit(2)
        name_dict[parts[0]] = parts[1]
        print("'%s' => '%s'" %(parts[0], parts[1]))

# NOTE: That 786O_KIDNEY 7860_KIDNEY are different as the first incorrectly has an "O" instead of a zero.


#achilles.dropna(thresh=2)  # To keep only rows with at least two no NA values.
# achilles.dropna(how='any')  # To remove any rows that have one or more NA values.  - but doesn't actually remove the 'NA' rows 

# Using: grep -v $'\t'NA$'\t' Achilles_v2.20.2_GeneSolutions.gct > Achilles_v2.20.2_GeneSolutions.gct_without_NA_rows

# AS:

# At commandline:  

# (1) grep NA$'\t' Achilles_v2.20.2_GeneSolutions.gct | wc -l
#    5760

# or:
# (2) grep $'\t'NA$'\t' Achilles_v2.20.2_GeneSolutions.gct | wc -l
#    5752

# or:
# (3) grep $'\t'NA Achilles_v2.20.2_GeneSolutions.gct | wc -l
#    5800


# awk '/NA\t/' Achilles_v2.20.2_GeneSolutions.gct | wc -l
#    5760
    
# awk '/\tNA\t/' Achilles_v2.20.2_GeneSolutions.gct | wc -l
#    5752
    
# awk '/\tNA/' Achilles_v2.20.2_GeneSolutions.gct | wc -l
#    5800
#    as a cellline and some gene Description start with NA, eg:   "NAT1     NAT1   ...."
    
# awk '/NA\n/' Achilles_v2.20.2_GeneSolutions.gct | wc -l
#      0    
# So no lines end with "NA\n" so can just test for: "\tNA\t"


# wc -l Achilles_v2.20.2_GeneSolutions.gct
#   17101

# awk '/NA\n/' Achilles_v2.20.2_GeneSolutions.gct | wc -l
#       0
       
# grep -v $'\t'NA$'\t' Achilles_v2.20.2_GeneSolutions.gct | wc -l
#   11349

# grep -v $'\t'NA Achilles_v2.20.2_GeneSolutions.gct | wc -l
#   11301
   
# grep -v NA$'\t' Achilles_v2.20.2_GeneSolutions.gct | wc -l
#   11341
"""
eg:
ASTL    ASTL    NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA
      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA
      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA
      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA
      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA
      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA
      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA
      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA
      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA
      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      NA      0.066104396754  -0.626414665472 -0.793573073217 -0.285284758483 0.0292186362583 -0.482626746015 0.377605277916  -0.0907947627426        -0.883886146595 0.781756281284  -0.301921377263 -0.119037403672 0.382437819561  -0.0763763597997        0.426841747306  -0.552342100903 -0.258072003478 -0.386055135095 0.160655846822  -0.185425434805 0.00582834247326        0.530622559697  0.62291618293   -0.0492428267891        -0.350682514688 0.0656686757859 0.0901086609941 -0.266033813895 -0.054590311397 0.139028242407  0.0817111296097 -0.22190716313  0.0772350869379 0.374990952107  -0.288255583265 -0.578881468957 0.782548501226  0.39036001898   -0.426775240109 0.2223301693    0.628065612553  0.334865012049  -0.257675893507 -0.135317523478 0.407036248758  0.174876194779  0.130591100026  -0.400235872055 -0.0243869261114        -0.0197564005509        -0.556303200613 -0.407761961503 1.42305832427   0.172499534953  -0.2863542554050.578947976154  -0.0403699634396        0.650643880897  0.160101292862  0.256752125776  -0.963900360729 0.538148649145  0.756801353114  -0.611758596547 -0.218104507409 -0.250981634998 -0.189069646537 -0.942906532268 -0.277837891029 0.052042492785  -0.548381001194 1.24956215699   -0.382608978348 0.305196375224  -0.530952162471 -0.169620646963 -0.327193193411 -0.0801790155209        -0.572939819393 -0.392194839645 -0.667610102452 -0.221431831165 0.0253248752438 -0.175483074533 0.211476756096  -0.120621843556 0.443478366086  0.465264414489
  0.157843466028  -0.839917939819 0.539336979058  -0.433112999645 -0.314953395308 0.536960319232  0.0428923524558 0.718774795902  -0.103351448822 0.195553135263  -0.356346887273 -0.265677314921 -0.190218365453 0.0143407457492 -0.0247553083844        0.0785422498421 -0.36621002555  0.413374008293  -0.661668452888 -0.24931797312  -0.687019491029 -1.08788278164 0.0283986886185 0.421296207712  0.547655288448  -0.229393641581 0.17063781809   0.000867223530998       -0.162530278483 -0.207409538193 -0.746039876702 -0.376548495792 0.46169942475   0.0432092404326 -0.469951226944 0.101991960123  0.377842943898  0.438725046434  -0.121057564524 1.49039701933   -0.237474284988 0.535771989319  0.417731217974  0.283370715825  0.0272935417995 -0.46004847767  0.00997165276949        0.196503799193  -0.750397086382 0.27647840233   -0.582446458696 0.301314497509  1.47692928032   0.280043392069  0.19000759567
   0.0312308749108 -0.127118047079 -0.203606882472 -0.261438938231 -0.656519023265 0.0336392235342 -0.195803516044 0.165884498438  0.032973758783  -0.517484423459 -0.267855919761 0.604299014295  0.57340243656   -0.125652440187 -0.288572471242 0.300839165544  0.0682037796001 -0.261795437205 -0.694941690448 0.289272754392  0.0464573421945 0.686689888254  -0.13175253374  0.142434788158  0.604695124266  0.569837446822  0.341876158535  0.70966426657   0.497745432107  -0.123236169364 -0.333808229926 0.565876347112  -0.0359652205625        0.393449676754  -0.465990127234 -0.401424201968 -0.236642454049 0.397133499484  -0.106401495598 -0.300020049403 -0.0667904985025        0.440309486318  -0.0488467168181        -0.566998169829 -0.11796790675  0.134037256773  -0.319865158948 -0.213866130719 -0.00741757495558       0.539733089029  -0.215094071629 -0.559868190351 0.191156314586  -0.706428879606 0.557954147693  -0.350761736683 -0.282353544698 -0.444204078832 -0.286156200419 -0.65453847341  0.845529986609  0.336053341962  0.223439277219  0.366593420723  -0.135872077438 -0.175601907525 0.0655894537917 0.237025849222  -0.315864448241 0.417731217974  0.106111503821  0.432387286899  -0.134644136528 0.523096470249  -0.140466953101 -0.0153754242721        0.00830402979175        0.263921716251  -0.0524513175538        -0.249951749074 -0.599479187447 0.180540567364  -0.410930841271 0.754028583317  -0.190733308415 0.397925719426  -0.169145314998 0.787697930849  -0.0057301464793        -0.0279043826535        0.0383172822913 0.264080160239  0.207555267383  0.344530095341  0.484673803066  -0.407365851532 0.521512030365  -0.137971460284 -0.0402907414454        0.276399180336  0.225895159039  0.590039055341  0.172380701962  0.408620688642  -0.0879427709517        -0.798326392868 0.168617657238  0.153010924382  0.712833146338  -0.0308791685354        -0.0676223294415        0.352293850771  0.406640138787  0.128174829203  -0.677116741755 -0.814170791707 -0.436677989383 0.481108813327  -0.207924481155 -0.185425434805 -0.254190125763 -0.673947861987 0.31343546262   -0.0142465108549        -0.354960502375 -0.109372320381 -0.724253828299 -0.262785712133 -0.0590663540688        -0.13515907949  0.0112233602777 0.146277054876  -0.131079146789 0.403471259019  0.175945691701  0.403075149048  -0.194971685105 0.0474872281189 -0.0060193067581
        -0.0927753125974        -0.431528559761 -0.294434898812
"""        

achilles.rename(columns=name_dict, inplace=True)
achilles = achilles.T
achilles.drop('Description', inplace=True)   # Description column is same as Name column.

# Manually remapped ENTREZ IDs (from Stephen)
entrez_ids_renamed = {
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
}

 


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
for x in achilles.columns.values:
    # name, solution_id, ataris_string = x.split('_')  # As format was: "A2ML1_1_01110",  but is now just: RPS6KA1
    if x not in symbol_to_id_map:
      print("Entrez_id not found in symbol_to_id_map for gene_symbol="+x)
    name_dict[x] = x + '_' + symbol_to_id_map[x]
#sys.exit(0)
    
achilles.index.names = ['cell.line']

achilles.rename(columns=name_dict, inplace=True)

achilles.to_csv("./rnai_output/Hahn_cancergd.txt", sep="\t")

# Create Tissue Map
cell_lines = achilles.index.values

numMissingCelllines = 0 
tissue_types = defaultdict(set)
for c in cell_lines:
    if c not in cellines_in_cancergd:
        print("Cellline not found in cancergd celllines: '%s' " %(c))
        numMissingCelllines += 1
        cellname = c.split('_', 1)[0]
        if cellname in cellline_to_cancergd:
            print("BUT could use cancergd cellline '%s' for Hahn cellline '%s'" %(cellline_to_cancergd[cellname],c))
            # cellline = cellline_to_cancergd[cellname]+'_'+tissue
    tissue_types[c.split('_', 1)[1]].add(c)
print("Number of missing cell-lines: %d" %(numMissingCelllines))
    
ordered_tissues = sorted(tissue_types.keys())
with open('./rnai_output/Hahn_cancergd_tissues.txt', 'w') as f:
    f.write("cell.line\t")
    f.write("\t".join(ordered_tissues))
    f.write("\n")
    for c in cell_lines:
        f.write("%s\t" % c)
        f.write("\t".join([str(int(c in tissue_types[x]))
                           for x in ordered_tissues]))
        f.write("\n")
