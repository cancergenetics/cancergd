// The functions for displaying and downloading the SVG (scalable vector graphics) boxplots 

// Global variables in this script:

var SHOW_NEXT_PREV_BUTTONS = false; // false to hide the 'Previous', 'Close' and 'Next' boxplot buttons.

var tissue_colours = {
  "BONE":         "yellow",  // BONE includes OSTEOSARCOMA, as Achilles BONE contains OSTEOSARCOMA non-OSTEOSARCOMA cell-lines.
  // "OSTEOSARCOMA": "yellow", // same as BONE above
  "BREAST":       "deeppink",  // Colt only contains Breast
  "CENTRAL_NERVOUS_SYSTEM": "darkgoldenrod",  // The original "darkgoldenrod4" colour doesn't work in IE.
  // "CERVICAL":     "blue",  // Not in Achilles data. Not in 23 driver dependencies
  "CERVIX":       "blue",  // Changed from Cervical to Cervix, Sept 2016. Not in Achilles data. Not in 23 driver dependencies  
  "ENDOMETRIUM":  "orange",     // Not in 23 driver dependency data
  "HEADNECK":     "firebrick",  // Not in Achilles data  (The original "firebrick4" colour doesn't work in IE) - NOT in dependency data from the 23 drivers, so don't show on legend.
  "LUNG":         "darkgrey",
  "OESOPHAGUS":   "green",
  "OVARY":        "cadetblue",
  "PANCREAS":     "purple",

  // The following are NOT in the Campbell dataset for the 23 driver dependency data:
  "HAEMATOPOIETIC_AND_LYMPHOID_TISSUE": "darkred",
  "INTESTINE":    "saddlebrown",  // Can remove this "INTESTINE" in future as replaced by "LARGE_INTESTINE"
  "LARGE_INTESTINE":    "saddlebrown",
  "KIDNEY":       "indianred",
  "PROSTATE":     "turquoise",
  "SKIN":         "peachpuff",
  "SOFT_TISSUE":  "lightgrey",
  "STOMACH":      "black",
  "URINARY_TRACT":"yellowgreen",
  // "LIVER":        "slategray", // Not in Campbell,  Not in 23 driver dependency data, so don't display on legend  

// In Achilles R input data Aug 2016:
// "OTHER"                         
  "PLEURA": "slategray"  // Occurs in the PANCAN samples, as no longer merging with LUNG
  };


var current_dependency_td; // To store the html table cell that this boxplot represents.
var svg_fancybox_loaded = false;
var drawing_svg = false;
var boxplot_csv = ''; 
var svgNS="http://www.w3.org/2000/svg"; // Name space needed for SVG.

// Boxplot dimensions and scaling:
var irange=0, iwtbox=3, imubox=8;
var itissue=0, icellline=1, iy=2, imutant=3;  // was: ix=2, 
var svgWidth=500, svgHeight=500;
var XscreenMin=50,  XscreenMax=(svgWidth-10); // To allow for a margin of 50px at left, and 10px at right
var YscreenMin=(svgHeight-50), YscreenMax=10; // To allow a margin of 50px at bottom, and small 10px margin at top
var wtxc=1.6, muxc=3.8, boxwidth=1.8;
var svg, xscale, yscale, Yscreen0, points;
var tissue_lists={};

var collusionTestRadius=4.6; // just less than the point radius, so can overlap slightly.
var PointRadius = 5; // Radius of Circle on the SVG plot.

var TriangleHalfBase = Math.sqrt(Math.PI/Math.sqrt(3))*PointRadius; // This is half the width of triangle base, so that triangle has same area as the circle
var TriangleBaseToCentre = Math.sqrt(Math.PI/(3*Math.sqrt(3)))*PointRadius; // base to circumcentre of triangle (is 1/sqrt(3) times the half base width).
var TriangleCentreToApex = Math.sqrt((4*Math.PI)/(3*Math.sqrt(3)))*PointRadius; // circumcentre to apex of triangle (is 2/sqrt(3) times the half base width).
// So triangle points relative to centre are at: (x,y) = (-TriangleHalfBase, -TriangleBaseToCentre), (-TriangleHalfBase, -TriangleBaseToCentre), (0,TriangleCentreToApex).

var SquareCornerXY = 0.5*Math.sqrt(Math.PI)*PointRadius; // So square has same are as circle withy radius PointRadius.

var DiamondDiagonalXY = 0.5*Math.sqrt(2*Math.PI)*PointRadius; // So diagonal has same are as circle with radius PointRadius.

var wt_boxplot_elems=[], mu_boxplot_elems=[], axes_elems=[], mutation_legend=null, copynumber_legend=null;

// Array indexes for the 7-number boxplot_stats():
var ilowerwhisker=1, ilowerhinge=2, imedian=3, iupperhinge=4, iupperwhisker=5; // also: ilowest=0, ihighest=6



function parse_boxplot_csv_data_into_points_array(boxplot_csv) {
  var data_lines = boxplot_csv.split(";");
  //console.log("data_lines.length = "+data_lines.length);

  points = []; // 'points' is global array used by the tooltip on hoover, etc.
  points.push(data_lines[0].split(","));  // The first line is: cellline_count, y-axis_min, y-axis_max, and wt & mu box stats.

  var NA_total = 0; // count of lines with y='NA'
  for (var i=1; i<data_lines.length; i++) {  
    var col = data_lines[i].split(",");	
    if (col[iy]=='NA') {console.log("Skipping "+col[icellline]+" "+tissue+" as y='"+col[iy]+"'"); NA_total++; continue;}
    if (col[itissue]=="OSTEOSARCOMA") {col[itissue]="BONE";}  // BONE is "OSTEOSARCOMA" in the tissue_colours array.
	points.push(col);
  }    

  var cellline_count = parseInt(points[0][0]) - NA_total; // Ignore these 'NA' points.
  
  // The "cellline_count" is the number of cell_lines. So add 1 lines for first points(cellline_count,range,wt_box,mu_box).
  if (points.length-1 != cellline_count) {alert( "Boxplot data length mismatch: "+(points.length-1)+" != "+cellline_count+" -NA_total")}  
  }


  
function draw_svg_boxplot(driver, target, boxplot_data) {
  if ((typeof boxplot_data !== 'undefined') && (boxplot_data!='')) {boxplot_csv=boxplot_data;} // so this function was called by AJAX success.
  
  if ((drawing_svg) || (boxplot_csv=='') || (!svg_fancybox_loaded)) {return true;} // returning 'true' so fancybox will display its content, but still waiting for AJAX to return with the boxplot data.
  drawing_svg = true; // To prevent drawing twice if both callbacks (from fancybox and AJAX) happened as same time.

  remove_existing_svg_elems();
  
  parse_boxplot_csv_data_into_points_array(boxplot_csv);

  var ymin = parseInt(points[0][1]), ymax = parseInt(points[0][2]);

  // These are global:
  // From: http://www.i-programmer.info/programming/graphics-and-imaging/3254-svg-javascript-and-the-dom.html
  svg=document.getElementById("mysvg"); // or can create with js: var svg=document.createElementNS(svgNS,"svg"); svg.width=300; svg.height=300; document.body.appendChild(svg);
  if (!svg) {alert("*****ERROR: SVG is undefined"+"  Fancybox loaded="+svg_fancybox_loaded);}
    
  xscale = 100; 
  yscale = (YscreenMax-YscreenMin)/(ymax-ymin);  // This is -ive, so Yscreen0 = YscreenMin + ymin*yscale
  Yscreen0 = YscreenMin - ymin*yscale;  // is really Yscreen0 = YscreenMin + (y0 - ymin)*yscale; eg. 380+(0-2)*(-30)
  
  axes_elems = axes(wtxc,muxc, ymin,ymax, driver,target);

  // Instead of using the box_stats calculated by the R script:
  // To match my javascript boxplot_stats() which return 7 numbers, starting at position 1 (as zero should be the lowest extreme point)   
  // var wt_boxstats = []; for (var i=0; i<5; i++) {wt_boxstats[i+1] = parseFloat(points[0][iwtbox+i]);}
  // var mu_boxstats = []; for (var i=0; i<5; i++) {mu_boxstats[i+1] = parseFloat(points[0][imubox+i]);}
  // Store the boxplot lines and rectangle in global array, so can adjust position later:
  // wt_boxplot_elems = boxplot( wtxc, boxwidth, wt_boxstats, "wtbox1", wt_boxplot_elems);
  // mu_boxplot_elems = boxplot( muxc, boxwidth, mu_boxstats, "mubox1", mu_boxplot_elems);
  // Can calculate box_stats (false means don't check the tissue checkboxes):
  update_boxplots(false); // sets wt_boxplot_elems and mu_boxplot_elems arrays, and creates/updates the boxplot box and whisker positions.
	
  // beeswarm(points, wtxc-1*boxwidth, muxc-2*boxwidth, boxwidth); // The -1 and -2 are because that is the position set in R for the jitter.
  beeswarm(points, wtxc, muxc, boxwidth); // The -1 and -2 are because that is the position set in R for the jitter.

  add_target_info_to_boxplot(target); // this gene info and ncbi_summary is returned with the boxplot_data from the AJAX call.

  add_tooltips();  
}


