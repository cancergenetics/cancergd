# ====================================== #
# Analysis functions used for univariate
# analyses in the Intercell II work
# jamesc@icr.ac.uk, 11th March 2014
# ====================================== #
require("preprocessCore")
require(gplots)
require(mixtools)

if (data_set == "Campbell") {	
  legend_pretty_tissues = c(
    "Bone",
    "Breast",
    "Lung",
    "Head & Neck",
    "Pancreas",
    "Cervix",
    "Ovary",
    "Esophagus",
    "Endometrium",
    "CNS"
  )
  legend_actual_tissues = c(
    "BONE",
    "BREAST",
    "LUNG",
    "HEADNECK",
    "PANCREAS",
    "CERVIX",
    "OVARY",
    "OESOPHAGUS",
    "ENDOMETRIUM",
    "CENTRAL_NERVOUS_SYSTEM"
  )
  legend_col=c(
    "yellow",
    "deeppink",
    "darkgrey",
    "firebrick4",
    "purple",
    "blue",
    "cadetblue",
    "green",
    "orange",	
    "darkgoldenrod4"
  )
  
} else if (data_set == "Achilles") {
  legend_pretty_tissues = c(
    "Bone",
    "Breast",
    "Lung",
    "Pancreas",
    "Ovary",
    "Esophagus",
    "Endometrium",
    "CNS",
    "Blood & Lymph",
    "Large Intestine", # Updated from "Intestine" Aug 2016,
    "Kidney",
    "Liver",
    "Pleura", # Added Aug 2016	
    "Prostate",
    "Skin",
    "Soft tissue",
    "Stomach",
    "Urinary tract",
    "Other"	  # Added Aug 2016	
  )	
  legend_actual_tissues = c(
    "BONE",
    "BREAST",
    "LUNG",
    "PANCREAS",
    "OVARY",
    "OESOPHAGUS",
    "ENDOMETRIUM",
    "CENTRAL_NERVOUS_SYSTEM",
    "HAEMATOPOIETIC_AND_LYMPHOID_TISSUE",
    "LARGE_INTESTINE", # Updated from "INTESTINE" Aug 2016
    "KIDNEY",
    "LIVER",
    "PLEURA", # Added Aug 2016
    "PROSTATE",
    "SKIN",
    "SOFT_TISSUE",
    "STOMACH",
    "URINARY_TRACT",
    "OTHER"	  # Added Aug 2016
  )	
  legend_col=c(
    "yellow",    # Bone
    "deeppink",  # Breast
    "darkgrey",  # Lung
    "purple",    # Pancreas
    "cadetblue", # Ovary
    "green",     # Oesophagus
    "orange",    # Endometrium
    "darkgoldenrod4", # CNS
    "darkred",   # Blood & Lymph
    "saddlebrown", # Large Intestine
    "indianred",
    "slategray",
    "slategray",  # **** Still to fix this colour for: "Pleura", # Added Aug 2016	
    "turquoise",  # Prostate
    "peachpuff",  # Skin
    "lightgrey",  # Soft tissue
    "black",      # Stomach
    "yellowgreen",
    "slategray" # **** Still to fix colour for: "Other"	  # Added Aug 2016	    
  )


    
  
  
} else if(data_set == "Colt") {	  # Only Breast, but dummy BONE added in tissues file for plotting
  legend_pretty_tissues = c(
    "Breast"
  )
  legend_actual_tissues = c(
    "BREAST"
  )
  legend_col=c(
    "deeppink"
  )
  
} else if(data_set == "Achilles_CRISPR") {
  legend_pretty_tissues = c(
    "Bone",
    "Breast",
    "Blood & Lymph",
    "Large Intestine",
    "Lung",
    "Ovary",
    "Pancreas",
    "Prostate",
    "Skin",
    "Soft tissue"  
  )
  legend_actual_tissues = c(
    "BONE",
    "BREAST",
    "HAEMATOPOIETIC_AND_LYMPHOID_TISSUE",
    "LARGE_INTESTINE",
    "LUNG",
    "OVARY",
    "PANCREAS",
    "PROSTATE",
    "SKIN",
    "SOFT_TISSUE"
  )
  legend_col=c(
    "yellow",   # Bone
    "deeppink", # Breast 
    "darkred",  # Blood & Lymph
    "saddlebrown", # Large Intestine
    "darkgrey", # Lung
    "cadetblue", # Ovary	
    "purple",   # Pancreas
    "turquoise", # Prostate
    "peachpuff",  # Skin
    "lightgrey"  # Soft tissue
  )

} else if(data_set == "Wang") {	  # Only Breast, but dummy BONE added in tissues file for plotting
  legend_pretty_tissues = c(
    "Blood & Lymph",
    "Stomach"
  )
  legend_actual_tissues = c(
    "HAEMATOPOIETIC_AND_LYMPHOID_TISSUE",
    "STOMACH"
  )
  legend_col=c(
    "darkred",   # Blood & Lymph
    "black"      # Stomach    
  )
  
} else {
  stop(paste("ERROR: Invalid data_set: '",data_set,"' but should be 'Campbell', 'Achilles', 'Colt' or 'Wang'"))
}

