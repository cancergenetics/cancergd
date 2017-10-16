#!/usr/bin/env bash

wget ftp://ftp.ebi.ac.uk/pub/databases/genenames/new/tsv/hgnc_complete_set.txt -P ./input_data
wget http://string-db.org/mapping_files/entrez_mappings/entrez_gene_id.vs.string.v10.28042015.tsv -P ./input_data

# wget http://string-db.org/download/protein.aliases.v10/9606.protein.aliases.v10.txt.gz -P ./input_data
# wget http://string-db.org/download/protein.links.v10/9606.protein.links.v10.txt.gz -P ./input_data

# Now changed to latest v10.5: 
wget http://string-db.org/download/protein.aliases.v10.5/9606.protein.aliases.v10.5.txt.gz -P ./input_data 
wget http://string-db.org/download/protein.links.v10.5/9606.protein.links.v10.5.txt.gz -P ./input_data

# wget http://string-db.org/download/protein.actions.v10.5/9606.protein.actions.v10.5.txt.gz

echo -e "\n*** Please check that the file sizes below match the downloaded sizes above, as if you run out of disk space then 'wget' can truncate the files without giving an error message.\n"

ls -l input_data/hgnc_complete_set.txt
ls -l input_data/entrez_gene_id.vs.string.v10.28042015.tsv

# ls -l input_data/9606.protein.aliases.v10.txt.gz
# ls -l input_data/9606.protein.links.v10.txt.gz

ls -l input_data/9606.protein.aliases.v10.5.txt.gz
ls -l input_data/9606.protein.links.v10.5.txt.gz 
