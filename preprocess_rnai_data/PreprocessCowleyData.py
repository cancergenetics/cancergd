'''
This script gets the Achilles ATARIS scores (Cowley et al) into a format usable by the R scripts.
This is quite convoluted as the Achilles data uses gene names rather than IDs. Mapping from gene name 
to Entrez ID is non-trivial as there is not a one-to-one mapping. To address this here we use two 
mappings - one going from shRNA clone ID to Entrez ID and another going from Ataris Solution IDs to 
shRNA clone IDs. Combining the two allows us to map from ATARIS solution ID to Entrez ID.
'''
import pandas as pd
import csv
from collections import defaultdict

achilles = pd.read_csv("./rnai_input/Achilles_QC_v2.4.3.rnai.Gs.gct",
                       skiprows=(0, 1), sep="\t", index_col=0)
name_dict = {}
with open("./rnai_input/achilles_to_cancergd.txt", "rU") as f:
    for i in f:
        parts = i.strip().split()
        name_dict[parts[0]] = parts[1]
achilles.rename(columns=name_dict, inplace=True)
achilles = achilles.T
achilles.drop('Description', inplace=True)

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

shRNA_map = {}  # MAPS shRNAs to ENTREZ IDs
with open("./rnai_input/CP0004_20131120_19mer_trans_v1.chip", "rU") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for r in reader:
        merged_name = "%s_%s" % (r['Barcode Sequence'], r['Gene Symbol'])
        if r['Gene ID'] in entrez_ids_renamed:
            entrez_id = entrez_ids_renamed[r['Gene ID']]
        else:
            entrez_id = r['Gene ID'].strip()
        if merged_name in shRNA_map:
            if shRNA_map[merged_name] != entrez_id:
                print merged_name, entrez_id, shRNA_map[merged_name]
        else:
            shRNA_map[merged_name] = entrez_id

ATARIS_map = {}
with open("./rnai_input/Achilles_QC_v2.4.3.rnai.shRNA.table.txt", "rU") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for r in reader:
        if r['isUsed'] == 'TRUE':
            ATARIS_map[r['sol.name']] = shRNA_map[r['shRNA']]

name_dict = {}
for x in achilles.columns.values:
    name, solution_id, ataris_string = x.split('_')
    new_name = name + solution_id + '_' + ATARIS_map[x]
    name_dict[x] = new_name
achilles.index.names = ['cell.line']

achilles.rename(columns=name_dict, inplace=True)

achilles.to_csv("./rnai_output/Cowley_cancergd.txt", sep="\t")

# Create Tissue Map
cell_lines = achilles.index.values
tissue_types = defaultdict(set)
for c in cell_lines:
    tissue_types[c.split('_', 1)[1]].add(c)
ordered_tissues = sorted(tissue_types.keys())
with open('./rnai_output/Cowley_cancergd_tissues.txt', 'w') as f:
    f.write("cell.line\t")
    f.write("\t".join(ordered_tissues))
    f.write("\n")
    for c in cell_lines:
        f.write("%s\t" % c)
        f.write("\t".join([str(int(c in tissue_types[x]))
                           for x in ordered_tissues]))
        f.write("\n")