names(legend_col) <- legend_actual_tissues

# List of driver genes we care about
cancergd_drivers_n5 <- c(
  "CCND1_595_ENSG00000110092",
  "CDKN2A_1029_ENSG00000147889",
  "EGFR_1956_ENSG00000146648",
  "ERBB2_2064_ENSG00000141736",
  "GNAS_2778_ENSG00000087460",
  "KRAS_3845_ENSG00000133703",
  "SMAD4_4089_ENSG00000141646",
  "MDM2_4193_ENSG00000135679",
  "MYC_4609_ENSG00000136997",
  "NF1_4763_ENSG00000196712",
  "NRAS_4893_ENSG00000213281",
  "PIK3CA_5290_ENSG00000121879",
  "PTEN_5728_ENSG00000171862",
  "RB1_5925_ENSG00000139687",
  "MAP2K4_6416_ENSG00000065559",
  "SMARCA4_6597_ENSG00000127616",
  "STK11_6794_ENSG00000118046",
  "TP53_7157_ENSG00000141510",
  "ARID1A_8289_ENSG00000117713",
  "FBXW7_55294_ENSG00000109670",
  "BRAF_673_ENSG00000157764",    # Added BRAF on 14 April 2016 for future runs
  "CDH1_999_ENSG00000039068",    # Added CDH1 on 15 April 2016 for future runs
  "NCOR1_9611_ENSG00000141027",  # Added NCOR1 on 15 Aug 2016 for future runs
  "RNF43_54894_ENSG00000108375", # Added NCOR1 on 15 Aug 2016 for future runs 
  "BCOR_54880_ENSG00000183337",
  "EP300_2033_ENSG00000100393",
  "CDKN2C_1031_ENSG00000123080",
  "PIK3R1_5295_ENSG00000145675", 
  "KDM6A_7403_ENSG00000147050",
  "ASXL1_171023_ENSG00000171456",
  "MSH2_4436_ENSG00000095002",
  "ARID1B_57492_ENSG00000049618",
  "APC_324_ENSG00000134982",
  "CTNNB1_1499_ENSG00000168036",
  "BRCA2_675_ENSG00000139618",
  "MSH6_2956_ENSG00000116062"    # Added NCOR1 on 15 Aug 2016 for future runs 
)


