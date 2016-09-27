"""
This is a utility script to download ENTREZ summaries using EUTILS.
"""
import json
import csv
import urllib2
import time

entrez_ids = []
with open("../input_data/hgnc_complete_set.txt", "rU") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        if row['entrez_id'] and row['symbol']:
            entrez_ids.append(row['entrez_id'])
entrez_ids.sort()

count = 0
print("Retrieving summaries for ", len(entrez_ids), " ENTREZ IDs")

with open("../input_data/entrez_summaries.txt", "w") as output:
    output.write("%s\t%s\n" % ("EntrezID", "Summary"))
    for i in range(0, len(entrez_ids), 500):
        print i, count, entrez_ids[i]
        subset = ",".join(entrez_ids[i:i + 499])
        url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id=' + \
            subset + '&retmode=json'
        data = json.load(urllib2.urlopen(url))
        for res in data["result"]:
            if "summary" in data["result"][res] and data["result"][res]["summary"] != "":
                output.write("%s\t%s\n" %
                             (res, data["result"][res]["summary"]))
                count += 1
        time.sleep(2)
