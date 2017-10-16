'''
This processes the data from DRIVE (2017): 
which is shRNA-based screens ....

.......to finish .....
Cell line names are changed to CCLE format, Entrez IDs are appended to Gene Names,
and a tissue_map file created describing the tissue type of each cell line name

Creates a mapping from Campbell style IDs (Symbol_ENSGXXX) to that used by CancerGD
(Symbol_ENTREZ). Also updates gene names to current symbols from HGNC
'''

"""
To export the data from RDS format to .csv file, in R:

  a<-readRDS( "rnai_input/DRIVE_ATARiS_data.RDS")
  write.table(a,file="rnai_input/DRIVE_ATARiS_data_exported_from_R.csv", quote=FALSE, sep="\t")

  b<-readRDS( "rnai_input/DRIVE_RSA_data.RDS") 
  write.table(b,file="rnai_input/DRIVE_RSA_data_exported_from_R.csv", quote=FALSE, sep="\t")

Then manually edited the above output files to add "Name" as first header for first column.

  Where:
    write.table(x, file = "", append = FALSE, quote = TRUE, sep = " ",
                eol = "\n", na = "NA", dec = ".", row.names = TRUE,
                col.names = TRUE, qmethod = c("escape", "double"),
                fileEncoding = "")

"""

import csv

# The following were found manually by going to: https://www.ncbi.nlm.nih.gov/gene/?term=(HDGFRP3%5BGene+Name%5D)+AND+human%5BOrganism%5D
# And using Gene search expression: (HDGFRP3[Gene Name]) AND human[Organism]
common_to_entrez_hgnc = {  # Added some not currently in the hgnc downloaded file (as updated on entrez on Sept 2017):
  'HDGFL2' : '84717',
  'HDGFL3' : '50810',
  'SF3B6'  : '51639',
  'SBK3'   : '100130827',
  'POMK'   : '84197',
  'PRAG1'  : '157285',
  'SF3B6'  : '51639',
  'SBK3'   : '100130827',
  'HDGFRP2': '84717',
  'SGK494' : '124923',  
}

"""
In the DRIVE RSA data:
INFO: Using C15orf65 for alias_symbol FLJ27352
Missing entrez_id for: 'FLJ40852'
Missing entrez_id for: 'FLJ45256'
INFO: Using PCAT4 for alias_symbol GDEP
INFO: Using MAP3K21 for alias_symbol KIAA1804
Missing entrez_id for: 'LOC100507203'
Missing entrez_id for: 'LOC100996481'
Missing entrez_id for: 'LOC375295'
Missing entrez_id for: 'LOC440356'
Missing entrez_id for: 'LOC440563'
Missing entrez_id for: 'LOC554223'
Missing entrez_id for: 'LOC642852'
Missing entrez_id for: 'LOC81691'
Alias_symbol MLL4 can be either: KMT2B|KMT2D
INFO: Using STK26 for alias_symbol MST4
INFO: Using NIM1K for alias_symbol NIM1
INFO: Using ACP7 for alias_symbol PAPL
INFO: Using RNF217-AS1 for alias_symbol STL
INFO: Using MAP3K20 for alias_symbol ZAK
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
# For mm7.xlsx:
'C11orf30' : 'EMSY',    #  56946
'C17orf70' : 'FAAP100', #  80233 
'C17orf89' : 'NDUFAF8', # 284184
'MLLT4'    : 'AFDN',    #   4301
'GC11orf35': 'C11orf35', # (ie. no "G" at the start). 'C11orf35' is 'LMNTD2'

'HDGFRP3'  : 'HDGFL3',
'SGK196'   : 'POMK',
'SGK223'   : 'PRAG1',
'SF3B14'   : 'SF3B6',
'SGK110'   : 'SBK3',
}
# 'STRA13' : 'MHF2',  # Probably.


"""
# Aliases still needing found for mm3.xlsx:

***** ... this was for WANG:
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