function remove_existing_svg_elems() {
  // tissue_lists is a global variable as used by 'toggle_tissue_checkboxes(e)'
  for (var tissue in tissue_lists) {
	  tissue_lists[tissue] = remove_array_of_elements(tissue_lists[tissue]); // remove any existing points.
    }
  tissue_lists={};
  mutation_legend = null;  copynumber_legend = null;    // Are in the axes_elems below.
  axes_elems = remove_array_of_elements(axes_elems);    // Delete the old axes elems.
  wt_boxplot_elems = remove_array_of_elements(wt_boxplot_elems);
  mu_boxplot_elems = remove_array_of_elements(mu_boxplot_elems); 
  // elements will be destroyed by garbage collector when there are no reference counts to them.
  }


function remove_array_of_elements(elems) {
  // were created using: var e = document.createElementNS(svgNS, svgType);
  for (var i=0; i<elems.length; i++) {
	elems[i].parentNode.removeChild(elems[i]); // or: document.removeChild(elems[i]); or svg.removeChild(elems[i]);
    }
  return [];
  }

	
function tohalf(x, strokewidth) {
  // As drawing vertical or horizontal one-pixel-wide lines positioned at the half pixel will make them exactly one pixel wide and won't be anti-aliased.
  return (strokewidth % 2 == 0) ? Math.round(x) : Math.floor(x)+0.5; // if even width then center line on grid, else center half-way between grid lines.
  }


function axes(wtxc,muxc, ymin,ymax, driver, target) {	
  var elems = [
    svg_line(wtxc, ymin, muxc, ymin, "1px", false, "black"), // the horizontal axis	
	svg_line(wtxc, ymin, wtxc, ymin+8/yscale, "1px", false, "black"), // tick mark at 'wt'
	svg_line(muxc, ymin, muxc, ymin+8/yscale, "1px", false, "black"), // tick mark at 'mutant'
    svg_text(wtxc,ymin+23/yscale,18,false,"wt"),	    // The svg text class is set to: text-anchor: middle.
    svg_text(muxc,ymin+23/yscale,18,false,"altered"),
    svg_text(0.5*(XscreenMin+XscreenMax)/xscale,ymin+45/yscale,20,false,driver+"  status"),
		
	svg_line(XscreenMin/xscale, ymin, XscreenMin/xscale, ymax, "1px", false, "black"), // y-axis
    svg_text(15/xscale,0.5*(ymin+ymax),20,true,target+" Z-score"),	 	//svg_text(15/xscale,ymin+2,20,true,target+" Z-score");
	svg_line(XscreenMin/xscale,-2, XscreenMax/xscale,-2, "1px", true, "red") // the red y=-2 full-width line	  
	];
	
	for (var y=ymin; y<=ymax; y++) {
	  elems.push( svg_line((XscreenMin-5)/xscale,y, XscreenMin/xscale,y,"1px",false,"black") );
	  var x = y>=0 ? 0.32 : 0.27;
	  elems.push( svg_text(x,y+8/yscale,18,false, y.toString()) );
	  }
	  
    // The labels for the type of alteration:
	//var x = tohalf( (XscreenMin + 0.80*(XscreenMax-XscreenMin))/xscale ,1);
    //var y = tohalf(ymin+45/yscale,1);
    var x = XscreenMin+ 0.85*(XscreenMax-XscreenMin);
	var y = ymin*yscale+15;  // yscreen = Yscreen0 + y*yscale;

	var e = document.createElementNS(svgNS, "polygon");
	e.setAttribute("fill", "white");	
	e.setAttribute("points",diamond_points(x,Yscreen0+y-5));   // yscreen = Yscreen0 + y*yscale;
    svg.appendChild(e);
    elems.push(e);
	e.onmouseover = mutation_legend_Over;
	e.onmouseout  = mutation_legend_Out;
	mutation_legend = e; // Global variable for now.	
   
	e = svg_text( (x+28)/xscale ,y/yscale,11,false, "Mutation");
	e.onmouseover = mutation_legend_Over;
	e.onmouseout  = mutation_legend_Out;
	elems.push(e);
	
	var y = ymin*yscale+30;
	e = document.createElementNS(svgNS, "polygon");
	e.setAttribute("fill", "white");
	e.setAttribute("points", triangle_points(x, Yscreen0+y-2));   // yscreen = Yscreen0 + y*yscale;
	svg.appendChild(e);
	elems.push(e);
	e.onmouseover = copynumber_legend_Over;
	e.onmouseout  = copynumber_legend_Out;
	copynumber_legend = e; // Global variable for now.
    e = svg_text( (x+40)/xscale, y/yscale,11,false, "Copy number");
	e.onmouseover = copynumber_legend_Over;
	e.onmouseout  = copynumber_legend_Out;	
	elems.push(e);
	
    return elems;
    }


function highlight_mutant_points(alteration_code, polygon_class) {
    // alteration_code is either "0" for or "1" for ...  ("0" is Wildtype)	
	//   "1" = mutation
    //   "2" = copy number (is one a deletion and one an amplification?)
	// test on driver: ARID1B, target: PIK3R2
	//console.log("highlight_mutant_points: "+alteration_code+" r:"+stroke_width);
    for (var i=1; i<points.length; i++) { // correctly starts at i=1, as points[0] is the boxplot dimensions.	
	    if (points[i][imutant]==alteration_code) {
			e = document.getElementById("c"+i.toString());
	        // e.setAttribute("stroke-width", stroke_width);  // This didn't work as is over-ruled by the polygon class which has stroke-width of 1px, so change the class instead:
			e.setAttribute('class', polygon_class);
		    }
	    }
    }	
	

function mutation_legend_Over(e)   {mutation_legend.setAttribute('class',"bold");   highlight_mutant_points("1", "bold");} // see: polygon:hover class below.
function mutation_legend_Out(e)    {mutation_legend.setAttribute('class',null);     highlight_mutant_points("1", null);  }   // ie. back to the default polygon.
function copynumber_legend_Over(e) {copynumber_legend.setAttribute('class',"bold"); highlight_mutant_points("2", "bold");}
function copynumber_legend_Out(e)  {copynumber_legend.setAttribute('class',null);   highlight_mutant_points("2", null);  }
	
function highlight_tissue_points(tissue, newclass) {
	//console.log("highlight_tissue_points: "+tissue);
    for (var i=1; i<points.length; i++) { // correctly starts at i=1, as points[0] is the boxplot dimensions.	
	    if (points[i][itissue]==tissue) {
			e = document.getElementById("c"+i.toString());
	        // e.setAttribute("stroke-width", stroke_width);  // This didn't work as is over-ruled by the polygon class which has stroke-width of 1px, so change the class instead:
			e.setAttribute('class', newclass);
		    }
	    }
    }	

function tissue_legend_Over(e) {
	e = e || window.event;  // Need: window.event for IE <=8 
    var tissue_legend = e.target || e.srcElement;
    var tissue = tissue_legend.id.substring(3); /// the tissue colour cell name is the 'tb_'+tissue.
	
	// tissue_legend.setAttribute(); // eg. set border thicker line ?
	highlight_tissue_points(tissue, "bold"); // In the SVG I've defined 'bold' class has been defined for both circle and polygon.
    // return false; // does true mean event was handled?	
	}

function tissue_legend_Out(e)  {
	e = e || window.event;  // Need: window.event for IE <=8 
    var tissue_legend = e.target || e.srcElement;
    var tissue = tissue_legend.id.substring(3); /// the tissue colour cell name is the 'tb_'+tissue.
	
	// tissue_legend.setAttribute(); // eg. set border thicker line ?
	highlight_tissue_points(tissue, null);
    // return false; // does true mean event was handled?	
    }

	
	
	
function mouseOver(e) {
	e = e || window.event;  // Need: window.event for IE <=8 
	var target = e.target || e.srcElement;
	target.setAttribute("r", "10");   // "r" only applies to circles.
    }


function mouseOut(e) {
	e = e || window.event;  // Need: window.event for IE <=8 
	var target = e.target || e.srcElement;
	target.setAttribute("r", "5");
    }



function search_rows_above_and_below(which_row,row,row_above,row_below,row_twoabove,row_twobelow) {
    var i = row.length; // ie. beyond end of this row
    while ( ((i < row_above.length) && row_above[i]) // testing for a space in the row below
         || ((i < row_below.length) && row_below[i]) // and for a space in the row above
         || ((i < row_twoabove.length) && row_twoabove[i]) // testing for a space in the row below
         || ((i < row_twobelow.length) && row_twobelow[i]) // and for a space in the row above		 
        ) {
        i++;
        //console.log('searching_above_and_below '+which_row+': '+i)
        }
    return i;
}

