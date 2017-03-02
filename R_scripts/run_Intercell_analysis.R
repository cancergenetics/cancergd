# ================================== #
# Analysis code as described in
# "Large scale profiling of kinase
# dependencies in cancer cell lines"
# jamesc@icr.ac.uk, 3rd March 2016
# Substantially modified by 
# s.bridgett@qub.ac.uk, colm.ryan@ucd.ie
# ================================== #

# Need to have preprocessCore, gplots and mixtools installed.

# --------------------------------------------------- #
# Select dataset to process by uncommenting that line #
# --------------------------------------------------- #

# data_set <- "Campbell"  # Campbell et al (2016) - Kinase Dependencies in Cancer Cell Lines.
# data_set <- "Achilles"  # Cowley et al   (2014) - Loss of function screens in 216 cancer cell lines.
# data_set <- "Colt"      # Marcotte et al (2016) - Breast cancer cell lines.
# data_set <- "Achilles_CRISPR" # New Achilles CRISPR-Cas9 data
data_set <- "Wang"  # Wang et al (2017) - CRISPR screens identify essential genes in 14 human AML cell lines.

# ----------------------------------------------------------- #
# Set output path on your computer                            #
# (the R_scripts and preprocessing are relative to this path) #
# ----------------------------------------------------------- #

# Eg: on Windows:
#setwd("C:/Users/HP/Django_projects/cgdd/postprocessing_R_results/")
# Eg: on Mac:
# setwd("/Users/colm/Desktop/django_stuff/cancergd/R_scripts/")
setwd("/Users/sbridgett/Documents/UCD/cancergd/R_scripts/")

# ------------------------------ #
# Common inputs for all datasets #
# ------------------------------ #

# Cell-line genotype files:
combmuts_func_file <- "../preprocess_genotype_data/genotype_output/GDSC1000_cnv_exome_func_muts_v1.txt" # (indicates if there is a functional mutation)
combmuts_all_file <- "../preprocess_genotype_data/genotype_output/GDSC1000_cnv_exome_all_muts_v1.txt"  # (indicates if there is any mutation)
combmuts_classes_file <- "../preprocess_genotype_data/genotype_output/GDSC1000_cnv_exome_func_mut_types_v1.txt" # (indicates mutation types: 1 or 2)


# ----------------------------------------------------- #
# Specify the Analysis specific input and results files #
# ------------------------------------------------------#