# This mapping fixed now:
#    ******** The mapping to "A673_SOFT_TISSUE" means this is messed up!!!! when the tries to output the tissue file as uses the original tissue before mapping :(

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
# 'SEM'      : 'SEM',  # <-- Only this is in the DRIVE_RSA data.
'SHI-1'    : 'SHI1',
# 'U937'     : 'U937',
# In file "mm3.xlsx":
'TF-1'     : 'TF1',
}


with open("./rnai_input/DRIVE_name_mapping_cancergd.txt", "rU") as f:  # <-- May need to add to this cell line list.
    line = f.readline().strip()     # Ignore the first line which is: "DepMap Name	CancerGD Name"
    if line != "Drive Name\tCancerGD Name\tNotes":
        print("Expected header line at start of 'DRIVE_name_mapping_cancergd'")
        sys.exit(1)
    print("Reading Drive Cell-line to CancerGD mapping file:")
    for line in f:
        parts = line.strip().split("\t")
        if len(parts) <2 or parts[1]=='':  # To skip the lines that don't have the second column
            if len(parts)>2:
                print("Ignoring line: '%s'" %(line))  # Probably has a note: "Potentially ...." 
            continue
        if parts[0] in cellline_to_cancergd:
            print("'%s' is already in as cellline_to_cancergd as '%s', but will be replaced with '%s'" %(parts[0],cellline_to_cancergd[parts[0]], parts[1]))
        cellline_to_cancergd[parts[0]] = parts[1]
        print("'%s' => '%s'" %(parts[0], parts[1]))


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


"""
tissue_dict = {
"KE97"    : "STOMACH",
"ML1"     : "THYROID",
"default" : "HAEMATOPOIETIC_AND_LYMPHOID_TISSUE",    # as rest are "HAEMATOPOIETIC_AND_LYMPHOID_TISSUE"
}

tissue_list = sorted(list(set(tissue_dict.values())))
"""

m = [["cell.line",],] # 2D array to store data to transpose later.
n = ["cell.line",] # 1D array of position of the tissue in tissue_list

# delim="," # or "\t"
delim="\t"

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
# inputScoresFile  = "./rnai_input/DRIVE_without_table_description_and_column2.csv"

dataset = "DRIVE_ATARiS"
# dataset = "DRIVE_RSA" # <-- Not using this RSA data.
print("\nConverting dataset: '%s' ...\n" %(dataset))

inputScoresFile  = "./rnai_input/"+dataset+"_data_exported_from_R.csv";
outputFilePrefix = "./rnai_output/"+dataset+"_cancergd"

# NumIsoCols = 0 # To Ignore these "Isogenic cell line" columns at right of table (are in "mm7.xlsx" but not in "mm3.xlsx")

countPrevSymbolsUsed = 0
countAliasSymbolsUsed = 0
countMissingEntrezIds = 0
countMultipleGenenames = 0


