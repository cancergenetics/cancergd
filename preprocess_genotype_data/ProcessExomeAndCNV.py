"""

Annotates cell lines according to the presence or absence of likely functional
alterations in a panel of cancer driver genes

"""
import pandas as pd
from collections import defaultdict
import csv


# Read list of ~500 cancer genes from Campbell et al
cancer_genes = {}
cancer_gene_names = {}
with open("./genotype_input/cancer_gene_classifications_v0.4.txt", "rU") as f:
    for line in f:
        if not line.startswith('#'):
            parts = line.strip().split()
            cancer_genes[parts[0]] = parts[-1]
            cancer_gene_names[parts[0]] = "%s_%s_%s" % (
                parts[0], parts[1], parts[2])


# For each driver gene, func_muts stores the set of cell lines believed to have a 'functional'
# alteration in that driver gene. For each driver gene, all_muts stores the set of cell lines
# with any alteration in that driver gene (including presumed non
# functional mutations).

func_muts = defaultdict(set)
all_muts = defaultdict(set)

mutations = pd.read_excel(
    "./genotype_input/TableS2C.xlsx", skiprows=range(0, 20))

# For oncogenes we consider recurrent missense or inframe alterations as functional alterations.
# In addition to recurrent events, for tumour suppressors we consider that all nonsense,
# frameshift and splice-site mutations are functional alterations.

for index, mutation in mutations.iterrows():
    if mutation['Gene'] in cancer_genes:
        if cancer_genes[mutation['Gene']] == 'OG':
            if mutation['Classification'] in ('missense', 'inframe'):
                if mutation['Recurrence Filter'] == 'Yes':
                    func_muts[mutation['Gene']].add(mutation['COSMIC_ID'])
            all_muts[mutation['Gene']].add(mutation['COSMIC_ID'])
        else:
            if mutation['Classification'] in ('nonsense', 'frameshift', 'ess_splice'):
                func_muts[mutation['Gene']].add(mutation['COSMIC_ID'])
            elif mutation['Recurrence Filter'] == 'Yes':
                func_muts[mutation['Gene']].add(mutation['COSMIC_ID'])
            all_muts[mutation['Gene']].add(mutation['COSMIC_ID'])

sequenced = set(mutations['COSMIC_ID'].unique())
print(len(sequenced), "cell lines")

cosmic_to_common = {}
with open("COSMIC_ID_TO_CANCERGD.txt", "rU") as f:
    for i in f:
        parts = i.strip().split()
        cosmic_to_common[int(parts[0])] = parts[1]

with open("genotype_output/GDSC1000_exome_func_muts_v1.txt", "w") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["Gene"] + [cancer_gene_names[x] for x in cancer_genes])
    for cell_line in sequenced:
        writer.writerow([cosmic_to_common[cell_line]] +
                        [int(cell_line in func_muts[x]) for x in cancer_genes])

with open("genotype_output/GDSC1000_exome_all_muts_v1.txt", "w") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["Gene"] + [cancer_gene_names[x] for x in cancer_genes])
    for cell_line in sequenced:
        writer.writerow([cosmic_to_common[cell_line]] +
                        [int(cell_line in all_muts[x]) for x in cancer_genes])

del mutations

copy_numbers = defaultdict(set)
func_cnvs = defaultdict(set)

with open("./genotype_input/Gene_level_CN.txt", "rU") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for line in reader:
        if line['gene'] in cancer_genes:
            for cell_line in line:
                if cell_line not in ('chr', 'start', 'stop', 'gene'):
                    parts = line[cell_line].split(',')
                    copies = int(parts[1])
                    if copies == 0 and cancer_genes[line['gene']] == 'TSG':
                        func_cnvs[line['gene']].add(int(cell_line))
                    elif copies > 7 and cancer_genes[line['gene']] == 'OG':
                        func_cnvs[line['gene']].add(int(cell_line))
cnv_profiled = set([int(x)
                    for x in line if x not in ('chr', 'start', 'stop', 'gene')])

with open("genotype_output/GDSC1000_cnv_func_muts_v1.txt", "w") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["Gene"] + [cancer_gene_names[x] for x in cancer_genes])
    for cell_line in cnv_profiled:
        writer.writerow([cosmic_to_common[cell_line]] +
                        [int(cell_line in func_cnvs[x]) for x in cancer_genes])

overlap = cnv_profiled.intersection(sequenced)
print(len(overlap), "cell lines copy number profiled and sequenced")

# For some oncogenes we only consider amplifications to be functional events
# while for others we only consider recurrent mutations. Could read these groups
# of data in as a configuration file.

amps = ['ERBB2', 'MYC', 'MYCN']
muts = ['KRAS', 'BRAF', 'NRAS', 'HRAS']
event_type = {}
for x in cancer_genes:
    if x in amps:
        event_type[x] = "CNV"
    elif x in muts:
        event_type[x] = "MUT"
    else:
        event_type[x] = "BOTH"


WT_VALUE = 0
MUT_VALUE = 1
CNV_VALUE = 2


def get_alteration_type(cell_line, gene, group="BOTH", mut_dict=func_muts):
    if group == 'CNV':
        if cell_line in func_cnvs[gene]:
            return CNV_VALUE
        else:
            return WT_VALUE
    elif group == 'MUT':
        if cell_line in mut_dict[gene]:
            return MUT_VALUE
        else:
            return WT_VALUE
    else:
        if cell_line in mut_dict[gene]:
            return MUT_VALUE
        elif cell_line in func_cnvs[gene]:
            return CNV_VALUE
        else:
            return WT_VALUE


def get_alteration_status(cell_line, gene, group="BOTH", mut_dict=func_muts):
    if group == 'CNV':
        if cell_line in func_cnvs[gene]:
            return 1
        else:
            return 0
    elif group == 'MUT':
        if cell_line in mut_dict[gene]:
            return 1
        else:
            return 0
    else:
        if cell_line in mut_dict[gene]:
            return 1
        elif cell_line in func_cnvs[gene]:
            return 1
        else:
            return 0

with open("genotype_output/GDSC1000_cnv_exome_func_muts_v1.txt", "w") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["Gene"] + [cancer_gene_names[x] for x in cancer_genes])
    for cell_line in overlap:
        writer.writerow([cosmic_to_common[cell_line]] + [get_alteration_status(
            cell_line, x, event_type[x], func_muts) for x in cancer_genes])

with open("genotype_output/GDSC1000_cnv_exome_all_muts_v1.txt", "w") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["Gene"] + [cancer_gene_names[x] for x in cancer_genes])
    for cell_line in overlap:
        writer.writerow([cosmic_to_common[cell_line]] + [get_alteration_status(
            cell_line, x, event_type[x], all_muts) for x in cancer_genes])

with open("genotype_output/GDSC1000_cnv_exome_func_mut_types_v1.txt", "w") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["Gene"] + [cancer_gene_names[x] for x in cancer_genes])
    for cell_line in overlap:
        writer.writerow([cosmic_to_common[cell_line]] + [get_alteration_type(
            cell_line, x, event_type[x], func_muts) for x in cancer_genes])
