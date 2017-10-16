# ================================== #
# Analysis code as described in
# "Large scale profiling of kinase
# dependencies in cancer cell lines"
# jamesc@icr.ac.uk, 3rd March 2016
# Substantially modified by 
# s.bridgett@qub.ac.uk, colm.ryan@ucd.ie
# ================================== #

# To run, use: setwd("/Users/sbridgett/Documents/DjangoApps/cancergd/R_scripts/"); source("run_intercell_analysis.R")


# Need to have preprocessCore, gplots and mixtools installed.
# Using:
# source("https://bioconductor.org/biocLite.R")
# biocLite("preprocessCore")
# install.packages("gplots")
# install.packages("mixtools")


# ----------------------------------------------------------- #
# Set output path on your computer                            #
# (the R_scripts and preprocessing are relative to this path) #
# ----------------------------------------------------------- #

# Eg: on Windows:
# setwd("C:/Users/HP/Django_projects/cancergd/R_scripts/")
# Eg: on Mac:
# setwd("/Users/colm/Desktop/django_stuff/cancergd/R_scripts/")
# setwd("/Users/sbridgett/Documents/UCD/cancergd/R_scripts/")
setwd("/Users/sbridgett/Documents/DjangoApps/cancergd/R_scripts/")


# --------------------------------------------------- #
# Select dataset to process by uncommenting that line #
# --------------------------------------------------- #

# data_set <- "Campbell"  # Campbell et al (2016) - Kinase Dependencies in Cancer Cell Lines.  Pubmed_id: "26947069"
# data_set <- "Cowley"    # Cowley et al   (2014) - Loss of function screens in 216 cancer cell lines. (Achilles project). Pubmed_id: "25984343"
# data_set <- "Marcotte"  # Marcotte et al (2016) - Breast cancer cell lines. (Colt study).  Pubmed_id: "26771497"
# data_set <- "Marcotte2012" # Marcotte et al (2012) - Breast, pancreatic, and ovarian cancer cells.  Pubmed_id: "22585861"
data_set <- "Wang_mmc3"  # Wang et al (2017) - CRISPR screens identify essential genes in 14 human AML cell lines.  Pubmed_id: "28162770"
### data_set <- "Achilles_CRISPR" # New Achilles CRISPR-Cas9 data, BUT *NOT* USED AT PRESENT.  Pubmed_id: "27260156"
# data_set <- "Hahn" # Hahn et al (2017) - Breast, pancreatic, and ovarian cancer cells.  Pubmed_id: "28753430"
# data_set <- "DRIVE_ATARiS"

# data_set <- "DRIVE_RSA"  # <-- Not using this RSA dataet.

# NOTES:
  # (1) Cowley: *Replaced by "(6) Hahn"*.  "Cowley_cancergd.txt" uses entrezid instead of ensembl ids, and "Cowley_cancergd_tissues.txt" treats PLEURA as separate tissue.
  # (2) Marcotte: All "Marcotte" data are breast tissues, so only 'by-tissue' analysis. There are several ids with just number and '_EntrezNotFound':
  # (3) Marcotte2012: The breast cell lines in this screen are a subset of those in Marcotte2016 above. so we won't store any breast specific dependencies from this screen. We should only store PANCAN, OVARY and PANCREAS specific dependencies.
  # (4) Wang_mmc3: "mmc3" is the table used from their paper (the smaller dataset in table "mmc7" isn't used here). All AML tissue so only 'by-tissue' analksis.
  # (5) Achilles_CRISPR: *Not using it at present*. kinome_file: "Achilles_v3.3.8_cancergd_with_entrezids.txt" and  tissues_file: "Achilles_v3.3.8_tissues.txt"
  # (6) Hahn: "Hahn_cancergd.txt" replaces Cowley, uses entrezid instead of ensembl ids, and "Hahn_cancergd_tissues.txt" ???treats PLEURA as separate tissue.
  # (7) DRIVE_ATARiS/DRIVE_RSA:  *Only using ATARiS data at present*. (DRIVE_RSA seems to contain all of DRIVE_ATARiS).

# ------------------------------ #
# Uncomment action(s) to perform #
# ------------------------------ #

#run_analysis <- FALSE 
run_analysis <- TRUE

#write_boxplot_files <- FALSE
write_boxplot_files <- TRUE


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

if (is.null(data_set) || data_set=='') {stop(paste("ERROR: Invalid data_set: '",data_set,"' but should be 'Campbell', 'Cowley', 'Marcotte', 'Marcotte2012', 'Wang_mm3', 'Hahn', 'DRIVE_ATARiS', or 'DRIVE_RSA'"))}

