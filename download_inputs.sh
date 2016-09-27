#!/usr/bin/env bash
wget ftp://ftp.ebi.ac.uk/pub/databases/genenames/new/tsv/hgnc_complete_set.txt -P ./input_data
wget http://string-db.org/mapping_files/entrez_mappings/entrez_gene_id.vs.string.v10.28042015.tsv -P ./input_data
wget http://string-db.org/download/protein.aliases.v10/9606.protein.aliases.v10.txt.gz -P ./input_data
wget http://string-db.org/download/protein.links.v10/9606.protein.links.v10.txt.gz -P ./input_data
