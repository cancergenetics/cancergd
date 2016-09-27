"""
This processes the data from Marcotte et al (2016)
Cell line names are changed to CCLE format, Entrez IDs are appended to Gene Names,
and a tissue_map file created describing the tissue type of each cell line name
"""

import pandas as pd
from collections import defaultdict

colt = pd.read_csv("./rnai_input/breast_zgarp.txt", sep="\t")
colt.rename(columns={'symbol': 'cell.line'}, inplace=True)
colt["cell.line"] = colt["cell.line"] + '_' + \
    colt["gene_id"].map(str)  # Appends ENTREZ_ID to gene name
name_dict = {}
for i in colt.columns.values[3:]:
    name_dict[i] = "%s_BREAST" % i.upper()
colt.rename(columns=name_dict, inplace=True)
colt = colt.T
colt = colt.drop('gene_name')
colt = colt.drop('gene_id')

colt.to_csv("./rnai_output/Marcotte_cancergd.txt", sep="\t", header=False)

# Create Tissue Map
cell_lines = colt.index.values[1:]
tissue_types = defaultdict(set)
for c in cell_lines:
    tissue_types[c.split('_', 1)[1]].add(c)
tissue_types['OTHER'] = set()  # dummy variable to create a 2nd column
ordered_tissues = sorted(tissue_types.keys())
with open('./rnai_output/Marcotte_cancergd_tissues.txt', 'w') as f:
    f.write("cell.line\t")
    f.write("\t".join(ordered_tissues))
    f.write("\n")
    for c in cell_lines:
        f.write("%s\t" % c)
        f.write("\t".join([str(int(c in tissue_types[x]))
                           for x in ordered_tissues]))
        f.write("\n")