function get_median(y,start,end) {
	var len = end-start+1;
	//console.log("get_median:",start,end,"len:",len);
    if (len==0) {alert("Array is empty"); return;}
	if (len % 2 !=0) { // is odd length
	    return y[start + (len-1)/2];  // or (start+end)/2
	}
	else { // is even length
	    return 0.5*(y[start + (len-2)/2] + y[start + len/2]); // or y[(start+end-1)/2] + y[(start+end+1)/2]
	}
}

 
function boxplot_stats(y) {
  // for an array of input numbers (integers or floating point), returns an array of 7 numbers for:
  //    min, lower_fence, lower_quartile, median, upper_quartile, upper_fence, max
  // (often called the Tukey boxplot) as in figure 3 of:
  //   where: the lower_fence is the lowest point still within 1.5 IQR(inter-quartile range) of the lower quartile,
  //      and the upper_fence is the highest point still within 1.5 IQR of the upper quartile 
  // This is same as R's boxplot.stats function:  https://en.wikipedia.org/wiki/Five-number_summary#Example_in_R
  // As finds the lower and upper "hinges" for Tukey (ie. inclusive Hinge) method.
  // see: https://en.wikipedia.org/wiki/Box_plot#Types_of_box_plots
  // http://www.ibm.com/support/knowledgecenter/SSLVMB_20.0.0/com.ibm.spss.statistics.help/alg_examine_tukey.htm
  // http://mathforum.org/library/drmath/view/60969.html
  // Or better: http://peltiertech.com/hinges/
  // http://peltiertech.com/comparison/

    var len = y.length;
    if (len==0) {return [0,0,0,0,0,0,0];} // return all zeros (or could return [];)	
	
	var sorted = y.sort(function(a, b){return a-b}); // by default sort compares as strings, so need this number compare function parameter.
	var end = len-1;  // as zero-based arrays.
	var min = sorted[0];
	var max = sorted[end];
	
	// Now find the lower and upper "hinges" for Tukey (ie. inclusive Hinge) method:
	var median = get_median(y,0,end);
	if (len %2 != 0) { // odd length, so include the middle in both halves
	   var middle = end/2;
	   var lower_quartile = get_median(y,0,middle);
	   var upper_quartile = get_median(y,middle,end);
	}
    else { // even length, so no middle point
	   var lower_quartile = get_median(y, 0, len/2-1);  // (len/2)-1 is end_of_lower_half
	   var upper_quartile = get_median(y, len/2 ,end);  // len/2 is start_of_upper_half, as zero-based array.
	}
	
	var quartile_range_15 = 1.5*(upper_quartile - lower_quartile); // as fences are within (1.5 of interquartile range) from the lower and upper quartiles respectively.
    var lower_fence = (lower_quartile-quartile_range_15);
    for (var i=0; i<=end; i++) { // start at min point
		if (sorted[i]>=lower_fence) {lower_fence=sorted[i]; break}
	}
    var upper_fence = (upper_quartile+quartile_range_15);
    for (var i=end; i>=0; i--) { // start at max point
		if (sorted[i]<=upper_fence) {upper_fence=sorted[i]; break}
	}
	
	return [ min, lower_fence, lower_quartile, median, upper_quartile, upper_fence, max ];
}


function download_legend(legend_type) {	
  // Using canvas, as IE9+ supports canvas.
  var ytop=20, xcircles=20, rad=8, xtext=40, line_height=25, font="20px Arial";  // maybe: font-family: sans-serif;

  var list;
  if (legend_type=='selected') {
    show_message("download_selected_legend", "Downloading...");
    list = tissue_lists;
  }
  else if (legend_type == 'all') {
    show_message("download_all_legend", "Downloading...");	  
	list = tissue_colours;	
  }
    
  var canvas = document.createElement('canvas');
  canvas.id="mycanvas"; // or:  canvas.setAttribute("id", "mycanvas");
  
  ctx = canvas.getContext('2d');
  ctx.font = font;

  var len=0, maxtextwidth=0, tissue;
  for (tissue in list) {
	 if ((legend_type=='selected') && (!document.getElementById('cb_'+tissue).checked)) {continue}
     var width = ctx.measureText(histotype_display(tissue).replace('&amp;','&')).width;
     if (width>maxtextwidth) {maxtextwidth=width}
	 len++;
     }
    
  canvas.width  = xtext+maxtextwidth+xcircles-rad; // margin of xcircles around
  canvas.height = ytop+(len-1)*line_height+ytop; // so margin of ytop at top and bottom
  //canvas.style="border:1px solid #000000;" is only for display on screen, as the downloaded image doesn't have this box. Need to draw a rect for background otherwise download has transparent background.

  // To avoid anti-aliasing, draw lines at half-pixel positions: http://www.rgraph.net/docs/howto-get-crisp-lines-with-no-antialias.html
  canvas_rect(ctx, 0.5,0.5, canvas.width-1, canvas.height-1, "white", "black"); // Make background white inside black rect.
  
  var y = ytop;
  for (tissue in list) {	  
	  if ((legend_type=='selected') && (!document.getElementById('cb_'+tissue).checked)) {continue}
	  var mtext = histotype_display(tissue).replace('&amp;','&'); // for "Blood &amp; Lymph"	  
	  
	  // Add 0.5 to improve the anti-aliasing of the circle. (Adding 0.5 has no effect on the text)
	  canvas_circle(ctx, xcircles+0.5, y-0.5, rad, tissue_colours[tissue]);
      canvas_text(ctx, xtext, y, mtext, font);
	  y += line_height;	  
	  }

  var filename="Legend_"+legend_type+'_'+len.toString()+'tissues.png';
  if (canvas.msToBlob) { //for IE:
      window.navigator.msSaveBlob(canvas.msToBlob(), filename);
  }
  else { //other browsers:
	  download_data(canvas.toDataURL("image/png",1), filename);	
  }
	
  return false; // false prevents page refreshing.
}


function canvas_rect(ctx, x,y, width,height, fillcolor, strokecolor) {
  ctx.beginPath();
  ctx.fillStyle = fillcolor;
  ctx.lineWidth = "1";
  ctx.strokeStyle = strokecolor;
  ctx.rect(x,y, width, height);
  ctx.stroke();
  ctx.fill();
  ctx.closePath(); // Circles and rectangles don't actually need the path to be closed.  
  }


function canvas_line(ctx, x1,y1,x2,y2, color) {
  ctx.lineWidth = "1";
  ctx.strokeStyle = color;
  ctx.moveTo(x1,y1);
  ctx.lineTo(x2,y2);
  ctx.stroke();  // This actually draws the line.
  }

function canvas_circle(ctx, x, y, r, fillcolor) {
  ctx.beginPath();  // Beginning new shape
  ctx.arc(x, y, r, 0, 2 * Math.PI); // false); // params: xcentre, ycentre, radius, startAngle, endAngle, anticlockwise(optional);
  ctx.fillStyle = fillcolor; // OR: = 'rgba(255,255,255,0.8)';
  ctx.fill();
  ctx.lineWidth = 1;
  ctx.strokeStyle = "black";
  ctx.stroke();
  ctx.closePath(); // Circles and rectangles don't actually need the path to be closed.
  }

function canvas_text(ctx, x,y, mtext, font) {
  ctx.font = font; // eg: "15px Arial", or "30px Comic Sans MS"; or ctx.font = radius*0.15 + "px arial";
  ctx.fillStyle = "black";
  // ctx.textAlign = "center";
  ctx.textBaseline="middle";
  ctx.fillText(mtext,x,y); // eg: ctx.fillText("Hello World", canvas.width/2, canvas.height/2); 
  }

  

function triangle_points(x,y) {
	x = tohalf(x,1)
    y = tohalf(y,1)
    return    tohalf(x-TriangleHalfBase,1).toString()+","+tohalf(y+TriangleBaseToCentre,1).toString()
         +" "+tohalf(x+TriangleHalfBase,1).toString()+","+tohalf(y+TriangleBaseToCentre,1).toString()
         +" "+x.toString()                           +","+tohalf(y-TriangleCentreToApex,1);
}

function diamond_points(x,y) {
	// Sets corner points for drawing diamond. An alternative is a 45 degree rotated square (a diamond) can be created using: <rect x="203" width="200" height="200" style="fill:slategrey; stroke:black; stroke-width:3; -webkit-transform: rotate(45deg);"/>

	x = tohalf(x,1); // Setting centre to half position as otherwise the diamond is not symentical even if use tohalf(x,1) below:
	y = tohalf(y,1);
    return            x.toString()                     +","+tohalf(y-DiamondDiagonalXY,1).toString()
		  +" "+tohalf(x+DiamondDiagonalXY,1).toString()+","+y.toString()
		  +" "       +x.toString()                     +","+tohalf(y+DiamondDiagonalXY,1).toString()
		  +" "+tohalf(x-DiamondDiagonalXY,1).toString()+","+y.toString();
}