# Function to read in data, find the intersecting
# rownames and return a list of dataframes with 
# the common cell lines.
# Added 10th Dec 2014 to stop the data preprocessing
# getting out of hand.
read_rnai_mutations <- function(
  rnai_file,
  func_muts_file,
  all_muts_file,
  mut_classes_file,
  tissues_file
){
  
  
  rnai <- read.table(
    file=rnai_file,
    header=TRUE,
    sep="\t",
    row.names=1
  )
  
  rnai_qn <- t(normalize.quantiles(t(rnai)))
  rownames(rnai_qn) <- rownames(rnai)
  colnames(rnai_qn) <- colnames(rnai)
  
  func_muts <- read.table(
    file=func_muts_file,
    sep="\t",
    header=TRUE,
    row.names=1
  )
  
  all_muts <- read.table(
    file=all_muts_file,
    header=TRUE,
    sep="\t",
    row.names=1
  )
  
  mut_classes <- read.table(
    file=mut_classes_file,
    header=TRUE,
    sep="\t",
    row.names=1
  )
  
  tissues <- read.table(
    file=tissues_file,
    header=TRUE,
    sep="\t",
    row.names=1
  )
  
  common_celllines <- intersect(
    rownames(rnai),
    rownames(func_muts)
  )
  
  common_celllines <- intersect(
    common_celllines,
    rownames(tissues)
  )
  
  
  
  i <- NULL
  row.index <- NULL
  rnai_muts_cmn <- NULL
  rnai_qn_muts_cmn <- NULL
  func_muts_rnai_cmn <- NULL
  all_muts_rnai_cmn <- NULL
  mut_classes_rnai_cmn <- NULL
  tissues_rnai_cmn <- NULL
  for(i in seq(1:length(common_celllines))){
    # rnai subset
    row.index <- NULL
    row.index <- which(rownames(rnai) == common_celllines[i])
    rnai_muts_cmn <- rbind(
      rnai_muts_cmn,
      rnai[row.index,]
    )
    # rnai_qn subset
    row.index <- NULL
    row.index <- which(rownames(rnai_qn) == common_celllines[i])
    rnai_qn_muts_cmn <- rbind(
      rnai_qn_muts_cmn,
      rnai_qn[row.index,]
    )
    # func_muts subset
    row.index <- NULL
    row.index <- which(rownames(func_muts) == common_celllines[i])
    func_muts_rnai_cmn <- rbind(
      func_muts_rnai_cmn,
      func_muts[row.index,]
    )
    # all_muts subset
    row.index <- NULL
    row.index <- which(rownames(all_muts) == common_celllines[i])
    all_muts_rnai_cmn <- rbind(
      all_muts_rnai_cmn,
      all_muts[row.index,]
    )
    # mut_classes subset
    row.index <- NULL
    row.index <- which(rownames(mut_classes) == common_celllines[i])
    mut_classes_rnai_cmn <- rbind(
      mut_classes_rnai_cmn,
      mut_classes[row.index,]
    )
    # tissues_rnai subset
    row.index <- NULL
    row.index <- which(rownames(tissues) == common_celllines[i])
    tissues_rnai_cmn <- rbind(
      tissues_rnai_cmn,
      tissues[row.index,]
    )
  }
  rownames(rnai_muts_cmn) <- common_celllines
  rownames(func_muts_rnai_cmn) <- common_celllines
  rownames(all_muts_rnai_cmn) <- common_celllines
  rownames(mut_classes_rnai_cmn) <- common_celllines
  rownames(tissues_rnai_cmn) <- common_celllines
  
  # calculate inter-quartile range (iqr) lower fence values
  # as a threshold for sensitivity. Do for the rnai and rnai_qn
  # data sets
  
  rnai_iqr_thresholds <- NULL
  i <- NULL
  for(i in 1:ncol(rnai)){
    rnai_iqr_stats <- quantile(rnai[,i], na.rm=TRUE)
    rnai_iqr_thresholds[i] <- rnai_iqr_stats[2] - 	((rnai_iqr_stats[4] - rnai_iqr_stats[2]) * 1.5)
  }
  names(rnai_iqr_thresholds) <- colnames(rnai)
  
  rnai_qn_iqr_thresholds <- NULL
  i <- NULL
  for(i in 1:ncol(rnai_qn)){
    rnai_qn_iqr_stats <- quantile(rnai_qn[,i], na.rm=TRUE)
    rnai_qn_iqr_thresholds[i] <- rnai_qn_iqr_stats[2] - 	((rnai_qn_iqr_stats[4] - rnai_qn_iqr_stats[2]) * 1.5)
  }
  names(rnai_qn_iqr_thresholds) <- colnames(rnai_qn)
  
  
  return(
    list(
      rnai=rnai_muts_cmn,
      rnai_qn=rnai_qn_muts_cmn,
      func_muts=func_muts_rnai_cmn,
      all_muts=all_muts_rnai_cmn,
      mut_classes=mut_classes_rnai_cmn,
      rnai_qn_iqr_thresholds=rnai_qn_iqr_thresholds,
      rnai_iqr_thresholds=rnai_iqr_thresholds,
      tissues=tissues_rnai_cmn
    )
  )
}