output_pancaner_results <- data_set %in% c("Campbell", "Cowley", "Achilles_CRISPR", "Marcotte2012", "Hahn", "DRIVE_ATARiS", "DRIVE_RSA" ) # No pan-cancer results for "Marcotte" (as all Breast) nor "Wand_mm3" (as all AML)

# Temporary hack:
# output_pancaner_results <- FALSE 

# Input files:
kinome_file  <- paste0("../preprocess_rnai_data/rnai_output/",data_set,"_cancergd.txt")
tissues_file <- paste0("../preprocess_rnai_data/rnai_output/",data_set,"_cancergd_tissues.txt")

# Output files:
uv_results_kinome_combmuts_file <- if (output_pancaner_results) paste0("outputs/", data_set, "_CGDs_pancan_witheffectsize_and_zdiff.txt") else "NONE"
uv_results_kinome_combmuts_bytissue_file <- paste0("outputs/", data_set, "_CGDs_bytissue_witheffectsize_and_zdiff.txt")


cat("\nVariables set to:",
	"\n  Data_set:", data_set,
    "\n  Run_analysis:", run_analysis,
    "\n  Write_boxplot_files:", write_boxplot_files,
	"\n  Input kinome_file:", kinome_file,
	"\n  Input tissues_file:",tissues_file,
	"\n  Pan-cancer results file:", uv_results_kinome_combmuts_file,
	"\n  By-tissue results file:", uv_results_kinome_combmuts_bytissue_file,
	"\n\n")

# ------------------------------ #
# Source the Intercell functions #
# ------------------------------ #

source("../R_scripts/Intercell_analysis_functions.R");  # source_file_info <- file.info(source_script); 


# ---------------- #
# Read in the data
# ---------------- #
cat("Reading input data ...\n")
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

if (run_analysis) {
  if (output_pancaner_results) {
	# Driver gene mutations in combined histotypes - No Pan-cancer for Colt as it is only Breast cancer cell lines.
    cat("Starting Pan-cancer univariate tests ...\n")
  
    # cat("Number to test:",length(colnames(kinome_combmuts$func_muts)))
  
    # Writing results directly to file (rather than appending each result to a data frame, which becomes slow with Cowley and  data):
    fileConn<-file(open="w", uv_results_kinome_combmuts_file)
	num_results <- run_univariate_tests(
		zscores=kinome_combmuts$rnai,
		mutations=kinome_combmuts$func_muts,
		all_variants=kinome_combmuts$all_muts,
		sensitivity_thresholds=kinome_combmuts$rnai_iqr_thresholds,
		min_size = 5,
		fileConn=fileConn,
		writeheader=TRUE,
		tissue=NULL
		)
	close(fileConn)
    cat("\n",num_results,"pan-cancer results\n\n")
  }


  # Driver gene mutations in separate histotypes
  cat("Starting by-tissue univariate tests ...\n")

  # Writing results directly to file:
  fileConn<-file(open="w", uv_results_kinome_combmuts_bytissue_file)
  num_results <- run_univariate_test_bytissue(
    x=kinome_combmuts,
	fileConn=fileConn,
	writeheader=TRUE
	)
  close(fileConn)
  cat("\n",num_results,"by-tissue results\n\n")
  
  }  # end of: if (run_analysis) ...


# ------------------------------------------------------------ #
# Reload results and add the boxplot data to the result files  #
# ------------------------------------------------------------ #

if (write_boxplot_files) {

  if (output_pancaner_results) {

    cat("Reloading pan-cancer results from file ...\n")
    uv_results_kinome_combmuts <- read.table(
		file=uv_results_kinome_combmuts_file,
		header=TRUE,
		sep="\t",
		stringsAsFactors=FALSE
		)

    cat("Writing pan-cancer boxplot data files ...\n")
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
		writeheader=TRUE
		)
	close(fileConn) # caller should close the fileConn	
	# To conserve memory, remove these results from memory: 
	rm(uv_results_kinome_combmuts)
    gc()
    }


  cat("Reloading by-tissue results from file ...\n")
  uv_results_kinome_combmuts_bytissue <- read.table(
	file=uv_results_kinome_combmuts_bytissue_file,
	header=TRUE,
	sep="\t",
	stringsAsFactors=FALSE
	)
	
  # Write the combmuts boxplot data for separate histotypes
  # select associations where wilcox.p <= 0.05 and CLES > =0.65
  cat("Writing by-tissue boxplot data files ...\n")
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
		writeheader=write_header
		)
	write_header <- FALSE # As only write the header line for first call of the above write_boxplot_data
    }
  close(fileConn) # caller should close the fileConn

} # end of: if (write_boxplot_files) ...


cat("\nFinished",data_set,"\n")
