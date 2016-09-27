#!/usr/bin/env bash
wget --content-disposition https://ndownloader.figshare.com/files/3178886 -P rnai_datasets
wget --content-disposition https://ndownloader.figshare.com/files/3209786 -P rnai_datasets
wget --content-disposition https://ndownloader.figshare.com/files/3209663 -P rnai_datasets
wget --content-disposition https://github.com/neellab/bfg/blob/gh-pages/data/shrna/breast_zgarp.txt.zip?raw=true -P rnai_datasets
wget https://raw.githubusercontent.com/GeneFunctionTeam/kinase-dependency-profiling/master/data_sets/siRNA_Zscores/Intercell_v18_rc4_kinome_zp0_for_publication.txt -P rnai_datasets