"""
Creates a mapping from GDSC ID to a new CCLE style name
"""
import pandas as pd
import re
from collections import defaultdict
import csv

cell_line_details = pd.read_excel(
    'genotype_input/TableS1E.xlsx', skiprows=(0, 1, 3, 1005))

tissues = {}
names = {}
for index, cell_line in cell_line_details.iterrows():
    cosmic_id = int(cell_line['COSMIC identifier'])
    tissue = cell_line['GDSC\nTissue\ndescriptor 2']
    name = str(cell_line['Sample Name'])
    tissues[cosmic_id] = tissue
    names[cosmic_id] = name

regex = re.compile('[^a-zA-Z0-9]')


def convert_name(name):
    return regex.sub('', name).upper()


# Read and process mapping from CDSC to CCLE data

conversion_file = pd.read_excel(
    'genotype_input/TableS4E.xlsx', skiprows=range(0, 8))

mapping = {}
for index, cell_line in conversion_file.iterrows():
    mapping[int(cell_line['GDSC1000 cosmic id'])] = cell_line['CCLE name']


# Identify candidates to manually rename
for i in mapping:
    if mapping[i].split('_', 1)[0] != regex.sub('', names[i]).upper():
        print mapping[i], regex.sub('', names[i]).upper()


# Identify mapping betweend GDSC and CCLE tissue types
tissue_type_map = defaultdict(set)
for i in mapping:
    gdsc_tissue_type = tissues[i]
    ccle_tissue_type = mapping[i].split('_', 1)[1]
    tissue_type_map[gdsc_tissue_type].add(ccle_tissue_type)

for x in tissue_type_map:
    if len(tissue_type_map[x]) > 1:
        print x, tissue_type_map[x]

# Some tissue types need to be manually created / altered
tissue_type_map['rhabdomyosarcoma'] = [u'SOFT_TISSUE']
tissue_type_map['kidney'] = [u'KIDNEY']
tissue_type_map['oesophagus'] = [u'OESOPHAGUS']
tissue_type_map['head and neck'] = [u'HEADNECK']
tissue_type_map['uterus'] = [u'SOFT_TISSUE']
tissue_type_map['Lung_other'] = [u'LUNG']
tissue_type_map['skin_other'] = [u'SKIN']
tissue_type_map['hairy_cell_leukaemia'] = [
    u'HAEMATOPOIETIC_AND_LYMPHOID_TISSUE']
tissue_type_map['leukemia'] = [u'HAEMATOPOIETIC_AND_LYMPHOID_TISSUE']
tissue_type_map['cervix'] = [u'CERVIX']


groups = defaultdict(set)
for i in names:
    if tissues[i] in tissue_type_map:
        groups[list(tissue_type_map[tissues[i]])[0]].add(names[i])
    else:
        groups['OTHER'].add(names[i])
for g in groups:
    print g, len(groups[g])

print [(names[x], tissues[x]) for x in tissues if tissues[x] not in tissue_type_map]

converted = set()
converted_names = {}
for x in mapping:
    if convert_name(names[x]) != mapping[x].split('_')[0]:
        print x, convert_name(names[x]), mapping[x]
for i in names:
    an_name = convert_name(names[i])
    if tissues[i] in tissue_type_map:
        tissue = list(tissue_type_map[tissues[i]])[0]
    else:
        tissue = "OTHER"
    converted.add("%s_%s" % (an_name, tissue))
    converted_names[i] = "%s_%s" % (an_name, tissue)

with open("COSMIC_ID_TO_CANCERGD.txt", "w") as f:
    for i in converted_names:
        f.write("%s\t%s\n" % (i, converted_names[i]))
