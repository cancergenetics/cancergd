# Extracts the dependencies that are found in more than one study.
# Input: "all_dependencies.csv.gz"   Output: "multihit_dependencies.csv"

import csv
import gzip
from collections import defaultdict

print("Extracting multi-hit dependencies (ie. dependencies found in more than one study) ...")

cgds = defaultdict(set) # a dictionary mapping cgds to the studies they were observed in
interacting = 0

with gzip.open("./all_dependencies.csv.gz","rt", encoding='utf-8') as fin :
    # First we record all the dependencies seen in CancerGD:
    reader = csv.DictReader(fin, delimiter = ",") 
    for r in reader :
        cgd = (r['driver_genename'], r['target_genename'], r['tissue'])
        cgds[cgd].add(r['study'])


	# Then we output all of the dependencies seen in at least 2 studies
# with gzip.open("./all_dependencies.csv.gz","rt", encoding='utf-8') as fin :
    fin.seek(0)     # can rewind to beginning instead of reopening the file.
    reader = csv.DictReader(fin, delimiter = ",")
    with open("./multihit_dependencies.csv", "w") as fout :
        fieldnames = ['driver_genename', 'driver_entrez', 'target_genename', 
                      'target_entrez', 'interaction', 'tissue', 'driver_ensembl', 
                      'target_ensembl', 'target_ensembl_protein', 'inhibitors', 
                      'studies'] 
        writer = csv.DictWriter(fout, delimiter = ",", fieldnames=fieldnames)
        writer.writeheader()
        written = set()
        for r in reader :
            cgd = (r['driver_genename'], r['target_genename'], r['tissue'])
            if len(cgds[cgd]) > 1 and cgd not in written:
                line = {}
                for n in fieldnames[0:-1] :
                    line[n] = r[n]
                line["studies"] = ";".join(sorted(cgds[cgd]))
                writer.writerow(line)
                written.add(cgd)