"""
# In DRIVE data some gene names have several names separated by commas, eg in "DRIVE_ATARiS_data_exported_from_R.csv":
ACAD11,NPHP3-ACAD11
AGAP4,AGAP11,AGAP6,AGAP9,AGAP7,AGAP10,AGAP8,AGAP5
AGAP4,AGAP6,AGAP9,AGAP7,AGAP10,AGAP8,AGAP5
AKR1B10,AKR1B15
AKR1C1,AKR1C2
ALG10,ALG10B
ALPP,ALPPL2
ANKHD1,ANKHD1-EIF4EBP3
ANKRD20A1,ANKRD20A3,ANKRD20A2,ANKRD20A4
ANKRD36B,ANKRD36,ANKRD36C
ARHGAP11A,ARHGAP11B
ARHGAP19,ARHGAP19-SLIT1
ARHGAP8,PRR5-ARHGAP8
ARL17A,LOC100294341,ARL17B,LOC100996709
ARPC4,ARPC4-TTLL3
ATAD3A,ATAD3B
ATAD3A,ATAD3B,ATAD3C
ATP5J2,ATP5J2-PTCD1
AURKA,AURKAPS1
BIRC2,BIRC3
BMI1,COMMD3-BMI1
BTN3A3,BTN3A2,BTN3A1
C1QTNF3,C1QTNF3-AMACR
C1QTNF9,C1QTNF9B
C4A,C4B,LOC100293534
CBWD1,CBWD2,CBWD5,CBWD3,CBWD6,CBWD7
CCDC144A,CCDC144B,CCDC144C
CCL4,CCL4L1,CCL4L2
CDC14B,CDC14C
CDK11B,CDK11A
CDK3,TEN1-CDK3
CDY1,CDY1B
CDY1,CDY2A,CDY2B,CDY1B
CEACAM3,CEACAM6
CEL,CELP
CES1,LOC100653057
CFHR4,CFHR3
CHKB,CHKB-CPT1B
CHRNA7,CHRFAM7A
CKMT1B,CKMT1A
CLCNKA,CLCNKB
CSH1,CSH2
CSNK2A1,CSNK2A1P
CTAG1B,CTAG1A
CTAG1B,CTAG2,CTAG1A
CTNND1,TMX2-CTNND1
CYP11B1,CYP11B2
CYP21A2,CYP21A1P
CYP2D7P1,CYP2D6
CYP3A7,CYP3A7-CYP3AP1
CYP4Z2P,CYP4Z1
DAZ1,DAZ3,DAZ2,DAZ4
DAZ1,DAZL,DAZ3,DAZ2,DAZ4
DCAF8L1,DCAF8L2
DDX19B,DDX19A
DDX39B,ATP6V1G2-DDX39B
DHX40,TBC1D3P1-DHX40P1
EEF1E1,EEF1E1-MUTED
EGLN2,RAB4B-EGLN2
EIF4A1,SENP3-EIF4A1
EIF4EBP3,ANKHD1-EIF4EBP3
EIF5A,EIF5AL1
ENO1,EDARADD
ERCC5,BIVM-ERCC5
ESPN,ESPNP
FAM22A,FAM22D
FAM22F,FAM22G
FBXW10,CDRT1
FCGR2A,FCGR2B,FCGR2C
FCGR3A,FCGR3B
FNTB,CHURC1-FNTB
FOXB1,FOXB2
FOXO3,FOXO3B
FRMPD2,FRMPD2P1
GABARAPL1,GABARAPL3
GLUD1,GLUD2
GMCL1,GMCL1P1
GNG10,DNAJC25-GNG10
GP1BB,SEPT5-GP1BB
GPR89B,GPR89A,GPR89C
GRAP,GRAPL
GSTA1,GSTA2
GSTA1,GSTA2,GSTA3,GSTA7P
GSTM1,GSTM2,GSTM4
GSTT2,GSTT2B
GTF2H2,GTF2H2B,GTF2H2C
GTF2I,GTF2IP1,LOC100093631
GTF2IRD2,GTF2IRD2B,GTF2IRD2P1
H3F3A,H3F3AP4
HBA1,HBA2
HBG1,HBG2
HLA-B,HLA-C
HMGN2,TRMT5
HNRNPA1,HNRNPA1L2,HNRNPA1P10
HNRNPC,HNRNPCL1,LOC440563
HNRNPCL1,LOC440563
HOXA9,HOXA10-HOXA9
HS3ST3B1,HS3ST3A1
HSP90AB1,HSP90AB3P
HSPE1,HSPE1-MOB4
IFNA1,IFNA13
INO80B,INO80B-WBP1
JMJD7-PLA2G4B,PLA2G4B
KANSL1,LOC100996748
KCTD14,NDUFC2-KCTD14
KIF4A,KIF4B
LEFTY2,LEFTY1
LGALS7,LGALS7B
LGALS9B,LGALS9C
LGALS9,LGALS9B,LGALS9C
LILRB3,LILRA6
LIMS1,LIMS3,LIMS3-LOC440895,LIMS3L
LOC647859,OCLN
MAGEA12,LOC101060230
MAGEA2,MAGEA2B
MAGEA3,MAGEA6
MAGEA9,MAGEA9B
MAGED4B,MAGED4
MAP1LC3B,MAP1LC3B2
MAP2K2,LOC407835
MBD3L2,MBD3L5,MBD3L4,MBD3L3,LOC729458
MED27,CRSP8P
MEF2BNB-MEF2B,MEF2B
METTL2B,METTL2A
MFRP,C1QTNF5
MMP3,MMP10
MSH5,MSH5-SAPCD1
MST1,MST1P2
MYL12A,MYL12B
NACA,NACA2
NCF1,NCF1B,NCF1C
NCF1,NCF1C
NEDD8,NEDD8-MDP1
NLGN4Y,NLGN4X
NME1,NME1-NME2
NME2,NME1-NME2
NOMO1,NOMO2,NOMO3
NSF,NSFP1
NUDT3,RPS10-NUDT3
NUTF2,LOC128322
OPN1MW,OPN1LW,OPN1MW2,LOC101060233
OR2T12,OR2T8,OR2T33
OR2T2,OR2T35
OR2T34,OR2T3
OR2T4,OR2T29,OR2T5
OR51A4,OR51A2
OR52I2,OR52I1
ORM1,ORM2
P2RY11,PPAN-P2RY11
PA2G4,PA2G4P4
PABPC1L2A,PABPC1L2B
PABPC3,PABPC1
PABPN1,BCL2L2-PABPN1
PAK2,LOC646214
PGAM1,PGAM4
PHB,ZNF607
PI4KA,PI4KAP2
PI4KA,PI4KAP2,PI4KAP1
PMS2,PMS2CL
POTEE,POTEI,POTEJ,POTEF
PPYR1,LOC100996758
PRDM7,PRDM9
PRKRIP1,LOC100630923
PSG2,PSG11
PTEN,PTENP1
RAB4B,MIA-RAB4B,RAB4B-EGLN2
RAB6A,RAB6C,WTH3DI
RAB6A,WTH3DI
RAB6C,WTH3DI
RABL2B,RABL2A
RANBP2,RGPD5,RGPD4,RGPD1,RGPD3,RGPD8,RGPD6,RGPD2
RBM4,RBM14-RBM4
RBM4,RBM4B
RBMX,RBMXL1
RBMY1A1,RBMY1F,RBMY1B,RBMY1D,RBMY1E,RBMY1J
RDH14,NT5C1B-RDH14
RDH5,BLOC1S1-RDH5
RFFL,RAD51L3-RFFL
RNF5,RNF5P1
RPS10,RPS10-NUDT3
RRN3,RRN3P2,RRN3P1
SAE1,LOC341056
SBDS,SBDSP1
SCXB,SCXA
SEPT5,SEPT5-GP1BB
SFTPA1,SFTPA2
SGK3,C8orf44-SGK3
SIRPB1,SIRPA
SLC2A3,SLC2A14
SLX1B,SLX1A,SLX1A-SULT1A3,SLX1B-SULT1A4
SMG1,LOC440354,LOC595101,SMG1P1,LOC100271836
SMN1,SMN2
SOHLH2,CCDC169-SOHLH2
SRP19,ZRSR2
SRSF10,LOC100996657
STAG3L1,STAG3L3,STAG3L2
STEAP1,STEAP1B
STON1,STON1-GTF2A1L
SULT1A2,SULT1A1
SULT1A2,SULT1A1,SULT1A3,SULT1A4,SLX1A-SULT1A3,SLX1B-SULT1A4
SULT1A3,SULT1A4,SLX1A-SULT1A3,SLX1B-SULT1A4
TAF1,TAF1L
TARDBP,LOC643387
TBC1D3F,TBC1D3B,TBC1D3C,TBC1D3G,TBC1D3,TBC1D3H
TEX28,LOC101060234
THOC3,LOC728554
TM4SF19,TM4SF19-TCTEX1D2
TMED10,TMED10P1
TMEFF1,MSANTD3-TMEFF1
TNFRSF6B,RTEL1-TNFRSF6B
TNFSF13,TNFSF12-TNFSF13
TNNI3K,FPGT-TNNI3K
TPM3,TPM3P9
TPT1,FLJ44635
TRIM13,KCNRG
TTC30A,TTC30B
UBE2F,UBE2F-SCLY
UBE2M,UBE2MP1
UBE2N,UBE2NL
UBE2V1,TMEM189-UBE2V1
ULBP2,RAET1L
YWHAE,LOC649395
"""