# This is the further revised code from Colm (28 April 2016) which includes the Delta-Score (and effect size test, and without spearman, etc):
run_univariate_tests <- function(
  zscores,
  mutations,
  all_variants,
  sensitivity_thresholds=NULL,
  nperms=1000000,
  alt="less",
  min_size = 3
){	
  
  zscores <- as.matrix(zscores)
  mutations <- as.matrix(mutations)
  all_variants <- as.matrix(all_variants)
  
  work_count <- 0  # SJB added
  results <- NULL
  i <- NULL
  for(i in seq(1:length(colnames(mutations)))){
    
    #Skip driver genes we don't care about
    if ( !(colnames(mutations)[i] %in% cancergd_drivers_n5) ) {
      next
    }
    work_count <- work_count + 1
    print(paste(toString(i),"WORKING ON:",toString(work_count),colnames(mutations)[i]))
    
    grpA <- which(mutations[,i] > 0)

    gene <- colnames(mutations)[i]
    
    
    # grpB includes cell lines with no reported mutations at all
    # in gene...
    grpB <- which(all_variants[,gene] == 0)
    
    # skip if nA < min_size as we are never going to
    # consider anything based on n=2
    if(length(grpA) < min_size | length(grpB) < min_size){
      next
    }
    
    j <- NULL
    for(j in seq(1:length(colnames(zscores)))){
      ascores <- na.omit(zscores[grpA,j])
      bscores <- na.omit(zscores[grpB,j])
      nA <- length(ascores)
      nB <- length(bscores)
      if(nA < min_size){
        next
      }
      if(nB < min_size){
        next
      }
      wilcox.p <- NA
      try(
        test <- wilcox.test(
          ascores,
          bscores,
          alternative=alt
        )
      )
      wilcox.p <- test$p.value
      cles <- 1-(test$statistic/(nA*nB))
      
      marker <- colnames(mutations)[i]
      target <- colnames(zscores)[j]
      nMin <- min(nA,nB)
      zA <- median(ascores)
      zB <- median(bscores)
      zDiff <- zA - zB
      # Output the result if min sample size is min_size or more
      if(nMin >= min_size){
        results <- rbind(
          results,
          c(
            marker,
            target,
            nA,
            nB,
            wilcox.p,
            cles,
            zA,
            zB,
            zDiff
          )
        )
      }
    }
  }
  
  if(is.null(nrow(results))){
    return(NULL)
  }
  
  colnames(results) <- c(
    "marker",
    "target",
    "nA",
    "nB",
    "wilcox.p",
    "CLES",
    "zA",
    "zB",
    "ZDiff"
  )
  
  return(results)
  
}

run_univariate_test_bytissue <- function(x){
  
  tissue_types <- colnames(x$tissues)
  print(tissue_types)
  uv_results_bytissue <- NULL
  tissue <- NULL
  for(tissue in tissue_types){
    print(paste("\nProcessing tissue:",tissue,"..."))
    cellline_count <- sum(
      x$tissues[,tissue]
    )
    if(cellline_count < 6){
      print(paste("  Skipping tissue:",tissue,"as it has less than 6 cell lines."))
      next
    }
    tissue_rows <- which(
      x$tissues[,tissue] == 1
    )
    temp_results <- NULL
    temp_results <- run_univariate_tests(
      zscores=x$rnai[tissue_rows,],
      mutations=x$func_muts[tissue_rows,],
      all_variants=x$all_muts[tissue_rows,],
      sensitivity_thresholds=x$rnai_iqr_thresholds,
      min_size = 3
    )
    if(is.null(nrow(temp_results))){
      print(paste("Skipping ", tissue, " - no results", sep=""))
      next
    }
    temp_results <- cbind(
      temp_results,
      rep(tissue, times=nrow(temp_results))
    )
    uv_results_bytissue <- rbind(
      uv_results_bytissue,
      temp_results
    )
  }
  colnames(
    uv_results_bytissue
  )[ncol(
    uv_results_bytissue
  )
  ] <- "tissue"
  return(uv_results_bytissue)
}
# Better to change this function so that it doesn't need tissue_actual_names list:

