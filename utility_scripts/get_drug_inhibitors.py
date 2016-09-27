"""
Retrives Drug inhibitors from dgidb.genome.wustl.edu
"""
import json
import csv
import urllib2
import time

symbols = []
symbol_to_entrez = {}
with open("../input_data/hgnc_complete_set.txt", "rU") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        if row['entrez_id'] and row['symbol']:
            symbols.append(row['symbol'])
            symbol_to_entrez[row['symbol']] = row['entrez_id']
symbols.sort()

# leaving out the clinical trials sources:  "MyCancerGenomeClinicalTrial"
# and "MyCancerGenome"
interaction_sources = ["CIViC", "CancerCommons", "ChEMBL", "ClearityFoundationBiomarkers", "ClearityFoundationClinicalTrial",
                       "DoCM", "DrugBank", "GuideToPharmacologyInteractions", "PharmGKB", "TALC", "TEND", "TdgClinicalTrial", "TTD"]

count = 0
print("Retrieving summaries for ", len(symbols), " Gene Symbols")

with open("../input_data/dgi_drug_targets.txt", "w") as output:
    output.write("%s\t%s\n" % ("EntrezID", "Inhibitors"))
    for i in range(0, len(symbols), 100):
        print i, count, symbols[i]
        subset = ",".join(symbols[i:i + 99])
        url = "http://dgidb.genome.wustl.edu/api/v1/interactions.json?" + \
            "interaction_types=inhibitor&genes=" + subset + \
            "&interaction_sources=" + ",".join(interaction_sources)
        data = json.load(urllib2.urlopen(url))
        matches = data['matchedTerms']
        for match in matches:
            inhibitors = set()
            gene = match["geneName"]
            for interaction in match['interactions']:
                drug = interaction['drugName']
                inhibitors.add(drug)
            output.write("%s\t%s\n" % (symbol_to_entrez[
                         gene], ", ".join(sorted(list(inhibitors)))))
        time.sleep(1)