tissues = []
numMissingCelllines = 0


print("\ncellline_to_cancergd:\n", cellline_to_cancergd)
if 'WM793_SKIN' in cellline_to_cancergd: print("** Found WM793_SKIN")

with open(inputScoresFile, "rU") as f:
    celllines = f.readline().strip().split(delim)
    for i in range(1,len(celllines)):  # ignore position 0, which is 'Gene' and is converted above to 'cell.line' in array m[[]]
        cellline = celllines[i].upper()  # As are lower case in DRIVE output from R.

        # print("Read cellline: '%s'" %(cellline))

        pos = cellline.find('_')
        if pos == -1:
            print("**** ERROR: Cellline has no '_' character in: '%s'" %(cellline))

        # cellline_name = cellline[:pos]

        # print("Searching for cellline_name '%s' in cellline_to_cancergd" %(cellline_name))

        # print("    So cellline: '%s'  name: '%s'  tissue: '%s'" %(cellline,cellline_name,tissue))

        if cellline in cellline_to_cancergd:  # This is correctly 'cellline in ..' not 'cellline_name in ..' 
            print("  Using cancergd cellline '%s' for DRIVE cellline '%s'" %(cellline_to_cancergd[cellline],cellline))
            cellline = cellline_to_cancergd[cellline]  # +'_'+tissue
            pos = cellline.find('_')  # As pos will have changed with renaming of the cellline.
        
        if cellline not in cellines_in_cancergd:
            print("  Cellline not found in cancergd celllines: '%s' " %(cellline))
            numMissingCelllines += 1

        celllines[i] = cellline
