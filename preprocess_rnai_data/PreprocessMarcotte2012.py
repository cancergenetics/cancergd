"""
This processes the data from Marcotte et al (2012).
zGARP scores for each cell line are Z-score normalized
Cell line names are changed to CCLE format, Entrez IDs are appended to Gene Names,
and a tissue_map file created describing the tissue type of each cell line name
"""

import pandas as pd
import csv
from collections import defaultdict

entrez_to_common_hgnc = {}
with open("../input_data/hgnc_complete_set.txt", "r") as f: 
    reader = csv.DictReader(f, delimiter="\t")
    for i in reader :        
        if i['entrez_id'] :
            entrez_to_common_hgnc[int(i['entrez_id'])] = i['symbol']

garp_map = {}
with open("./rnai_input/Marcotte2012_to_cancergd.txt", "r") as f:
    for i in f :
        parts = i.strip().split("\t")
        garp_map[parts[0]] = parts[1]

garp = pd.read_csv("./rnai_input/GARP-score.txt", sep="\t", index_col = 2)
garp.index.names = ["cell.line"]
del garp["Refseq"]
del garp["Description"]
del garp["Gene name"]
garp.rename(columns=garp_map, inplace = True)

garp = (garp - garp.mean()) / garp.std()

garp = garp.T

gene_mapping = {}
for i in garp.columns.values :
    if i in entrez_to_common_hgnc :
        gene_mapping[i] = "%s_%s" % (entrez_to_common_hgnc[i],i)
    else :
        gene_mapping[i] = "%s_%s" % ("UNKNOWN",i)

garp.rename(columns=gene_mapping, inplace = True)

garp.to_csv("./rnai_output/Marcotte2012_cancergd.txt", sep="\t", header=True)

# Create Tissue Map
cell_lines = garp.index.values[1:]
tissue_types = defaultdict(set)
for c in cell_lines:
    tissue_types[c.split('_', 1)[1]].add(c)
tissue_types['OTHER'] = set()  # dummy variable to create a 2nd column
ordered_tissues = sorted(tissue_types.keys())
with open('./rnai_output/Marcotte2012_cancergd_tissues.txt', 'w') as f:
    f.write("cell.line\t")
    f.write("\t".join(ordered_tissues))
    f.write("\n")
    for c in cell_lines:
        f.write("%s\t" % c)
        f.write("\t".join([str(int(c in tissue_types[x]))
                           for x in ordered_tissues]))
        f.write("\n")
