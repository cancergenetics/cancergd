#!/usr/bin/env bash
wget http://www.cancerrxgene.org/gdsc1000/GDSC1000_WebResources//Data/suppData/TableS2C.xlsx -P ./genotype_input
wget ftp://ftp.sanger.ac.uk/pub/project/cancerrxgene/releases/release-6.0/Gene_level_CN.xlsx -P ./genotype_input
wget http://www.cancerrxgene.org/gdsc1000/GDSC1000_WebResources//Data/suppData/TableS1E.xlsx -P ./genotype_input
wget http://www.cancerrxgene.org/gdsc1000/GDSC1000_WebResources//Data/suppData/TableS4E.xlsx -P ./genotype_input
wget http://www.cancerrxgene.org/gdsc1000/GDSC1000_WebResources//Data/suppData/TableS4I.xlsx -P ./genotype_input
wget https://raw.githubusercontent.com/GeneFunctionTeam/cell_line_functional_annotation/master/resources/cancer_gene_classifications_v0.4.txt  -P ./genotype_input