function beeswarm(points,wtxc,muxc,boxwidth) {
  // Plots the swarm of points.
  // Avoids overlapping any points by checking using function "search_rows_above_and_below()" to search arrays wtleft, wtright, muleft, muright
  var wt_points=[],mu_points=[];

  var wtHorizPointSpacing = 8, muHorizPointSpacing = 12;  // was 12 for horizontal point spacing, but ERBB2 vs ERBB2 points overflow the boxplot width
  var tissue_count=0;
  var wtleft=[], wtright=[], muleft=[], muright=[]; // To avoid overlapping points.
  var wt_tissue_counts = {}, mu_tissue_counts = {};
  
  for (var i=1; i<points.length; i++) { // corectly starts at i=1, as points[0] is the boxplot dimensions.
    var tissue = points[i][itissue];
		

	var isWT = points[i][imutant]=="0";  // Wildtype rather than mutant.
	

if (isWT) {wt_points.push(parseFloat(points[i][iy]))}
else {mu_points.push(parseFloat(points[i][iy]))}

//    var y = tohalf(Yscreen0 + parseFloat(points[i][iy]) * yscale, 1);
    var y = Yscreen0 + parseFloat(points[i][iy]) * yscale;

    var Yi = Math.round(y / collusionTestRadius);

	var pointType = "circle", svgType = "circle";
	// Pre-Aug-2016 mutation types mapping was:
	//   1,2,3 = mutation
    //   4,5 = copy number (is one a deletion and one an amplification?)
    // Now simply:
	//   1 = mutation
    //   2 = copy number (is one a deletion and one an amplification?)    
    if (!isWT) {
	  switch (points[i][imutant]) {		  
	    case "1":
		  // pointType = "square";   svgType = "rect"; break; // Square not drawn correctly yet.
		  pointType = "diamond";  svgType = "polygon"; break;		  

	    case "2":
          pointType = "triangle"; svgType = "polygon"; break;
		// if needed a 5-point star could be another shape
	    
//	    case "3":		
//      case "4":
//	    case "5":
	    default: alert("Invalid point type: '"+points[i][imutant]+"'")
	  }
	}
	
    var e = document.createElementNS(svgNS, svgType);

	var colour = tissue_colours[tissue];
	if (typeof colour === 'undefined') {alert("Unexpected tissue '"+tissue+"'");}
	
    e.setAttribute("fill", colour);
    //e.setAttribute("stroke", colour);    // e.style.stroke=colour;
	// e.setAttribute("stroke-width", "1"); // e.style.strokewidth=1;
	// e.setAttribute("fill-opacity", "0.5");

	var x = isWT ? wtxc*xscale : muxc*xscale;  // The centerline.
		
    if (tissue in tissue_lists) {tissue_lists[tissue].push(e);}
	else {
	  tissue_lists[tissue]=[e];
	  wt_tissue_counts[tissue]=0;
	  mu_tissue_counts[tissue]=0;
	  tissue_count++;
	  }
	if (points[i][imutant]==0) {wt_tissue_counts[tissue]++}  // This is correctly outside the above
	else {mu_tissue_counts[tissue]++}

	if (isWT) { // Wild type
	    // on right side set to position one to true so won't plot two points on centre line, as point on left occupies the one position..
		for (var j=-2; j<=2; j++) {
	      if (typeof wtleft[Yi+j] === 'undefined') {if (typeof wtright[Yi+j] !== 'undefined') {alert("wtright defined Yi+'+j+' "+Yi)}; wtleft[Yi+j]=[]; wtright[Yi+j]=[true];}
		  }
				
       // find position on left nearest to centre line:
	   var xleft  = search_rows_above_and_below('wtleft:'+Yi,wtleft[Yi],wtleft[Yi-1],wtleft[Yi+1],wtleft[Yi-2],wtleft[Yi+2]);
	   var xright = search_rows_above_and_below('wtright:'+Yi,wtright[Yi],wtright[Yi-1],wtright[Yi+1],wtright[Yi-2],wtright[Yi+2]);

//       if (tissue_count % 2 == 0) // put odd numbered tissues on the left, even on right.
	   if (xleft<=xright)
	     {for (var j=wtleft[Yi].length; j<xleft; j++) {wtleft[Yi][j]=false;}; wtleft[Yi][xleft]=true; x-=xleft*wtHorizPointSpacing;} // console.log('using xleft x='+x+' wtleft[Yi].length:'+wtleft[Yi].length);
	   else 
	     {for (var j=wtright[Yi].length; j<xright; j++) {wtright[Yi][j]=false;}; wtright[Yi][xright]=true; x+=xright*wtHorizPointSpacing;} // console.log('using xright x='+x+' wtright[Yi].length:'+wtright[Yi].length);
	   	   
	   } // end of isWT
	   
	else { // is Altered (Mutant)
	   for (var j=-2; j<=2; j++) {
	     if (typeof muleft[Yi+j] === 'undefined') {if (typeof muright[Yi+j] !== 'undefined') {alert("muright defined Yi+'+j+' "+Yi)}; muleft[Yi+j]=[]; muright[Yi+j]=[true];}
	     }
	  
       // find position on left nearest to centre line:		
	   var xleft  = search_rows_above_and_below('muleft:'+Yi,muleft[Yi],muleft[Yi-1],muleft[Yi+1],muleft[Yi-2],muleft[Yi+2]);
	   var xright = search_rows_above_and_below('muright:'+Yi,muright[Yi],muright[Yi-1],muright[Yi+1],muright[Yi-2],muright[Yi+2]);

       //  if (tissue_count % 2 == 0) // put odd numbered tissues on the left, even on right.	   
	   if (xleft<=xright)
	     {for (var j=muleft[Yi].length; j<xleft; j++) {muleft[Yi][j]=false;}; muleft[Yi][xleft]=true; x-=xleft*muHorizPointSpacing;} // console.log('using xleft x='+x+' muleft[Yi].length:'+muleft[Yi].length);
	   else 
	     {for (var j=muright[Yi].length; j<xright; j++) {muright[Yi][j]=false;}; muright[Yi][xright]=true; x+=xright*muHorizPointSpacing;} // console.log('using xright x='+x+' muright[Yi].length:'+muright[Yi].length);
	   
		} // end of is Mutant
		
    // Using tohalf() and Math.round() to prevent anti-aliasing of horizontal and vertical lines, and ensure circles, triangle, diamond are drawn pixel consistently.
    switch(pointType) {
	  case "circle":
	    //add the xcentre after the above calculations 	
	    e.setAttribute("cx", tohalf(x,1).toString() ); // or: e.cx.baseVal.value =  parseFloat(points[i][2]) * xscale );	
	    e.setAttribute("cy", tohalf(y,1).toString() ); // or: e.cy.baseVal.value = parseFloat(points[i][3]) * yscale );				
	    e.setAttribute("r", PointRadius.toString()); // Firefox and IE don't use the 'r' in the 'circle' class (whereas Chrome does)  e.r.baseVal.value = PointRadius.toString(); set in the 'circle' class
		break;
	
      case "square": // rect
	    e.setAttribute("x", tohalf(x-SquareCornerXY, 1).toString());
	    e.setAttribute("y", tohalf(y-SquareCornerXY, 1).toString());
	    e.setAttribute("width", Math.round(2*SquareCornerXY).toString());
	    e.setAttribute("height",Math.round(2*SquareCornerXY).toString());
	    break;

	  case "triangle": // polygon
	    // polygons also have stroke and fill which is similar to circle: "stroke:#660000; fill:#cc3333; stroke-width: 3;"
	    // draw triangle inverted as graphics y=0 is at top of screen.
	    e.setAttribute("points", triangle_points(x,y));
	    break;
		
	  case "diamond": // path
	    e.setAttribute("points",diamond_points(x,y));
        break;
		
      //default:
				
	}
	
	var id = "c"+i.toString();
	e.setAttribute("id", id); // 'c' for circle or cell_line
	
	e.onmouseover = mouseOver;  // or: e.onmouseover = function() { myFun(this) };
	// the mouseenter event, the mouseover event triggers if a mouse pointer enters any child elements as well as the selected element. The mouseenter event is only triggered when the mouse pointer enters the selected element. 
	e.onmouseout = mouseOut;
	
	//evt.target.setAttribute('opacity', '0.5');"
	svg.appendChild(e);
    }
    
   create_legend_table(wt_tissue_counts,mu_tissue_counts);
}