if (data_set == "Campbell") {
  pubmed_id <- "26947069" # Campbell(2016)  
  kinome_file <- "../preprocess_rnai_data/rnai_output/Campbell_cancergd.txt"
  tissues_file <- "../preprocess_rnai_data/rnai_output/Campbell_cancergd_tissues.txt"
  
  uv_results_kinome_combmuts_file <- "outputs/Campbell_CGDs_pancan_witheffectsize_and_zdiff.txt"
  uv_results_kinome_combmuts_bytissue_file <- "outputs/Campbell_CGDs_bytissue_witheffectsize_and_zdiff.txt"

} else if (data_set == "Achilles") {
  pubmed_id <- "25984343" # Cowley(2014) for Achilles  
  kinome_file <- "../preprocess_rnai_data/rnai_output/Cowley_cancergd.txt" # Uses entrezid instead of ensembl ids.
  tissues_file <- "../preprocess_rnai_data/rnai_output/Cowley_cancergd_tissues.txt" # Treats PLEURA as separate tissue.

  uv_results_kinome_combmuts_file <- "outputs/Cowley_CGDs_pancan_witheffectsize_and_zdiff.txt"
  uv_results_kinome_combmuts_bytissue_file <- "outputs/Cowley_CGDs_bytissue_witheffectsize_and_zdiff.txt"

} else if (data_set == "Colt") {
  # NOTE: There are several ids with just number and '_EntrezNotFound':
  pubmed_id <- "26771497" # Marcotte(2016) for Colt study
  kinome_file <- "../preprocess_rnai_data/rnai_output/Marcotte_cancergd.txt"
  tissues_file <- "../preprocess_rnai_data/rnai_output/Marcotte_cancergd_tissues.txt"   # All Colt data are breast tissues.

  # In Colt study only breast tissue - so only by-tissue anaylsis, no Pan-cancer:
  uv_results_kinome_combmuts_file <- "NONE"
  uv_results_kinome_combmuts_bytissue_file <- "outputs/Marcotte_CGDs_bytissue_witheffectsize_and_zdiff.txt"
  
} else if (data_set == "Achilles_CRISPR") {
  print("Running Achilles_CRISPR ...")
  pubmed_id <- "27260156" # Achilles CRISPR(2016)  
  kinome_file <- "../preprocess_genotype_data/rnai_datasets/Achilles_v3.3.8_cancergd_with_entrezids.txt"
  tissues_file <- "../preprocess_genotype_data/rnai_datasets/Achilles_v3.3.8_tissues.txt"
  
  uv_results_kinome_combmuts_file <- "outputs/univariate_results_Achilles_CRISPR_for36drivers_pancan_kinome_combmuts_witheffectsize_and_zdiff.txt"
  uv_results_kinome_combmuts_bytissue_file <- "outputs/univariate_results_Achilles_CRISPR_for36drivers_bytissue_kinome_combmuts_witheffectsize_and_zdiff.txt"  

} else if (data_set == "Wang") {
  #table="mmc7"
  table="mmc3"

  print(paste("Running Wang",table," ..."))
  pubmed_id <- "28162770" # Wang(2017)
    
  kinome_file  <- paste("../preprocess_rnai_data/rnai_output/Wang_",table,"_cancergd.txt", sep="")
  tissues_file <- paste("../preprocess_rnai_data/rnai_output/Wang_",table,"_cancergd_tissues.txt", sep="")
  
#  uv_results_kinome_combmuts_file <- paste("outputs/Wang_",table,"_for36drivers_pancan_kinome_combmuts_witheffectsize_and_zdiff.txt", sep="")
#  uv_results_kinome_combmuts_bytissue_file <- paste("outputs/Wang_",table,"_for36drivers_bytissue_kinome_combmuts_witheffectsize_and_zdiff.txt", sep="")

# Wang is only one tissue type:
#  uv_results_kinome_combmuts_file <- paste("outputs/Wang_",table,"_CGDs_pancan__witheffectsize_and_zdiff.txt", sep="")
  uv_results_kinome_combmuts_bytissue_file <- paste("outputs/Wang_",table,"_CGDs_bytissue_witheffectsize_and_zdiff.txt", sep="")
  
} else {
  stop(paste("ERROR: Invalid data_set: '",data_set,"' but should be 'Campbell', 'Achilles', 'Colt' or 'Wang'"))
}

print(paste("Variables set to:\ndata_set:",data_set,"\nkinome_file:",kinome_file,"\ntissues_file:",tissues_file,"\n"))


# ------------------------------ #
# Source the Intercell functions #
# ------------------------------ #

# ******* Always need to set the 'data_set' value before sourcing the Intercell_functions, as it is used to set the tissue lists and plot colours.

source_script <- "../R_scripts/Intercell_analysis_functions.R";    # source_file_info <- file.info(source_script); 
source(source_script); 

# ---------------- #
# Read in the data
# ---------------- #

kinome_combmuts <- read_rnai_mutations(
	rnai_file=kinome_file,
	func_muts_file=combmuts_func_file,
	all_muts_file=combmuts_all_file,
	mut_classes_file=combmuts_classes_file,
	tissues_file=tissues_file
	)

# -------------------------------- #
# Run the set of hypothesis tests
# on the kinome z-score data sets
# -------------------------------- #

if (data_set != "Colt" && data_set != "Wang") {
	# Driver gene mutations in combined histotypes - No Pan-cancer for Colt as it is only Breast cancer cell lines.
	uv_results_kinome_combmuts <- run_univariate_tests(
		zscores=kinome_combmuts$rnai,
		mutations=kinome_combmuts$func_muts,
		all_variants=kinome_combmuts$all_muts,
		sensitivity_thresholds=kinome_combmuts$rnai_iqr_thresholds,
		min_size = 5
		)
	write.table(
		uv_results_kinome_combmuts,
		file=uv_results_kinome_combmuts_file,
		sep="\t",
		quote=FALSE,
		row.names=FALSE
		)
}