write_box_dot_plot_data <- function(
  results,
  zscores,
  mutation.classes,
  mutations,
  exclusions,
  tissues,
  fileConn,
  writeheader,
  tissue_actual_names,
  response_type="Z-score"
){
  # Using cat() as does less conversion than print() so should be faster: https://stat.ethz.ch/R-manual/R-devel/library/base/html/cat.html
  if (writeheader){cat(names(results), "boxplot_data\n", file=fileConn, sep="\t")}
  # The by_tissue results will have extra 'tissue' column.
  
  data_rows <- character(500) # Initialise to a large empty vector so that appending is fast
  
  i <- NULL	
  for(i in 1:nrow(results)){

    if(results$nA[i] > 2){
      marker_gene <- strsplit(results$marker[i], "_")[[1]][1]
      target_gene <- strsplit(results$target[i], "_")[[1]][1]
      
      # make a factor with three levels:
      # 		wt,
      #		non-recurrent mutant
      # 		recurrent mutant
      # use for boxplot and  stripchart x-axis
      
      # start by setting all cell lines to wt
      wt_mut_grps_strings <- rep(
        "wt",
        times=length(mutations[,results$marker[i]])
      )
      
      # set the non-recurrent mutations
      wt_mut_grps_strings[which(exclusions[,results$marker[i]] == 1)] <- "non-rec. mut."
      # set the recurrent/functional mutations
      wt_mut_grps_strings[which(mutations[,results$marker[i]] == 1)] <- "rec. mut."						
      wt_grp_rows <- which(wt_mut_grps_strings == "wt")
      nonfunc_mut_grp_rows <- which(wt_mut_grps_strings == "non-rec. mut.")
      func_mut_grp_rows <- which(wt_mut_grps_strings == "rec. mut.")
      # Trim the target_variant last character from the gene names for Achilles data:
      if ((data_set == "Achilles") || (data_set == "Achilles_CRISPR")) {target_gene = substr(target_gene, 1, nchar(target_gene)-1)}
      # boxplot based on all data (wt and mut groups)
      # This print(...) just writes to the console - want to write to file - so maybe add to table then write.table(..
      # SJB: "In a box and whisker plot, a box is drawn around the quartile values, and the whiskers extend from each quartile to the extreme data points.
      # http://intermath.coe.uga.edu/dictnary/descript.asp?termID=57
      
      #Box Plots: http://sphweb.bumc.bu.edu/otlt/MPH-Modules/BS/R/R2_SummaryStats-Graphs/R2_SummaryStats-Graphs_print.html
      # A "boxplot", or "box-and-whiskers plot" is a graphical summary of a distribution; the box in the middle indicates "hinges" (close to the first and third quartiles) and median. The lines ("whiskers") show the largest or smallest observation that falls within a distance of 1.5 times the box size from the nearest hinge. If any observations fall farther away, the additional points are considered "extreme" values and are shown separately. A boxplot can often give a good idea of the data distribution, and is often more useful to compare distributions side-by-side, as it is more compact than a histogram. We will see an example soon.
      
      # From: https://stat.ethz.ch/R-manual/R-devel/library/grDevices/html/boxplot.stats.html
      #  boxplot.stats(x, coef = 1.5, do.conf = TRUE, do.out = TRUE)
      wt_boxplot = boxplot.stats( round(zscores[wt_grp_rows,results$target[i]],2), do.conf = FALSE, do.out = TRUE )
      # The round is so that will get same results as my javascript boxplot_stats() which uses input y values already rounded to 2 decimal places.
      wt_boxplot_stats = wt_boxplot$stats
      # http://r.789695.n4.nabble.com/Whiskers-on-the-default-boxplot-graphics-td2195503.html
      # http://stackoverflow.com/questions/8844845/how-do-i-turn-the-numeric-output-of-boxplot-with-plot-false-into-something-usa
      # http://rstudio-pubs-static.s3.amazonaws.com/21508_35a770dc38fa4658accef1acc4fb2fbe.html
      # *** GOOD: http://www.sr.bham.ac.uk/~ajrs/R/r-show_data.html
      # boxplot.stats: https://stat.ethz.ch/R-manual/R-devel/library/grDevices/html/boxplot.stats.html
      mutant_boxplot = boxplot.stats( round(zscores[func_mut_grp_rows,results$target[i]],2), do.conf = FALSE, do.out = TRUE )
      # The round is so that will get same results as my javascript boxplot_stats() which uses input y values already rounded to 2 decimal places.
      mutant_boxplot_stats = mutant_boxplot$stats
      boxplot_range <- range(wt_boxplot_stats, wt_boxplot$out, mutant_boxplot_stats, mutant_boxplot$out)
      boxplot_range <- c( floor(boxplot_range[1]), ceiling(boxplot_range[2]) ) # Round lower down and upper up to integers.
      cell_line_count <- 0  # This should be same as the data_rows_count
      data_rows_count <- 0  # Index for the 'data_rows' vector, which is number of cell-lines for this tissue (which is different from cell_line_count above for all the tissues for this driver+target)
      j <- NULL
      for(j in 1:length(tissue_actual_names)){
        tissue <- tissue_actual_names[j]
        wt_rows_by_tissue <- which(
          wt_mut_grps_strings == "wt" &
            tissues[,tissue] == 1
        )
        mutant_rows_by_tissue <- which(
          wt_mut_grps_strings == "rec. mut." &
            tissues[,tissue] == 1
        )
        
        # count to check that the full number of cell_lines is sent by the AJAX call:
        cell_line_count <- cell_line_count + length(wt_rows_by_tissue) + length(mutant_rows_by_tissue)
        
        # or set the data_rows vector length to the above: length(wt_rows_by_tissue) + length(mutant_rows_by_tissue)
        
        ### SJB: To get row names, use: print(row.names(tissues)[wt_rows_by_tissue])				
        if(length(wt_rows_by_tissue) > 0){
          y <- zscores[wt_rows_by_tissue,results$target[i]]
          cell_lines <- row.names(tissues)[wt_rows_by_tissue] # Added by SJB
          
          mutant_types <- mutation.classes[wt_rows_by_tissue,results$marker[i]] # Added by SJB - should all be 0 for wt.
          
          cell_line_tissues <- sub("^(.*?)_","",cell_lines) # the part after the first "_"
          if(length(which(cell_line_tissues != tissue)) > 0){
            unequal_tissues <- which(cell_line_tissues != tissue)
            for (k in 1:length(unequal_tissues)) {
              if (tissue=="INTESTINE" && (cell_line_tissues[k]=="LARGE_INTESTINE" || cell_line_tissues[k]=="SMALL_INTESTINE")) {
                #print(paste("Accepting:",cell_line_tissues[k],"==",tissue))
              } else {
                stop(paste("ERROR:",cell_line_tissues[k], "!=", tissue[k]))
              }
              # But for Achilles data we allow the case of: 
              #LARGE_INTESTINE != INTESTINE
              #SMALL_INTESTINE != INTESTINE
              # and lung.
            }
          }
          
          # for JSON:
          cell_line_names <- sub("_.*$","",cell_lines) # the part before the first "_"
          # or as CSV:
          for (k in 1:length(wt_rows_by_tissue)) {
            # cat(tissue,cell_line_names[k],y[k],"0;", file=fileConn, sep = ",") # "1" for mutant. (0 for wild type) Semi-colon is our end-of-line marker, instead of new-line.
            # cat(tissue,cell_line_names[k],round(x[k],2),y[k],"0;", file=fileConn, sep = ",") # "1" for mutant. (0 for wild type) Semi-colon is our end-of-line marker, instead of new-line.
            data_rows_count <- data_rows_count +1
            # Optionally add: (if (k==1) tissue else "")
            # The round(y[k],2) is needed for Achilles and Colt data, but seems already rounded in Campbell data:
            
            if (mutant_types[k]!=0) {stop(paste("ERROR: for k=",k,", mutant_types[k]=",mutant_types[k], "!= 0"))}
            data_rows[data_rows_count] <- paste(tissue,cell_line_names[k],round(y[k],2),"0", sep=",") # removed the semi colon, as will join at end using sep=';' as don't want semi-colon at end of the very last row.
          }
        }
        if(length(mutant_rows_by_tissue) > 0){
          # plot at 2
          #x <- jitter(rep(2,times=length(mutant_rows_by_tissue)), amount=0.33)
          y <- zscores[mutant_rows_by_tissue,results$target[i]]
          mutant_types <- mutation.classes[mutant_rows_by_tissue,results$marker[i]] # Added by SJB - should be non-zeros.
          cell_lines <- row.names(tissues)[mutant_rows_by_tissue] # Added by SJB
          #print(c(round(x,2),y,cell_lines)) # ,tissue_cols[j] # Added by SJB
          #for(k in 1:length(mutant_rows_by_tissue)) {print(sprintf("x:%.2f,y:%.2f,c:%s",x[k],y[k],cell_lines[k]), quote = FALSE)}
          cell_line_tissues <- sub("^(.*?)_","",cell_lines) # the part after the first "_"
          #					print(cell_line_tissues)
          if(length(which(cell_line_tissues != tissue)) > 0){
            unequal_tissues <- which(cell_line_tissues != tissue)					
            for (k in 1:length(unequal_tissues)) {
              if (tissue=="INTESTINE" && (cell_line_tissues[k]=="LARGE_INTESTINE" || cell_line_tissues[k]=="SMALL_INTESTINE")) {
                # print(paste("Accepting:",cell_line_tissues[k],"==",tissue))
              } else {
                stop(paste("ERROR:",cell_line_tissues[k], "!=", tissue[k]))
              }
            }
          }
          # for JSON:
          cell_line_names <- sub("_.*$","",cell_lines) # the part before the first "_"					
          # or as CSV:
          for (k in 1:length(mutant_rows_by_tissue)) {
            data_rows_count <- data_rows_count +1
            if (mutant_types[k]<=0) {stop(paste("ERROR: for k=",k,", mutant_types[k]=",mutant_types[k], "<= 0"))}
            data_rows[data_rows_count] <- paste(tissue,cell_line_names[k],round(y[k],2),mutant_types[k], sep=",") # removed ';' from end.

          } # end of: for (k in 1:length(mutant_rows_by_tissue)) { ....
        }  # end of: if(length(mutant_rows_by_tissue) > 0){ ....
      } # end of: for(j in 1:length(tissue_actual_names)){ ....
      if (data_rows_count!=cell_line_count) {stop(paste("ERROR:",cell_line_count, "!=", tissue))}
      # Correct:
      #"ERBB2_2064_ENSG00000141736      MAP2K3_ENSG00000034152  12      67      0.000379762881197737    0.807213930348259       range,-5,2;
      #wt_box,-2.66,-1.28,-0.62,0.04,1.26;
      #mu_box,-4.61,-3.555,-1.765,-0.91,-0.62;
      #BONE,143B,1.14,-0.21,0;BONE,CAL72,1.1,-0.61,0;BONE,G292,1.01,-1.85,0;BONE,HOS,1.13,-2.15,0;BONE,HUO3N1,0.86,-1.12,0;BONE,HUO9,0.82,-0.91,0;BONE,MG63,0.71,-1.48,0;BONE,NOS1,1.12,-0.99,0;BONE,NY,0.97,0.18,0;BONE,SAOS2,1.16,-0.91,0;BONE,SJSA1,1.11,0.88,0;BONE,U2O"
      
      "ERBB2_2064_ENSG00000141736      MAP2K3_ENSG00000034152  12      67      0.000379762881197737    0.807213930348259       -1.765  -0.62   -1.145  
      (count:)79,
      (range:)-5,2,
      (wt_box:)-2.66,-1.28,-0.62,0.04,1.26,
      (mu_box:)-4.61,-3.555,-1.765,-0.91,-0.62;
      (cell_line:)BONE,143B,-0.21,0;
      (cell_line:)BONE,CAL72,-0.61,0;
      (cell_line:)BONE,G292,-1.85,0;BONE,HOS,-2.15,0;BONE,HUO3N1,-1.12,0;BONE,HUO9,-0.91,0;BONE,MG63,-1.48,0;BONE,NOS1,-0.99,0;BONE,NY,0.18,0;BONE,SAOS2,-0.91,0;BONE,SJSA1,0.88,0;BONE,U2OS,0.36,0;BREAST,BT20,-2.29,0;BREAST,BT549,-1.67,0;BREAST,CAL120,1.26,0;BREAST,CAL51,-0.67,0;BREAST,CAMA1,1.04,0;BREAST,DU4475,0.22,0;BREAST,HCC38,-0.23,0;BREAST,HCC70,-0.91,0;BREAST,HS578T,-2.03,0;BREAST,MCF7,-0.42,0;BREAST,MDAMB157,-1.54,0;BREAST,MDAMB231,-0.1,0;..."
            
      cat(file=fileConn, sep="\t", unname(unlist(results[i,])))
      cat(file=fileConn, "\t")
      cat(file=fileConn, sep = ",", cell_line_count, boxplot_range, wt_boxplot_stats, mutant_boxplot_stats)
      cat(file=fileConn, ";")
      cat(file=fileConn, sep=';', data_rows[1:data_rows_count])  # data_rows[1:data_rows_count] is same as head(data_rows, n=data_rows_count)
      cat(file=fileConn, "\n")

    } # end of: if(results$nA[i] > 2){ marker_gene <- strsplit(results$marker[i], "_")[[1]][1]; target_gene <- strsplit(results$target[i], "_")[[1]][1]
  }
  #	close(fileConn) # caller should close the fileConn
}