function create_legend_table(wt_tissue_counts,mu_tissue_counts) {
    // Creates the tissue legend table, with totals and check-boxes to show/hide points.
	var legend_thead = '<thead><tr><th rowspan="2">Show</th><th rowspan="2">Tissue</th><th colspan="3">Cell lines</th></tr><tr style="font-size: 95%"><th>Wild type</th><th>Altered</th><th>Total</th></tr></thead>';
  	
	var legend_tbody='<tbody>';
	var wt_total=0, mu_total=0;
    for (tissue in tissue_lists) {
	  var colour = tissue_colours[tissue];
	  
//	  $('head').append('<style type="text/css">.'+tissue+'_tooltip{background:'+colour+';}</style>'); // add the style to use later for the tooltips background colour.
	  
      if (tissue_lists[tissue].length != wt_tissue_counts[tissue]+mu_tissue_counts[tissue]) {alert("ERROR: Tissue count mismatch for tissue: '"+tissue+"'")} // Just to check my script is working correctly
	  
	  if (wt_tissue_counts[tissue]==0) {wt_tissue_counts[tissue]='<i>'+wt_tissue_counts[tissue].toString()+'</i>'} // To put italics on the zeros
	  else {wt_total+=parseInt(wt_tissue_counts[tissue])}
	  if (mu_tissue_counts[tissue]==0) {mu_tissue_counts[tissue]='<i>'+mu_tissue_counts[tissue].toString()+'</i>'}
	  else {mu_total+=parseInt(mu_tissue_counts[tissue])}
	  
	  legend_tbody += '<tr><td id="td_'+tissue+'" style="background-color:'+colour+'"><input type="checkbox" id="cb_'+tissue+'" checked/></td>'
	   + '<td>'+histotype_display(tissue)+'</td>'
	   + '<td>'+wt_tissue_counts[tissue]+'</td>'
	   + '<td>'+mu_tissue_counts[tissue]+'</td>'
	   + '<td>'+tissue_lists[tissue].length+'</td></tr>';
	  }
    legend_tbody+='</tbody>';

	var all_button = '<input input type="button" id="all_checkboxes" value="All" style="padding: 2px;" onclick="tissue_checkboxes(\'all\');">';
	var none_button = '<input input type="button" id="none_checkboxes" value="None" style="padding: 2px;" onclick="tissue_checkboxes(\'none\');">';
	
    // Disabled the "toggle" button:
    // var toggle_button = '<br/><input input type="button" id="toggle_checkboxes" value="Toggle" style="font-size: 90%" onclick="tissue_checkboxes(\'toggle\');">';	
    // var legend_tfoot = '<tfoot><tr><td>'+all_button+none_button+toggle_button+'</td>' + ......
	
	var legend_tfoot = '<tfoot><tr><td style="padding: 1px;">'+all_button+none_button+'</td>'
	 + '<td>Totals:</td><td>'+wt_total+'</td>'
	 + '<td>'+mu_total+'</td>'
	 + '<td>'+(wt_total+mu_total)+'</td></tr></tfoot>';
	  // The onchange event should also work with keyboard input, whereas onclick is only listens for mouse clicks.
		  
	$("#legend_table").html( legend_thead + legend_tbody + legend_tfoot );
	
	if ( (wt_total+mu_total) != points.length-1) {alert("cellline_count mismatch: "+(wt_total+mu_total)+" != "+points.length-1);}  // The -1 is because point[0] stores the cell_count (before subtracting NA_total), ymin,ymax, etc
	
	// The inline onchange="..." tag doesn't pass the event in all browsers, which is needed, so instead attach these events using javascript:
    for (tissue in tissue_lists) {
		// showhide_cell_clicked:
		var e = document.getElementById("td_"+tissue);
		e.onclick=showhide_cell_clicked;
		e.onmouseover = tissue_legend_Over;
	    e.onmouseout  = tissue_legend_Out;
		
		document.getElementById("cb_"+tissue).onchange=showhide_tissue;	
		}

}


function add_tooltips() {
  // Add the tooltips to the SVG points and the driver info text section of the boxplot.
  $("#mysvg, #boxplot_driver_details, #ncbi_summary_showhide_link, #boxplot_target_links").tooltip({  // was $(document).tooltip(....
    items: "circle, rect, polygon, [data-gene], [data-link]",
	position: { my: "left+28 center", at: "center center+10" }, // at: "right center" }
	show: false, // instead of animated show/hide: { effect: "", duration: 0, delay: 0}, see: http://webduos.com/tooltip-using-jquery-ui-library/#.Vvb48uKLSih
	hide: false, 
    // tooltipClass: "custom-tooltip-styling", // doesn't work :(
	content: function(callback) {
	  var element = $( this );
      if ( element.is( "circle" ) || element.is( "rect" ) || element.is( "polygon" )) {
	    var id = element.attr("id");
		if ((typeof id === "undefined") || (id.substring(0,1)!='c')) {return "";} // As can be a 'rect' that forms the boxplot box.
        var i = parseInt(id.substring(1)); // remove the starting 'c'
		
        var tissue = points[i][itissue];
		var mutant = points[i][imutant];

        var mutant_type='';
        
        // Pre-August-2016 mutant codes:
		// if ((mutant=='1') || (mutant=='2') || (mutant=='3')) {mutant_type="Mutation (type "+mutant+")<br/>";}
		// else if ((mutant=='4') || (mutant=='5')) {mutant_type="Copy number (type "+mutant+")</br>"}

		if      (mutant=='0') {mutant_type="Wild type<br/>";}
		else if (mutant=='1') {mutant_type="Mutation (type "+mutant+")<br/>";}
		else if (mutant=='2') {mutant_type="Copy number (type "+mutant+")</br>"}
		else {mutant_type="Unexpected mutant_type (type "+mutant+")</br>"}
		
        // To add the mutation type, use: +(mutant!="0" ? "MutantType....<br/>" : "")
        return '<b>'+points[i][icellline]+'</b><br/>'+mutant_type+histotype_display(tissue)+'<br/>Z-score: '+points[i][iy]; // '<br/>y: '+y+'<br/>Yi: '+Yi+
	    }
      else if ( element.is( "[data-link]" ) ) {
	      return element.attr("data-link");
        }		
      else if ( element.is( "[data-gene]" ) ) { // To display the target genes in the boxplot_title.
        var gene_name = element.attr("data-gene");  // was: = element.text();
		if (gene_name in gene_info_cache) {
			var result = format_gene_info_for_tooltip(gene_info_cache[gene_name]);
			callback(result);
			}
		else {
            var url = global_url_gene_info_for_mygene.replace('mygene',gene_name);
            $.ajax({
              url: url,
              dataType: 'json', 
            })
            .done(function(data, textStatus, jqXHR) {  // or use .always(...)
              if (data['success']) {
			  	gene_info_cache[gene_name] = data; // cache to retrieve faster next time.
			    result = format_gene_info_for_tooltip(data);
			    callback(result);
				}
			  else {callback("Error: "+data['message'])}
		    })
		    .fail(function(jqXHR, textStatus, errorThrown) {
			  callback("Ajax Failed: '"+textStatus+"'  '"+errorThrown+"'");
            })
		  }
        }
		
	},
	
  });
}



function svg_rect(xcenter,width, ylower,yupper, id, e) {
    // Creates (or update existing rect if parameter 'e' is already defined) the SVG boxes for the boxplot

    if (typeof e == "undefined") {
	    e = document.createElementNS(svgNS,"rect");
	    svg.appendChild(e); // or: document.documentElement.appendChild(elem); // console.log("SVGrect made");
	    }
	else if (!(e instanceof SVGRectElement)) {alert("svg_rect(): expected 'rect' for existing elem, but got: "+e.tagName)}
		
	e.setAttribute("x", tohalf((xcenter-0.5*width)*xscale, 1) );
	var y = tohalf(Yscreen0 + yupper*yscale, 1);

	e.setAttribute("y", y);  // Note: box drawn upside down, as screen zero is top left.
    e.setAttribute("width", Math.round(width*xscale) );	
	e.setAttribute("height", Math.round( (Yscreen0 + ylower*yscale) - y) );	// yscale is -ive. Slightly more accurate than (ystats[1]-ystats[3])*yscale, as ystats[3]*yscale has been moved slightly by the tohalf.
	e.setAttribute("id",id);
	
	//e.setAttribute("fill", "none"); // set by the CSS
	//e.setAttribute("stroke", "black");
	//e.setAttribute("stroke-opacity", "1.0");
	//e.setAttribute("stroke-width", strokewidth);

	return e;
	}

	
