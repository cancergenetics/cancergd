Cell line naming :

We follow the naming convention established by the Cancer Cell Line Encyclopedia. The CCLE naming convention is the cell line name (containing only numbers and upper case letters) followed by an underscore, followed by the tissue/primary site in upper case. Where possible we use the same tissue types as the CCLE, in a small number of cases where a tissue was absent from the CCLE (e.g. CERVIX) we have created a new tissue type. Having the tissue type in the cell line name allows us to filter the boxplots (e.g. to show the RNAi sensitivities for cell lines from a specific tissue) in the browser without having to perform additional datbase queries. In instances where the same cell line is featured in two datasets but there is a naming disagreement (e.g. H1299_LUNG in Campbell et al is NCIH1299_LUNG in our genotype set) we manually rename the RNAi dataset to match the genotype data.

Processing exome data :

For oncogenes we consider recurrent missense or recurrent in frame deletions/insertions to be activating events. Recurrence here is taken as at least 3 previous mutations in the COSMIC database. In addition to recurrent missense or indel events, for tumour suppressors we consider that all nonsense, frameshift and splice-site mutations are loss-of-function events. 

Processing copy number data :

For copy number analysis we use the gene level copy number scores from COSMIC (which are derived from PICNIC analysis of Affymetrix SNP6.0 array data). An oncogene is considered amplified if the entire coding sequence has 8 or more copies. A tumour suppressor is considered deleted if any part of the coding sequence has a copy number of 0.

Merging copy number and exome data :

For tumour suppressors we consider a functional alteration to be either a deletion (derived from copy number profiles) or a presumed loss-of-function mutation (derived from exome data). For most oncogenes we consider a functional alteration to be either an amplification or a recurrent mutation. For a small number of oncogenes (ERBB2,MYC,MYCN) we only consider amplifications as functional events, while for another group (KRAS,BRAF,NRAS,HRAS) we only consider recurrent mutations.

