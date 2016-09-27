'''
Creates a mapping from Campbell style IDs (Symbol_ENSGXXX) to that used by CancerGD
(Symbol_ENTREZ). Also updates gene names to current symbols from HGNC
'''
import csv

entrez_to_common_hgnc = {}
entrez_to_ensembl_hgnc = {}
ensembl_to_entrez_hgnc = {}
with open("../input_data/hgnc_complete_set.txt", "rU") as f:
    reader = csv.DictReader(f, delimiter="\t")
    status = set()
    for i in reader:
        entrez_to_common_hgnc[i['entrez_id']] = i['symbol']
        if 'ENSG' in i['ensembl_gene_id']:
            entrez_to_ensembl_hgnc[i['entrez_id']] = i['ensembl_gene_id']
            ensembl_to_entrez_hgnc[i['ensembl_gene_id']] = i['entrez_id']

with open("./rnai_input/Intercell_v18_rc4_kinome_zp0_for_publication.txt", "rU") as f:
    header = f.readline().strip().split("\t")
    genes = set()
    for gene in header[1:]:
        genes.add(gene)

manual_map = {}
with open("./rnai_input/Campbell_manual_entrez.txt", "rU") as f:
    for line in f:
        parts = line.strip().split("\t")
        manual_map[parts[0]] = parts[1]

entrez_to_common_hgnc['84451'] = 'MLK4'
entrez_to_common_hgnc['51776'] = 'ZAK'
entrez_to_common_hgnc['157285'] = 'SGK223'
entrez_to_common_hgnc['124923'] = 'SGK494'

translation = {}
for x in genes:
    gene = x.split('_')[1]
    if gene in ensembl_to_entrez_hgnc:
        translation[x] = "%s_%s" % (entrez_to_common_hgnc[ensembl_to_entrez_hgnc[
                                    gene]], ensembl_to_entrez_hgnc[gene])
    else:
        if manual_map[gene] in entrez_to_common_hgnc:
            translation[x] = "%s_%s" % (
                entrez_to_common_hgnc[manual_map[gene]], manual_map[gene])

with open("./rnai_input/Campbell_gene_update.txt", "w") as f:
    for i in translation:
        f.write("%s\t%s\n" % (i, translation[i]))