function svg_line(x1,y1,x2,y2,strokewidth,dashed,colour, e) {
    // Creates (or update existing line if parameter 'e' is already defined) the SVG lines for the boxplot

	if (typeof e == "undefined") {
	    e = document.createElementNS(svgNS,"line"); // console.log("SVGline made");
		svg.appendChild(e);
	    }
    else if (!(e instanceof SVGLineElement)) {alert("svg_line(): expected 'line' for existing elem, but got: "+e.tagName)}	
	
    var isVertical = x1==x2;
    var isHorizontal = y1==y2;
	
	// For sharp lines, best to have position at 0.5 if thinkness is 1px, then won't need antialiasing.
	var x = isVertical ? tohalf(x1*xscale, strokewidth) : x1*xscale;
	e.setAttribute("x1", x);
	e.setAttribute("x2", (isVertical ? x : x2*xscale) );  // otherwise tohalf(x2*xscale) which is same as above.
    //if (isVertical) {console.log("tohalf x"+x2+" => "+x);}

	var y = isHorizontal ? tohalf(Yscreen0 + y1*yscale, strokewidth) : Yscreen0 + y1*yscale;

	e.setAttribute("y1", y);	
	e.setAttribute("y2", (isHorizontal ? y : Yscreen0 + y2*yscale) );
	
	e.setAttribute("stroke", colour); // as black is default in the CSS
	e.setAttribute("stroke-width", strokewidth);
	if (dashed) {e.setAttribute("stroke-dasharray", "6,3");} // se: http://www.w3schools.com/svg/svg_stroking.asp

	return e;
	}
	
	
function svg_text(x,y,size,vertical,text, e) {
	//  Creates (or update existing text if parameter 'e' is already defined) the SVG text for the boxplot
	
	// To better position text, could use:  style="text-anchor: middle" so uses text centre for positioning text
	if (typeof e == "undefined") {
		e = document.createElementNS(svgNS,"text");
        svg.appendChild(e);
		}
    else if (!(e instanceof SVGTextElement)) {alert("svg_text(): expected 'text' for existing elem, but got: "+e.tagName); }	
	
    var xscreen = x*xscale;
	e.setAttribute("x", xscreen);
	var yscreen = Yscreen0 + y*yscale;
	e.setAttribute("y", yscreen);
	e.setAttribute("font-size", size);
	if (vertical) {e.setAttribute("transform", "rotate(-90,"+xscreen+","+yscreen+")");}  // transform="rotate(30 20,40)" See: http://stackoverflow.com/questions/11252753/rotate-x-axis-text-in-d3
	//e.setAttributeNS(null,"stroke", colour);
    e.appendChild(document.createTextNode(text));
	return e;
	}

	
function boxplot(xcenter,width,ystats, rect_id, elms) {
    // Creates the boxplot rectangle and whiskers and returns the array of created SVG elements.
	if (ystats.length < (iupperwhisker+1)) {alert("*** Boxplot ystats length="+ystats.length+" but should have length >= "+(iupperwhisker+1));	return [];}
	return [
      svg_rect(xcenter,width, ystats[ilowerhinge],ystats[iupperhinge], rect_id, elms[0]), // box lower_hinge to upper_hinge
	  svg_line(xcenter-0.25*width,ystats[ilowerwhisker], xcenter+0.25*width,ystats[ilowerwhisker], "1px", false, "black", elms[1]), // horizontal lower_whisker line
	  svg_line(xcenter,ystats[ilowerwhisker], xcenter,ystats[ilowerhinge], "1px", true, "black", elms[2]),  // vertical line from lower_whisker to rect lower_hinge dashed line
	  svg_line(xcenter-0.5*width,ystats[imedian], xcenter+0.5*width,ystats[imedian], "3px", false, "black", elms[3]), // horizontal median line
	  svg_line(xcenter,ystats[iupperhinge], xcenter,ystats[iupperwhisker], "1px", true, "black", elms[4]),  // vertical line from upper_whisker to rect upper_hinge dashed line
	  svg_line(xcenter-0.25*width,ystats[iupperwhisker], xcenter+0.25*width,ystats[iupperwhisker], "1px", false, "black", elms[5]) // horizontal upper_whisker line
	];
    }


function update_boxplots(check_tissue_checkbox_is_checked) {
  // Sets or updates the boxplot rectangle and whiskers when tissues are made hidden or made visible by clicking the checkboxes in the legend table.
  
  var wt_points=[],mu_points=[];	
  for (var i=1; i<points.length; i++) { // corectly starts at i=1, as points[0] is the boxplot dimensions.
	
    // Check if that tissue's checkbox is checked (so point is visible).
    if (check_tissue_checkbox_is_checked) { // When drawing the initial full boxplot, don't need to check if tissue visible
      var tissue = points[i][itissue];
	  var checkbox = document.getElementById('cb_'+tissue);
	  if (! checkbox.checked) {continue}
      // Could alternatively check if point itself is visible:
      //    if (document.getElementById("c"+i.toString()).getAttribute("visibility")=="hidden") {continue}   // "c" for circle or cell_line.  // otherwise: "visible"	  
	  }

	var isWT = points[i][imutant]=="0";  // Wildtype rather than mutant.
    if (isWT) {wt_points.push(parseFloat(points[i][iy]))}
    else {mu_points.push(parseFloat(points[i][iy]))}
    }	
  	
  // The boxplot lines and rectangles are stored in two global arrays, so can adjust position later:
  wt_boxplot_elems = boxplot( wtxc, boxwidth, boxplot_stats(wt_points), "wtbox", wt_boxplot_elems ); // When check_tissue_checkbox_is_checked is true, don't need: "wt_boxplot_elems = boxplot(...)" as element ids are unchanged, just their positions are changed.
  mu_boxplot_elems = boxplot( muxc, boxwidth, boxplot_stats(mu_points), "mubox", mu_boxplot_elems );

  return true;
  }


function set_tissue_visibility(tissue,visible, updateboxplots) {
	for (var i=0; i<tissue_lists[tissue].length; i++) {
	    var elem = tissue_lists[tissue][i];
	    elem.setAttribute("visibility", visible ? "visible":"hidden");
	    }
	if (updateboxplots) {update_boxplots(true);} // To move the boxplots to match the changes. But if clicked All/None/Toggle buttons then update at end rather than for each tissue.
	}

	

function showhide_cell_clicked(e) {  // elem can be a 'td' or checkbox.
  // Shows or hides the points for the tissue, based on the tissue check-box checked/unchecked status
  // Is called if the check-box is clicked (which also called the enclosing td cell click event)
  
  // When the checkbox is clicked: IE seems to call this checkbox code first then the 'td' click event, whereas Chrome and Firefox seem to call the 'td' event first, then the checkbox event.
  // Not using event as not passed in Firefox when inline onclick="" used
  e = e || window.event;  // Need: window.event for IE <=8
  // e.preventDefault(); // should cancel the also click cell event
  // e.stopPropagation(); // To stop propagation to parent element. ie. stops the event from bubbling up the event chain.
  // see: http://stackoverflow.com/questions/5963669/whats-the-difference-between-event-stoppropagation-and-event-preventdefault
  // e.cancelBubble  // for IE<=8 
  // or maybe use jquery e.stopPropagation...

  var elem = e.target || e.srcElement;
  //console.log('showhide_cell: '+elem.id);
  if (elem.id.substring(0,3)=='cb_') { // Ignoring this click event from the check_box itself, as this is event is called twice (by outer td element and check_box)
        // console.log('leaving showhide_cell');
	    return true; // Need to return true so will be handled by the checkbox click event (showhide_tissue(e)).
	}
  var tissue = elem.id; /// the checkbox name is the tissue.
  tissue=tissue.substring(3); // remove the 'td_' to leave the tissue name

  // window.event.preventDefault(); // should cancel the click cell event
  var checkbox = document.getElementById('cb_'+tissue);

  checkbox.checked = ! checkbox.checked; // Toggle checked state, but doesn't fire the onchanged event.
  set_tissue_visibility(tissue, checkbox.checked, true)

  return false;
  }


function showhide_tissue(e) {
  // Shows or hides the points for the tissue, based on the tissue check-box checked/unchecked status
  // Is called when the td cell (outside the checkbox) is clicked, and when the checkbox is clicked.
  
  // see: http://stackoverflow.com/questions/24578837/remove-or-hide-svg-element

  e = e || window.event;  // Need: window.event for IE <=8
  // e.preventDefault(); // should cancel the also click cell event
  // e.stopPropagation(); // To stop propagation to parent element. ie. stops the event from bubbling up the event chain.
  // e.cancelBubble  // for IE<=8 
  // or maybe use jquery e.stopPropagation...

  // if (!e) e = window.event;
  //    e.cancelBubble = true;
  //    if (e.stopPropagation) e.stopPropagation();
  //}

  var checkbox = e.target || e.srcElement;
  var tissue = checkbox.id.substring(3); /// the checkbox name is the 'cb_'+tissue.

  set_tissue_visibility(tissue, checkbox.checked, true);
  return false; // does true mean event was handled?
  }
   

function tissue_checkboxes(action) {
    // Called when the All or None (or Toggle) buttons are clicked
    for (tissue in tissue_lists) {
   	  var checkbox = document.getElementById('cb_'+tissue);

	  switch(action) {
	    case 'all': checkbox.checked = true; break; 
	    case 'none': checkbox.checked = false; break;
  	    case 'toggle': checkbox.checked = ! checkbox.checked; break; // Toggle checked state, but doesn't fire the onchanged event.
		default: alert('Invalid action for tissue_checkboxes(): "'+action+'"');
        }
	  set_tissue_visibility(tissue, checkbox.checked, false); // 'false' as will update boxplot once at the end after this loop, instead of doing it for each tissue.
		
      }
	update_boxplots(true);  
    }

	
	
