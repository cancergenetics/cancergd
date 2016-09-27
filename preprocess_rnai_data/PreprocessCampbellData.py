"""
This processes the data from Campbell et al (2016)
Cell line names are updated to reflect the genotype data (using intercell_to_cancergd.txt)
and a tissue_map file created describing the tissue type of each cell line. Gene names are 
updated and changed to contain ENTREZ IDs rather than ENSEMBL IDs
"""

import pandas as pd
from collections import defaultdict

# Rename Cell Lines
intercell = pd.read_csv(
    "./rnai_input/Intercell_v18_rc4_kinome_zp0_for_publication.txt", sep="\t")
cell_name_dict = {}
with open("./rnai_input/intercell_to_cancergd.txt", "rU") as f:
    for i in f:
        parts = i.strip().split()
        cell_name_dict[parts[0]] = parts[1]
for i in intercell.index:
    if intercell.loc[i, 'cell.line'] in cell_name_dict:
        intercell.loc[i, 'cell.line'] = cell_name_dict[
            intercell.loc[i, 'cell.line']]

# Rename Genes
gene_name_dict = {}
with open("./rnai_input/Campbell_gene_update.txt", "rU") as f:
    for i in f:
        parts = i.strip().split()
        gene_name_dict[parts[0]] = parts[1]
intercell.rename(columns=gene_name_dict, inplace=True)
intercell.to_csv("./rnai_output/Campbell_cancergd.txt", sep="\t", index=False)

# Create Tissue Map
cell_lines = intercell['cell.line'].values
tissue_types = defaultdict(set)
for c in cell_lines:
    tissue_types[c.split('_', 1)[1]].add(c)
ordered_tissues = sorted(tissue_types.keys())
with open('./rnai_output/Campbell_cancergd_tissues.txt', 'w') as f:
    f.write("cell.line\t")
    f.write("\t".join(ordered_tissues))
    f.write("\n")
    for c in cell_lines:
        f.write("%s\t" % c)
        f.write("\t".join([str(int(c in tissue_types[x]))
                           for x in ordered_tissues]))
        f.write("\n")
