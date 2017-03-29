# ====================================== #
# Analysis functions used for univariate
# analyses in the Intercell II work
# jamesc@icr.ac.uk, 11th March 2014
# Modified: s.bridgett@qub.ac.uk, March 2017
# ====================================== #
require("preprocessCore")
require(gplots)
require(mixtools)


# List of driver genes we care about (March 2017): "The rules for this list is that a gene must be present in our putative driver gene set (GDSC1000_cnv_exome_func_muts_v1) and also listed in either the Cancer Gene Census or a curated list from the Vogelstein lab. This results in a starting set of 256 genes. We then identify those genes that contain functional alterations in at least five cell lines in one study (ignoring tissue type) or in at least 3 cell lines in one study all of the same tissue type. This gives us a list of 53 driver genes." 
cancergd_drivers_n5 <- read.csv("../input_data/AlterationDetails.csv")$Gene


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
# And writing directly to file, which especially for Cowley and Marcotte data is much faster than rbind()
# if tissue is NULL then won't write tissue column (ie. for pan-cancer data)
run_univariate_tests <- function(
  zscores,
  mutations,
  all_variants,
  sensitivity_thresholds=NULL,
  nperms=1000000,
  alt="less",
  min_size = 3,
  fileConn,
  writeheader,
  tissue=NULL
){	

  if (writeheader){
      cat(file=fileConn, sep="\t", "marker", "target", "nA", "nB", "wilcox.p", "CLES", "zA", "zB", "ZDiff")
	  if (! is.null(tissue)) {cat(file=fileConn, "\ttissue")}
	  cat(file=fileConn, "\n")
	  }
  
  zscores <- as.matrix(zscores)
  mutations <- as.matrix(mutations)
  all_variants <- as.matrix(all_variants)
  
  num_results <- 0 # SJB added
  work_count <- 0  # SJB added

  i <- NULL
  for(i in seq(1:length(colnames(mutations)))){
    
    #Skip driver genes we don't care about
    if ( !(colnames(mutations)[i] %in% cancergd_drivers_n5) ) {
      next
    }
    work_count <- work_count + 1
    cat("   ",work_count, "WORKING ON: i=", i,":", colnames(mutations)[i], "\n")
    
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
      	# Using cat(..paste()) gives upto 15 digit output, so is same as write.table(). Whereas just using cat() alone gives only 7 digit, unless set options("digits")=15.
		# options("digits"=15)  getOption("digits")
        cat(file=fileConn, sep="\t", marker, target, nA, nB, paste(sep="\t",wilcox.p, cles, zA, zB, zDiff) )
		if (! is.null(tissue)) {cat(file=fileConn, sep="", "\t", tissue)} # NOTE: just "\t" here, not sep="\t", but default is a space.
        cat(file=fileConn, "\n")
		num_results <- num_results + 1;
      }
    }
  }
    
  return(num_results)
}


run_univariate_test_bytissue <- function(x, fileConn, writeheader){
  
  tissue_types <- colnames(x$tissues)
  cat("\nTissue types:\n", tissue_types, "\n")

  tissue <- NULL
  total_num_results <- 0
  
  for(tissue in tissue_types){
    cat("\nProcessing tissue:",tissue,"...\n")
    cellline_count <- sum(
      x$tissues[,tissue]
    )
#    if(cellline_count < 6){
#      print(paste("  Skipping tissue:",tissue,"as it has less than 6 cell lines."))
# Changed in March 2017 for the new driver selection rule: 
#   "...functional alterations in at least five cell lines in one study (ignoring tissue type) or in at least 3 cell lines in one study all of the same tissue type."
# BUT the test below isn't quite correct ...... as could have less than 3 cellines in one tissue type but still have 5 cellines when ignoring tissue type. Although the min_size=3 argument for run_univariate_tests(...) below is still testing for that anyway.
#    if(cellline_count < 3){
#      print(paste("  Skipping tissue:",tissue,"as it has less than 3 cell lines."))
#      next
#    }
# In the main "" script run_univariate_tests(...) has min_size=5 for pancancer tests so that is ok.
    tissue_rows <- which(
      x$tissues[,tissue] == 1
    )

    num_results <- run_univariate_tests(
      zscores=x$rnai[tissue_rows,],
      mutations=x$func_muts[tissue_rows,],
      all_variants=x$all_muts[tissue_rows,],
      sensitivity_thresholds=x$rnai_iqr_thresholds,
      min_size = 3,
	  fileConn=fileConn,
	  writeheader=writeheader,
	  tissue=tissue
    ) 
	if (num_results == 0) { cat("\n Skipping ", tissue, " - as no results", "\n") }
	total_num_results <- total_num_results + num_results
	writeheader <- FALSE
	
  }

  return(total_num_results)
}

  
write_box_dot_plot_data <- function(
  results,
  zscores,
  mutation.classes,
  mutations,
  exclusions,
  tissues,
  fileConn,
  writeheader,
  response_type="Z-score"
){
  # Using cat() as does less conversion than print() so should be faster: https://stat.ethz.ch/R-manual/R-devel/library/base/html/cat.html
  if (writeheader){cat(names(results), "boxplot_data\n", file=fileConn, sep="\t")}
  # The by_tissue results will have extra 'tissue' column.
  
  write_box_stats <- TRUE
  data_rows <- character(500) # Initialise to a large empty vector so that appending is fast
  
  tissue_names <- colnames(tissues)
  
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
	  
	  if (write_box_stats) {
	    # As boxplot stats are now computed by the javascript on-the-fly as need to resize boxplots when interactively unselect/select different tissues in the web interface.
	    # BUT "svg_boxplots.js" javascript still checks that's it's initial boxes match these values from R, but this could optionally be removed in future from this R script.
        # boxplot based on all data (wt and mut groups)

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
	  }
	  
      cell_line_count <- 0  # This should be same as the data_rows_count
      data_rows_count <- 0  # Index for the 'data_rows' vector, which is number of cell-lines for this tissue (which is different from cell_line_count above for all the tissues for this driver+target)
      j <- NULL
      for(j in 1:length(tissue_names)){
        tissue <- tissue_names[j]
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
      } # end of: for(j in 1:length(tissue_names)){ ....
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
      cat(file=fileConn, sep = "", cell_line_count, ',')
	  if (write_box_stats) {cat(file=fileConn, sep = ",", boxplot_range, wt_boxplot_stats, mutant_boxplot_stats)}
      cat(file=fileConn, ";")
      cat(file=fileConn, sep=';', data_rows[1:data_rows_count])  # data_rows[1:data_rows_count] is same as head(data_rows, n=data_rows_count)
      cat(file=fileConn, "\n")

    } # end of: if(results$nA[i] > 2){ marker_gene <- strsplit(results$marker[i], "_")[[1]][1]; target_gene <- strsplit(results$target[i], "_")[[1]][1]
  }
  #	close(fileConn) # caller should close the fileConn
}