function download_boxplot(download_type, driver, target, histotype, study_pmid) {   
  // Downloads the boxplot as image file. 
  // download_type can be 'png', 'svg', or 'csv'.   
  // Uses the "svg_todataurl"
   
  var filename = driver+"_"+target+"_"+histotype+"_pmid"+study_pmid+"."+download_type;   
   
  switch (download_type) {
	case 'svg':
	  show_message("download_SVG_boxplot", "Downloading..."); // maybe warn if browser is IE
	  mysvg.toDataURL("image/svg+xml", {		  
	    callback: function(data) {download_data(data,filename)}
      });
	  break;
	    		
    case 'png':
	  show_message("download_png_boxplot", "Downloading..."); // maybe warn if browser is IE
      var ua = window.navigator.userAgent;  // if ($.browser.msie) {alert($.browser.version);}	
      var ie = ((ua.indexOf('MSIE ') > 0) || (ua.indexOf('Trident/')>0));  // 'MSIE' for IE<=10; 'Trident/' for IE 11; || (ua.indexOf('Edge/')>0) for Edge (IE 12+)
	  var render = ie ? "canvg" : "native";  // Using "canvg" for IE, to avoid the SECURITY_ERR in IE: canvas.toDataURL(type)	
      // The following works in IE 11 (and probably in IE 10 which introduced msToBlob()):
      mysvg.toDataURL("canvas", {	// "canvas" was added to return a canvas for IE msToBlob().
  	    callback: function(canvas) {
			if (canvas.msToBlob) { //for IE  
              window.navigator.msSaveBlob(canvas.msToBlob(), filename); // msToBlob() returns canvas as a PNG image
            }
	        else { //other browsers
              download_data(canvas.toDataURL("image/png",1), filename);
            }
		},
		renderer: render 
      });
	  break;

    case 'csv':
      // Download CSV file from server, as client side download not working.
	  saveTextAsFile(boxplot_csv,filename,"text/csv")  // or "text/plain" or "text/json"
      break;
  
	default: alert("Invalid download_type: '"+download_type+"'")
	}
  }

   

function download_data(data, filename) {
    // This doesn't work in earlier browsers, as 'download' attribute is only HTML5.
    // And used msSaveBlob in IE in download_boxplot()
    var a = document.createElement('a');
    a.setAttribute('href', data);
    a.setAttribute('target', '_blank');	// or: 	a.target = '_blank';
    a.setAttribute('download', filename);	
	document.body.appendChild(a);    // as link has to be on the document - needed in Firefox, etc.
    if(a.click) {a.click();}
    else if(document.createEvent) {  // For Safari earlier versions, but the 'download' attribute might be missing or try jquery: $(a).click()
        var eventObj = document.createEvent('MouseEvents');
        eventObj.initEvent('click',true,true);
        element.dispatchEvent(eventObj);
	    // see: http://stackoverflow.com/questions/12925153/jquery-click-works-on-every-browser-but-safari		
        }
	
    document.body.removeChild(a);
    }
	

	
function saveTextAsFile(data,filename,mimetype) {
    // Creates an html <a> download link, clicks it then removes the link. Needs html5 for the 'download' attribute.
	// mimetype should be, eg: "text/csv" or "text/plain"
	// Based on: http://stackoverflow.com/questions/35148578/download-a-text-file-from-textarea-on-button-click

    var textFileAsBlob = new Blob([data], { type: mimetype }); // create a new Blob (html5 magic) that conatins the data from your form field
    var a = document.createElement("a");
    a.download = filename;
    a.innerHTML = "My Hidden Link";
    // allow code to work in webkit & Gecko based browsers without the need for a if / else block.
    window.URL = window.URL || window.webkitURL;    
    a.href = window.URL.createObjectURL(textFileAsBlob); // Create the link Object.
    // when link is clicked call a function to remove it from the DOM in case user wants to save a second file.
    a.onclick = destroyClickedElement;
    a.style.display = "none";         // make sure the link is hidden.
    document.body.appendChild(a);  // add the link to the DOM
    a.click();      // click the new link
    }

function destroyClickedElement(event) {
    // Remove the link from the DOM
    document.body.removeChild(event.target);
    }



  
function fetch_data(driver,target,histotype,study_pmid) {
    // Fetches data from pythonanywhere server using AJAX call.
    
	boxplot_csv=''; // or undefined.  This var is global to indicate that no data has been retrieved yet.
				
	var boxplot_key = driver+'_'+target+'_'+histotype+'_'+study_pmid;
	if (boxplot_key in boxplot_cache) {
			draw_svg_boxplot(driver, target, boxplot_cache[boxplot_key]);
	  }
	else {
		
	  var dataformat='jsonplotandgene';  // or 'jsonplot'	
	  var url = global_url_for_boxplot_data.replace('myformat',dataformat).replace('mydriver',driver).replace('mytarget',target).replace('myhistotype',histotype).replace('mystudy',study_pmid);
	  // eg:  "http://localhost:8000/gendep/get_boxplot_csv/"+driver+"/"+target+"/"+histotype+"/"+study_pmid+"/";
	    
      $.ajax({
        url: url,
		cache: true, // is the default but requires webserver to set headers (ETag or Last-Modified) to allow browser caching of the response.
        dataType: 'json',   // 'text',  // use 'text' as there is no specific 'csv' option for this.
        })
        .done(function(data, textStatus, jqXHR) {  // or use .always(...)
            if (data['success']) {
			  if (dataformat=='jsonplotandgene') {
				if ('gene_info' in data) {gene_info_cache[target] = data['gene_info'];} // cache to retrieve faster next time - will also include the ncbi_summary, which isn't in the gene_info returned for the onhoover tooltips.
				else {alert("AJAX data didn't contain the 'gene_info'");}
			    }
			  boxplot_cache[boxplot_key] = data['boxplot'];
			  draw_svg_boxplot(driver, target, data['boxplot']);
			  }
			else {alert("ERROR: "+data['message']);}
		})
		.fail(function(jqXHR, textStatus, errorThrown) {
		    alert("Ajax Failed: '"+textStatus+"'  '"+errorThrown+"'");
        });
	  }
	return true; // return true to the fancybox afterLoad, so that the fancy box content is shown.		
    }



function showhide_ncbi_summary() {
	if ($("#boxplot_ncbi_summary").css("display") == "none") {
      $("#boxplot_ncbi_summary").css("display", "block"); // is a paragraph so display as block, rather than inline.
	}
	else {
      $("#boxplot_ncbi_summary").css("display", "none");
	}  
}	


function add_target_info_to_boxplot(target)	{
  // Adds details about the target gene to the title for the boxplot.
  if (typeof target === 'undefined') {alert("target gene is undefined"); return false;}

  var target_info;
  if (target in gene_info_cache) {target_info = gene_info_cache[target];}
  else {alert("target gene '"+target+"' NOT in gene_info_cache"); return false;}
  
  if (typeof target_info === 'undefined') {$("#target_details").html("Unable to retrieve synonyms and external links for this '"+target+"' gene"); return false;}

  if (target !== target_info['gene_name']) {alert("Target name:"+target+" != target_info['gene_name']:"+target_info['gene_name'] ); return false;}
  
  var target_full_name  = '<i>'+target_info['full_name']+'</i>';
  var target_synonyms   = target_info['synonyms'];
  if (target_synonyms !== '') {target_synonyms = ' | '+target_synonyms;}

  var target_details = target+'</b>'+target_synonyms+', '+target_full_name
	 
  var ncbi_summary = target_info['ncbi_summary']; // Not all genes have a summary in Entrez  
  if ((typeof ncbi_summary !=="undefined") && (ncbi_summary!=="")) {
	target_details += ' <a id="ncbi_summary_showhide_link" href="javascript:void(0);" onclick="showhide_ncbi_summary();" data-link="Show Entrez gene summary">(Gene Description)</a>'; // The ncbi_summary_link
	
    $("#boxplot_ncbi_summary").html('<b>Entrez summary for '+target+':</b> '+ncbi_summary);
  }

  $("#boxplot_target_details").html(target_details);
	
  var target_links = target+' Links: '+gene_external_links(target_info['ids'], '|', false); // returns html for links to entrez, etc. The 'false' means returns the most useful selected links, not all links.
    
  $("#boxplot_target_links").html(target_links);

  return true;
  }


function set_previous_next_boxplot_buttons(jq_button, mtext, dependency_td) {
  if (dependency_td===null) {
    jq_button.attr('onclick','').html("No "+mtext+"</br>boxplot").attr('disabled', true);
    }
  else {	  	  
    jq_button
     .attr('onclick',  dependency_td.getAttribute('onclick'))
	 .html(mtext+" boxplot<br/>"+dependency_td.getAttribute('data-gene'))
	 .attr('disabled', false);
    }
  }  


  
