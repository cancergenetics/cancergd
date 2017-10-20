"""
Retrives Drug inhibitors from dgidb.genome.wustl.edu
"""
import json
import csv
import urllib.request  # in python2 was: import urllib2
import time

symbols = []
symbol_to_entrez = {}
with open("../input_data/hgnc_complete_set.txt", "rU") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        if row['entrez_id'] and row['symbol']:
            # In hgnc_complete_set.txt is "C10orf10", but this is returned as upper case "C10ORF10" by dgidb, so just force uppercase:
 # BUT another problem is that "FDX1L" returned by DGIdb for FDX2, as "FDX1L" (ferredoxin 1-like) is an alias or previous name for "FDX2" in the hgnc_complete_set.txt file.  
            ucsymbol = row['symbol'].upper()
            symbols.append(ucsymbol)
            symbol_to_entrez[ucsymbol] = row['entrez_id']
symbols.sort()

# leaving out the clinical trials sources:  "MyCancerGenomeClinicalTrial"
# and "MyCancerGenome"
interaction_sources = ["CIViC", "CancerCommons", "ChEMBL", "ClearityFoundationBiomarkers", "ClearityFoundationClinicalTrial",
                       "DoCM", "DrugBank", "GuideToPharmacologyInteractions", "PharmGKB", "TALC", "TEND", "TdgClinicalTrial", "TTD"]

#count = 0
print("Retrieving summaries for ", len(symbols), " Gene Symbols")

with open("../input_data/dgi_drug_targets.txt", "w") as output:
    output.write("%s\t%s\n" % ("EntrezID", "Inhibitors"))
    for i in range(0, len(symbols), 100):
        print( i, symbols[i] )
        subset = ",".join(symbols[i:i + 99])
#       url = "http://dgidb.genome.wustl.edu/api/v1/interactions.json?" + \
        # DGIdb has updated to api v2:
        url = "http://dgidb.org/api/v2/interactions.json?" + \
            "interaction_types=inhibitor&genes=" + subset + \
            "&interaction_sources=" + ",".join(interaction_sources)
        # print("URL: '%s'" %(url))
        data = json.load(urllib.request.urlopen(url))    # in python2 was: urllib2.urlopen(url)
        # print("Got data for %s" %(", ".join(symbols)))
        matches = data['matchedTerms']
        for match in matches:
            inhibitors = set()
            gene = match["geneName"]
            for interaction in match['interactions']:
                drug = interaction['drugName']
                inhibitors.add(drug)
            output.write("%s\t%s\n" % (symbol_to_entrez[
                         gene], ", ".join(sorted(list(inhibitors)))))
# In hgnc_complete_set.txt is "C10orf10", but this is returned as upper case "C10ORF10" by dgidb
        time.sleep(1)