#        tissue = tissue_dict.get(header[i], tissue_dict["default"])
#        n.append(tissue_list.index(tissue))
#        m[0].append(header[i] + "_" + tissue)

        m[0].append(cellline)

        tissue = cellline[pos+1:]
        if tissue in tissues:
            index = tissues.index(tissue)
        else:
            index = len(tissues)
            tissues.append(tissue)
        n.append(index)

    for line in f:
        c = line.strip().split(delim)
        if len(c) != len(celllines): print("WARNING: Number of columns %d different from number of header names %d for: %s" %(len(c),len(celllines),c))

        # In DRIVE data, some have several names separated by commas:
        names = c[0].split(',')
        if len(names) > 1:
            # print("Skipping as multiple gene names: %s" %(c[0]))
            countMultipleGenenames += 1
            continue

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
            print("Missing entrez_id for: '%s'" %(c[0]))
            c[0] += '_NoEntrezId'
            #print("'"+c[0]+"'  : '',")

        # if NumIsoCols==0: 
        m.append(c)
        # else: m.append(c[:-NumIsoCols])

print("\nNumber of missing cell-lines: %d" %(numMissingCelllines))
print("\ncountPrevSymbolsUsed: %d\ncountAliasSymbolsUsed: %d\ncountMissingEntrezIds: %d\nSkipped as have multiple genenames: %d\n" %(countPrevSymbolsUsed,countAliasSymbolsUsed,countMissingEntrezIds,countMultipleGenenames))

if len(m[0]) != len(n): print("ERROR: len(m[0]) != len(n)")

# Transpose. Assumes all rows are the same length (otherwise zip() truncates to the shortest row), which was checked above using: if len(c) != len(celllines) ...
m = list(zip(*m))

# Write files:
with open(outputFilePrefix+".txt",'w') as f:
    for row in m:
       f.write("\t".join(row) + "\n")

with open(outputFilePrefix+"_tissues.txt",'w') as f:
    f.write(n[0] + "\t" + "\t".join(tissues) + "\n")
    for i in range(1,len(m)):
#        pos = m[i][0].find('_')
#        tissue = m[i][0][pos+1:]
#        index = tissues.index(tissue)
        f.write(m[i][0] + "\t0"*n[i] + "\t1" + "\t0"*(len(tissues)-n[i]-1) + "\n")

print("Finished.\n")