function show_svg_boxplot_in_fancybox(dependency_td_id, driver, target, histotype, study_pmid, wilcox_p, effect_size, zdelta_score,  target_variant) {
  // Displays the boxplot in the fancybox popup window
  
  drawing_svg = false;
  boxplot_csv = '';
  fetch_data(driver,target,histotype,study_pmid);	  // is asynchronous AJAX call. // removed parameter: target_variant

  if (!svg_fancybox_loaded) {  // so this function was called by clicking on dependency table cell, rather than by Previous/Next boxplot button.

    // Need the [CDATA[ tag as SVG can contain extra '<' characters that can confuse HTML parsers.
    var mycontent = '<table align="center" style="padding:0; border-collapse: collapse; border-spacing: 0; border-bottom: solid 1px black;">'
      + '<tr><td rowspan="2" style="padding:0;">'
      + '<svg id="mysvg" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="'+svgWidth.toString()+'" height="'+svgHeight.toString()+'">'
      + '<style type="text/css"><![CDATA['
      + '  line{stroke-opacity: 1.0;}'
      + '  rect{fill: none; stroke: black; stroke-width: 1px; stroke-opacity: 1.0;}'
      + '  circle {fill-opacity: 0.9; stroke-width: 1px; stroke: black;}'
      + '  polygon {fill-opacity: 0.9; stroke-width: 1px; stroke: black;}'
      + '  polygon.bold  {stroke-width: 5px; stroke: black;}'
      + '  polygon:hover {stroke-width: 5px; stroke: black;}'
      + '  circle.bold   {stroke-width: 5px; opacity: 0.9; stroke: black;}'	  
      + '  circle:hover  {stroke-width: 5px; opacity: 0.9; stroke: black;}'	  
      + '  text {font-family: sans-serif; word-spacing: 2; text-anchor: middle;}'
      + ']]></style>'
      + '<rect id="background_rect" x="0" y="0" width="'+svgWidth.toString()+'" height="'+svgHeight.toString()+'" style="fill:white;stroke-width:0;fill-opacity:1.0;"/>'
      + 'Sorry, your browser does not support inline SVG.'
      + '</svg>'
      + '</td><td style="vertical-align:middle; padding:0;">'
      + '<table id="legend_table" class="tablesorter"></table>'
      + '<table id="boxplot_download_buttons_table" style="padding:0; border-collapse: collapse; border-spacing: 0;"></table>'
      + '<table id="legends_download_buttons_table" style="padding:0; border-collapse: collapse; border-spacing: 0;"></table>'
      + '</td><tr><td style="vertical-align:bottom; text-align:center; padding:0;">'
      + '<table id="next_prev_boxplot_buttons_table" style="padding:0; border-collapse: collapse; border-spacing: 0;"></table></td></tr>'
      + '</td></tr></table>';


    var plot_title = '<p id="boxplot_driver_details" style="margin-top: 2px; margin-bottom: 5px; text-align: center; line-height: 1.3"></p>'
      + '<p id="boxplot_target_details" style="margin-bottom: 0; margin-top: 7px; text-align: center; line-height: 1.3;"></p>'
      + '<p id="boxplot_ncbi_summary" style="display:none; font-size:90%; margin-top:0; margin-bottom:0;"></p>'
      + '<p id="boxplot_target_links" style="margin-top: 1px; margin-bottom: 0; text-align: center;"></p>';

		
    $.fancybox.open({
		preload: 0, // Number of gallary images to preload
		minWidth: 800, // was 900 but too wide of older monitors and projectors.
		minHeight: 510,
		width: 820,  // as boxplot is 500 + legend table of 317 = 817px
		height: 510,
		// width: '100%',
		// height: '100%',
		padding: 5, // To reduce the border arround box from the 15px default, to fit narrower screens/projectors. (padding is the space between image and fancybox, default 15)
		// margin:  2, 	// is space between fancybox and viewport, default 20
		autoSize: false, // true, //false,  // true,  // false, // otherwise it resizes too tall.
		aspectRatio: true,
		// fitToView: true,
		autoCenter: true,
		arrows: true, // false, (next/prev arrows)
		loop : false,
		closeEffect : 'none',
		helpers: {
        	title: {
            	type: 'inside'
	        },
    	    overlay: {
        	    showEarly: true  // false  // Show true, as otherwise incorrectly sized box displays before images have arrived.
	        }
    	},
		type: 'inline', // 'html', // 'iframe', // 'html',
		content: mycontent,
		title: plot_title, 
		// href: url_boxplot,
	
		// "..afterShow would make way more sense to use if you plan on adding any events, whereas afterLoad fires as soon as it's ready to load before it shows anything at all""
		afterShow: function(current, previous) {  // Otherwise might draw before fancybox is ready 	
			svg_fancybox_loaded = true;
			draw_svg_boxplot(driver,target,boxplot_csv)   // ,histotype, study_pmid, wilcox_p, effect_size, zdelta_score,  target_variant);
			return true;
		},		
		afterClose: function() {  // There is also a "beforeClose()" event
			remove_existing_svg_elems(); // Could reuse these same elements for the next boxplot - but is svg is recreated?
			svg_fancybox_loaded=false;
		}	
	});

    // Buttons to download the boxplot as PNG image or CSV data file:
    var download_csv_click = "show_message('download_csv_boxplot', 'Downloading...');";    
    $("#boxplot_download_buttons_table").html('<tr><td style="font-size:80%">Download boxplot as:</td>'
      + '<td><input type="button" id="download_png_boxplot" value="PNG image" data-value="PNG image" style="font-size:80%"/></td>'
      + '<td><form id="download_boxplot_form" method="get">'
      + '<input type="submit" id="download_csv_boxplot" value="CSV file" data-value="CSV file" onclick="'+download_csv_click+'"/ style="font-size:80%"></form>'
      + '</td></tr>');    

    // Buttons to download the legend table as PNG image - for selected or all tissues:
    $("#legends_download_buttons_table").html('<tr><td style="font-size:80%">Download legend for:</td>'
      + '<td><input type="button" id="download_selected_legend" value="Selected tissues" data-value="Selected tissues" onclick="download_legend(\'selected\');" style="font-size:80%; padding: 1px;"/></td>'
      + '<td><input type="button" id="download_all_legend" value="All tissues" data-value="All tissues" onclick="download_legend(\'all\');" style="font-size:80%; padding: 1px;"/></td>'
      + '</tr>');

    if (SHOW_NEXT_PREV_BUTTONS) {
      // Buttons for moving to the Next or Previous boxplot, or Closing the fancybox:
      // Changed to using the <button>....</button> tags instead of <input type="button"... /> as can include line breaks inside the button>, eg: <button> I see this <br/>is a long <br/> sentence here.</button>
      // Can even put images inside these button tags text.
      $("#next_prev_boxplot_buttons_table").html(
        '<tr>' 
      + '<td style="padding: 1px 5px;"><button id="previous_boxplot_button" data-value="Previous boxplot" style="font-size:75%;"></button></td>'
      + '<td style="padding: 1px 5px;"><button id="close_boxplot_button" data-value="Close boxplot" onclick="$.fancybox.close();" style="font-size:75%;">Close</br>boxplot</button></td>'
      + '<td style="padding: 1px 5px;"><button id="next_boxplot_button" data-value="Next boxplot" style="font-size:75%;"></button></td>'
      + '</tr>'  
      );   
    }   
   
  } // end of if (!svg_fancybox_loaded) { ....

  
  $("#boxplot_driver_details").html(
     '<b><span data-gene="'+driver+'">'+driver+'</span></b>'
	 + ' altered cell lines have an increased dependency upon'
 	 + ' <b><span data-gene="'+target+'">'+target+'</span></b></br>'
 	 + ' (p='+wilcox_p.replace('e', ' x 10<sup>')+'</sup>'
     + ' | effect size='+effect_size+'%'
     + ' | &Delta;Score='+zdelta_score
	 + ' | Tissues='+ histotype_display(histotype)
	 + ' | Source='+ study_display_shortname(study_pmid)
	 + ')'
	 );
	
  $("#download_boxplot_form").attr('action', global_url_for_boxplot_data.replace('myformat','download').replace('mydriver',driver).replace('mytarget',target).replace('myhistotype',histotype).replace('mystudy',study_pmid) );  

  var comma = "','";
  $("#download_png_boxplot").attr('onclick', "download_boxplot('png" +comma+ driver +comma+ target +comma+ histotype +comma+ study_pmid+"');" );
  
  var this_td =   svg=document.getElementById(dependency_td_id);
  
  if (SHOW_NEXT_PREV_BUTTONS) {  
    set_previous_next_boxplot_buttons($("#previous_boxplot_button"), 'Previous', previous_dependency(this_td));
    set_previous_next_boxplot_buttons($("#next_boxplot_button"),     'Next',     next_dependency(this_td));
  }

  return false; // Return false to the caller so won't move on the page
}	