# Driver gene mutations in separate histotypes
uv_results_kinome_combmuts_bytissue <- run_univariate_test_bytissue(kinome_combmuts)
write.table(
	uv_results_kinome_combmuts_bytissue,
	file=uv_results_kinome_combmuts_bytissue_file,
	sep="\t",
	quote=FALSE,
	row.names=FALSE
)


# ------------------------------ #
# (Re-)load in the results files
# ------------------------------ #

if (data_set != "Colt" && data_set != "Wang") {
	uv_results_kinome_combmuts <- read.table(
		file=uv_results_kinome_combmuts_file,
		header=TRUE,
		sep="\t",
		stringsAsFactors=FALSE
		)
}		

uv_results_kinome_combmuts_bytissue <- read.table(
	file=uv_results_kinome_combmuts_bytissue_file,
	header=TRUE,
	sep="\t",
	stringsAsFactors=FALSE
	)

# ----------------------------------------- #
# Add the boxplot data to the result files  #
# ----------------------------------------- #

if (data_set != "Colt" && data_set != "Wang") {
	# Add the combmuts boxplot data, which will be coloured by tissue
	# select associations where wilcox.p <= 0.05 and CLES > =0.65

	fileConn<-file(open="w", paste0( sub("\\.txt$","",uv_results_kinome_combmuts_file), "_and_boxplotdata_mutantstate.txt") ) # Need "\\." to correctly escape the dot in regexp in R
	write_box_dot_plot_data(
		results=as.data.frame(
			uv_results_kinome_combmuts[which(
				uv_results_kinome_combmuts[,"wilcox.p"] <= 0.05 &
				uv_results_kinome_combmuts[,"CLES"] >= 0.65 # SJB Added this effect_size test
				),]
			),
		zscores=kinome_combmuts$rnai,
		mutation.classes=kinome_combmuts$mut_classes, # SJB - I think this is the mutation types.
		mutations=kinome_combmuts$func_muts,
		exclusions=kinome_combmuts$all_muts,
		tissues=kinome_combmuts$tissues,
		fileConn = fileConn,
		writeheader=TRUE,
		tissue_actual_names=legend_actual_tissues
		)
	close(fileConn) # caller should close the fileConn	
}

	
# Write the combmuts boxplot data for separate histotypes
# select associations where wilcox.p <= 0.05 and CLES > =0.65

fileConn<-file(open="w", 
paste0( sub("\\.txt$","",uv_results_kinome_combmuts_bytissue_file), "_and_boxplotdata_mutantstate.txt") ) # Output file. Needs "w" otherwise cat(...) overwrites previous cat()'s rather than appending. To open and append to existing file use "a"
tissues <- levels(as.factor(uv_results_kinome_combmuts_bytissue$tissue))
write_header <- TRUE
for(this_tissue in tissues){
	rows_to_plot <- which(
		kinome_combmuts$tissues[,this_tissue] == 1
		)
	write_box_dot_plot_data(
		results=as.data.frame(
			uv_results_kinome_combmuts_bytissue[which(
				uv_results_kinome_combmuts_bytissue[,"wilcox.p"] < 0.05 &
				uv_results_kinome_combmuts_bytissue[,"CLES"] >= 0.65 & # SJB Added this effect_size test
				uv_results_kinome_combmuts_bytissue[,"tissue"] == this_tissue
				),]
			),
		zscores=kinome_combmuts$rnai[rows_to_plot,],
		mutation.classes=kinome_combmuts$mut_classes[rows_to_plot,],
		mutations=kinome_combmuts$func_muts[rows_to_plot,],
		exclusions=kinome_combmuts$all_muts[rows_to_plot,],
		tissues=kinome_combmuts$tissues[rows_to_plot,], 
		fileConn=fileConn,
		writeheader=write_header,
		tissue_actual_names=legend_actual_tissues,
		)
	write_header <- FALSE # As only write the header line for first call of the above write_boxplot_data
}
close(fileConn) # caller should close the fileConn