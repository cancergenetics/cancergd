// Javascript functions for CGDD web interface.
// These functions don't need any template so are static and can be stored in gendep/static
// Most are called by index.html (or by other functions within the "cgdd_functions.js" file)


function sprintf(str) {
  // A simple sprintf() function. Usage: eg: in doc ready:
  //   var msg = 'the department';
  //   $('#txt').html(sprintf('<span>Teamwork in </span> <strong>%s</strong>', msg));
  // returns empty string if variable 'msg' is undefined.

  var args = arguments,
    flag = true,
    i = 1;

  str = str.replace(/%s/g, function() {
    var arg = args[i++];

    if (typeof arg === 'undefined') {
      flag = false;
      return '';
    }
    return arg;
  });
  return flag ? str : '';
};


// As Safari 6 and IE 8 don't support performance.now(), so don't have: window.performance   From: http://jsfiddle.net/moob/1vw3ncck/
// Date.now() wasn't added to the JavaScript spec until ECMAScript 5 so this is needed for <=IE8
Date.now = Date.now || function() { return +new Date; };
window.performance = (window.performance || {
    offset: Date.now(),
    now: function now(){
        return Date.now() - this.offset;
    }
});
// Alternatively see: https://gist.github.com/paulirish/5438650



function show_message(elem_id, message, waitfor) {
    // Sets an element's text value to the message, then reset it to the original value after the waitfor seconds.
    //   elem_id: the span, div, paragraph or button to contain the message
    //   message: text or html
    //   waitfor: in milliseconds: 0 means don't clear message; undefined means clear after 3 seconds.

	var elem = document.getElementById(elem_id);
	var data_value = elem.getAttribute("data-value"); // so is a button to reset to its original text value
	// Note: If the attribute "data-value" does not exist, the return value is null or an empty string ("")

	if ((data_value !== null) && (data_value !== "")) {elem.value = message;} // for an input button.
	else {elem.innerHTML = message;}

    var timerid = "0"; // to set id to zero if no time out specified, so that any pending setTimeout won't clear this message.
	if (typeof waitfor == "undefined") {waitfor = 3000;} // default 3 seconds.
	if (waitfor > 0) {
        // Only clear message if was set by this call, as may have subsequently been set by a second click of same button by user.
        // Use an anonymous function, which works in all browsers (whereas extra parameters for timeout only work in IE9+)
		timerid = setTimeout(function(){
    	    if (elem.getAttribute("data-timerid") == timerid) {  // so only clears messages set by this particular show_message() call.
				var data_value = elem.getAttribute("data-value"); // so is a button to reset to its original text value
				if ((data_value !== null) && (data_value!=="")) {elem.value = data_value;}
				else {elem.innerHTML="";}
				}
		}, waitfor);
	  };
    elem.setAttribute("data-timerid",timerid);
  }



// The study_info() function is part of the main "index.html" template as it needs each study from the database Study table.
function study_url(study_pmid) {
    if (study_pmid.substring(0,7) === 'Pending') {href = global_url_for_mystudy.replace('mystudy', study_pmid);} // was: '/gendep/study/'+study_pmid+'/';
    else {href = 'https://www.ncbi.nlm.nih.gov/pubmed/' + study_pmid;}
    return href
}


function study_weblink(study_pmid, study) {
//	if (typeof study === 'undefined') {
		return sprintf('<a href="%s" target="_blank">%s</a>', study_url(study_pmid),study[ishortname]);
		// not displaying this now: study = study_info(study_pmid); 	// returns: short_name, experiment_type, summary, "title, authors, journal, s.pub_date"
//        }
//    return sprintf('<a class="tipright" href="%s" target="_blank">%s<span>%s</span></a>', study_url(click()), study[0], study[3] );
}

function gene_external_links(id, div, all) {
  // id : is a dictionary returned by ajax from: view.py : gene_ids_as_dictionary()
  // if 'all' is false, then shows just those links to be displayed below the boxplot images.
  // gene is a row in the Gene table
  // was previously in 'models.py'
  // Note the above sprinf() returns empty string if variable is undefined.
  // console.log("external_links ids=",id)
//links  = '<a class="tip" href="http://www.genecards.org/cgi-bin/carddisp.pl?gene='+id['gene_name']+'" target="_blank">GeneCards<span>Genecards: '+id['gene_name']+'</span></a> ';
  links  = '<a href="http://www.genecards.org/cgi-bin/carddisp.pl?gene='+id['gene_name']+'" target="_blank" title="Genecards: '+id['gene_name']+'">GeneCards</a> ';
  if (id['entrez_id'] != '') {links += div+' <a class="tip" href="https://www.ncbi.nlm.nih.gov/gene/'+id['entrez_id']+'" target="_blank">Entrez<span>Entrez Gene at NCBI: '+id['entrez_id']+'</span></a> ';}
  if (id['ensembl_id'] != '') {links += div + sprintf(' <a class="tip" href="http://www.ensembl.org/Homo_sapiens/Gene/Summary?g=%s" target="_blank">Ensembl<span>Ensembl Gene: %s</span></a> ', id['ensembl_id'], id['ensembl_id']);}
    // Ensembl_protein not needed now: if (all && (id['ensembl_protein_id'] != '')) {links += div + sprintf(' <a class="tip" href="http://www.ensembl.org/Homo_sapiens/protview?peptide=%s" target="_blank">Ensembl_protein<span>Ensembl Protein: %s</span></a> ', id['ensembl_protein_id'],id['ensembl_protein_id']);}
  // Hiding HGNC to save space: if (id['hgnc_id'] != '') {links += div + sprintf(' <a class="tip" href="http://www.genenames.org/cgi-bin/gene_symbol_report?hgnc_id=%s" target="_blank">HGNC<span>HUGO Gene Nomenclature Committee: %s</span></a> ', id['hgnc_id'], id['hgnc_id']);}
  if (all) {
    // No loner showing VEGA: if (id['vega_id'] != '') {links += div + sprintf(' <a class="tip" href="http://vega.sanger.ac.uk/Homo_sapiens/Gene/Summary?g=%s" target="_blank">Vega<span>Vertebrate Genome Annotation: %s</span></a> ', id['vega_id'], id['vega_id']);}
    if (id['omim_id'] != '') {links += div + sprintf(' <a class="tip" href="http://www.omim.org/entry/%s" target="_blank">OMIM<span>Online Mendelian Inheritance in Man: %s</span></a> ', id['omim_id'], id['omim_id']);}
    links += div + sprintf(' <a class="tip" href="http://www.cancerrxgene.org/translation/Search?query=%s" target="_blank">CancerRxGene<span>CancerRxGene search: %s</span></a> ', id['gene_name'],id['gene_name']);
	}
  links += div + sprintf(' <a class="tip" href="http://www.cbioportal.org/ln?q=%s" target="_blank">cBioPortal<span>cBioPortal for Cancer Genomics: %s</span></a> ', id['gene_name'],id['gene_name']);
  if (id['cosmic_id'] != '') {links += div + sprintf(' <a class="tip" href="http://cancer.sanger.ac.uk/cosmic/gene/analysis?ln=%s" target="_blank">COSMIC<span>Catalogue of Somatic Mutations in Cancer: %s</span></a> ', id['cosmic_id'],id['cosmic_id']);}
  if (id['uniprot_id'] != '') {links += div + sprintf(' <a class="tip" href="https://cansar.icr.ac.uk/cansar/molecular-targets/%s/" target="_blank">CanSAR<span>CanSAR: %s</span></a> ', id['uniprot_id'],id['uniprot_id']);}  // CanSAR uses UniProt ids
  if (all && (id['uniprot_id'] != '')) {links += div + sprintf(' <a class="tip" href="http://www.uniprot.org/uniprot/%s" target="_blank">UniProtKB<span>UniProtKB: %s</span></a> ', id['uniprot_id'],id['uniprot_id']);}
  if (id['entrez_id'] != '') {links += div + ' <a class="tip" href="http://www.genomernai.org/genedetails/' +id['entrez_id'] + '" target="_blank">GenomeRNAi<span>GenomeRNAi - phenotypes from RNA interference</span></a> ';}  // as links are eg:  http://www.geneomernai.org/genedetails/2064
  if (id['ensembl_id'] != '') {links += div + ' <a class="tip" href="https://www.targetvalidation.org/target/' +id['ensembl_id'] + '" target="_blank">Open Targets<span>Open Targets</span></a> ';}  // as links are eg:https://www.targetvalidation.org/target/ENSG00000047936

  return links;
}



function show_search_info(data) {
  var qi = data['query_info']; // best to test if this exists in the query

  var search_by = qi['search_by'];
  $("#gene_search_by").html(search_by=='target' ? 'Target' : 'Driver');
  var gene = qi['gene_name'];
  var entrez_id = qi['gene_entrez'];  // global_selected_entrez_id

  if (gene != global_selected_gene) {alert("ERROR: query returned search by gene("+gene+") != global_selected_gene("+global_selected_gene+")")}
  $("#gene_name").html(gene);
  $("#gene_synonyms").html(qi['gene_synonyms']);
  $("#gene_alteration_considered").html(qi['gene_alteration_considered']);
  $("#gene_full_name").html(qi['gene_full_name']);

  global_selected_gene_info = data['gene_ids'];
  if (!(gene_name in gene_info_cache)) {gene_info_cache[gene_name] = data['gene_ids'];} // Store for later.

  $("#gene_weblinks").html(gene_external_links(data['gene_ids'], '|', true));

  var histotype_name = qi['histotype_name'];
  var histotype_formatted = (histotype_name=="ALL_HISTOTYPES") ? "<b>"+histotype_display(histotype_name)+"All tissues</b>" : "tissue type <b>"+histotype_display(histotype_name)+"</b>";

  $("#result_info").html( "For "+ search_by +" gene <b>" + gene + "</b>, a total of <b>" + qi['dependency_count'] + " dependencies</b> were found in " + histotype_formatted + " in " + study_info(qi['study_pmid'])[idetails]);

  //var download_csv_url = global_url_for_download_csv.replace('mysearchby',search_by).replace('mygene',gene).replace('myhistotype',qi['histotype_name']).replace('mystudy',qi['study_pmid']);
  //var download_excel_url = global_url_for_download_excel.replace('mysearchby',search_by).replace('mygene',gene).replace('myhistotype',qi['histotype_name']).replace('mystudy',qi['study_pmid']);

  var download_csv_url = global_url_for_download_csv.replace('mysearchby',search_by).replace('mygene',entrez_id).replace('myhistotype',qi['histotype_name']).replace('mystudy',qi['study_pmid']);
  var download_excel_url = global_url_for_download_excel.replace('mysearchby',search_by).replace('mygene',entrez_id).replace('myhistotype',qi['histotype_name']).replace('mystudy',qi['study_pmid']);


   $("#download_csv_form")
     .attr("action", download_csv_url)
     .submit(function( event ) {
		show_message("download_csv_button", "Downloading CSV file...");
	//return true;
   });

   $("#download_excel_form")
     .attr("action", download_excel_url)
     .submit(function( event ) {
		show_message("download_excel_button", "Downloading Excel file...");
	//return true;
   });

}



function dict_to_string(dict,div) {
	var str = '';
	var count = 0;
	for (key in dict)
	{
		if (str != '') {str += div;}
		str += key
		count++;
	}
	console.log("dict_to_string_and_count",count,str)
	return str;
}

function count_char(s,c) {
	var count = 0;
    for(var i=0; i < s.length; i++){
        if (s.charAt(i) == c) {count++;}
		}
	return count;
}

function get_id_list_for_depenedencies(div, idtype) {
	// returns string with proteins separated by 'div' character (eg. ';'), and the count of number of proteins in the string
	// 'idtype' : 'protein' or 'gene'; or 'protein-gene' for both. If is undefined gives alert, but could change this to default to 'protein'

	// Currently returns a max of 'global_max_stringdb_proteins_ids' ids.
	// Could add a parameter in future: 'max_number_to_get', as 353 is the maximum number of protein id that can be send on the GET line, otherwise stringdb server reports:
	// Request-URI Too Long The requested URL's length exceeds the capacity limit for this server.
	// This url of corresponds to 8216 characters (see example in file: max_stringdb_url.txt)
	// When possible use POST instead of GET to overcome this limit.

	var protein_dict = {}, gene_dict = {}; // Need to use a dictionary because when tissue is 'All tissues' then each protein or gene can appear several times in dependency table (just with different tissue each time).

	var protein_count = 0;

    var getProtein = false, getGene = false;
	switch (idtype) {
		case 'protein':      getProtein=true; break;
	    case 'gene':         getGene=true; break;
		case 'protein-gene': getProtein=true; getGene=true; break;
		default: alert("Invalid idtype: "+idtype); // maybe should default to 'protein'.
	}


	// In order to catch the 'remove-me' class of the space <tr> used for the scroller, need to loop through the rows
	// "remove-me" is the "tablesorter-scroller-spacer" row: https://github.com/Mottie/tablesorter/issues/1143

    $('#result_table tbody tr:visible').each(function(index) {
		if ($(this).hasClass("remove-me")) {console.log("Skipping 'remove-me'",index); return true;} // in the each() loop returning 'true' is same effect as 'continue' in a for(..) loop

		if (protein_count >= global_max_stringdb_proteins_ids) {return false;} // return false to end the ".each()" loop early. like 'break' in a for() loop. Alternatively return true skips to the next iteration (like 'continue' in a normal loop).

	    var first_td = $("td:first-child", $(this));

        if (getProtein) {
		    var protein_id = first_td.attr("data-epid");
            if ((protein_id != '') && !(protein_id in protein_dict)) {
                if (getGene) { // getting the gene and protein ids:
                    var gene_id = first_td.attr("data-gene");
                    if ((gene_id != '') && !(gene_id in gene_dict)) {
                        protein_dict[protein_id] = true;
						gene_dict[gene_id] = true;
                        protein_count++;
					}
					else {console.log("A gene with a valid protein id '"+protein_id+"' shares a gene id: '"+gene_id+"'");}
				}
				else { // only getting the protein ids:
                    protein_dict[protein_id] = true;
                    protein_count++;
				}
			}
		}
		else {
            var gene_id = first_td.attr("data-gene");
            if ((gene_id != '') && !(gene_id in gene_dict)) {
				gene_dict[gene_id] = true;
                protein_count++;
			}

		}

    });
    console.log("get_id_list_for_depenedencies:", protein_dict, gene_dict, protein_count)
	if (getProtein && getGene) {return [dict_to_string(protein_dict,div), dict_to_string(gene_dict,div), protein_count];}
	else if (getProtein) {return [dict_to_string(protein_dict,div), protein_count];}
	else if (getGene) {return [dict_to_string(gene_dict,div), protein_count];}
	else {return false;}
}



function show_cytoscape() {

	show_message("cytoscape_submit_button", "Fetching cytoscape...");  // was: Fetching Cytoscape protein list for cytoscape image

	var protein_and_gene_list_and_count = get_id_list_for_depenedencies(';', 'protein-gene');

	var protein_list = protein_and_gene_list_and_count[0];
    var gene_list = protein_and_gene_list_and_count[1];
    var protein_count = protein_and_gene_list_and_count[2];

	// Could try to remove unconnected proteins for the list before displaying the string network image.
	//var url = global_url_for_stringdb_interactionsList + dict_to_string(protein_dict,'%0D'); // Need a function to do this? eg. jQuery.makeArray() or in EM 5.1: Object.keys(protein_dict);

	//var protein_list = dict_to_string(protein_dict,';');
	console.log("Cytoscape original protein count:",protein_count, "Protein list:",protein_list,"Gene list:",gene_list);

    /*
	For GET use:
	var url = global_url_for_cytoscape_get.replace('myproteins', protein_list).replace('mygenes', gene_list);  // Using semi-colon instead of return character '%0D'
	window.open(url);  // should open a new tab in browser.
	return false; // or maybe return true?
	*/

	// For POST using form:
	document.getElementById("cytoscape_protein_list").value = protein_list;
	document.getElementById("cytoscape_gene_list").value = gene_list;
    return true; // to submit the form, otherwise false;
}



function show_enrichr() {
	show_message("enrichr_submit_button", "Fetching Enrichr..."); // was: "Fetching Enrichr "+gene_set_library+" enrichment ....");

    var dependency_search = global_selected_gene+", "+histotype_display(global_selected_histotype)+", "+study_info(global_selected_study)[ishortname]+'.';
    var gene_list_and_count = get_id_list_for_depenedencies("\n", 'gene');
	if (gene_list_and_count[1]==0) {
		alert("Sorry: No gene names found in this dependency table to submit to Enrichr")
		return false; // to cancel form submission
	    }
	var description = "For "+gene_list_and_count[1] +" genes from CGDD dependency search: "+dependency_search;
    document.getElementById("enrichr_list").value = gene_list_and_count[0];
	document.getElementById("enrichr_description").value = description;
    return true; // to submit the form, otherwise false;
    }



function set_string_form_identifiers() {
    // called by the form: 'string_interactive_form'
	show_message("string_interactive_submit_button", "Fetching String-DB...");

	var protein_list_and_count = get_id_list_for_depenedencies("\n", 'protein');
	//console.log("protein_list_and_count",protein_list_and_count);
    var protein_list = protein_list_and_count[0];
    var protein_count = protein_list_and_count[1];

	console.log("Original protein count:",protein_count, "Protein list:",protein_list);

	if (protein_count == 0) {alert("No rows to display that have ensembl protein ids"); return false;}
	var field_id = (protein_count == 1) ? 'string_protein_identifier' : 'string_protein_identifiers';

    document.getElementById(field_id).value = protein_list; // or $('#'+field_id).val(protein_list);
    return true; // To allow opening the form.
    }



function show_stringdb(display_callback_function) {
	// This calls the String-DB server to remove unconnected proteins from the list before displaying the string network image.

	show_message("string_image", "Fetching String-DB...", 12000); // show this message for 12 seconds as can be slow for images with many proteins, and message will be hidden by image when image loads.

	var protein_list_and_count = get_id_list_for_depenedencies(';', 'protein');
	console.log("protein_list_and_count",protein_list_and_count);
    var protein_list = protein_list_and_count[0];
    var protein_count = protein_list_and_count[1];

	console.log("Original protein count:",protein_count, "Protein list:",protein_list);
	var url = global_url_for_stringdb_interactionsList.replace('myproteins', protein_list);  // Using semi-colon instead of return character '%0D'

	// Because of AJAX same origin policy (ie. no cross-site requests) so need to use our pythonanywhere server as a proxy to get the string interaction list.
	// I had tried retrieving interactionsList directly from String-DB.org, but it would need to support either JSNOP or CORS in its replies: http://stackoverflow.com/questions/15477527/cross-domain-ajax-request
	// http://hayageek.com/cross-domain-ajax-request-jquery/

	//console.log("url.length:", url.length);
    console.log("url:", url);
    $.ajax({
      url: url,
      dataType: 'text',  // 'csv', // really is tab deliminated
      })
      .done(function(protein_list2, textStatus, jqXHR) {  // or use .always(function ...
	    //console.log("Received:", protein_list2);
		protein_list = protein_list2;
		 })
	  .fail(function(jqXHR, textStatus, errorThrown) {
		 alert("Ajax Failed: '"+textStatus+"'  '"+errorThrown+"'");  // Just display the original list below anyway.
         })
	  .always(function() {
		 if (protein_list=='') {
		     protein_count = 0
			 alert('StringDB reports zero interactions of confidence>700 between these selected proteins. Click the "StringDB interactive" button to see this.')
		 }
		 else {
		    protein_count = protein_list.split(';').length;
		    protein_list = protein_list.replace(/;/g, '%0D');  // as javascript's replace(';', '%0D') only replaces the first instance.
	  	    display_callback_function(protein_list, protein_count);
		 }
		 console.log("Count after removing unconnected proteins: "+protein_count+", Protein list: '"+ protein_list+"'" );
	     });

    return false; // Return false to the caller so won't move on the page as is called from a href="...
 }



function toggle_show_drugs(obj,drug_names,div,gene) {
  // An alternative could be tooltip that stays when link clicked: http://billauer.co.il/blog/2013/02/jquery-tooltip-click-for-help/
  // or: http://pagenotes.com/pagenotes/tooltipTemplates.htm
  // or: Modal tooltips: http://qtip2.com/
  // or: https://www.quora.com/How-do-I-make-a-tooltip-that-stays-visible-when-hovered-over-with-JavaScript

  // This works but the column width is too wide if then select Any from filter menu:
  //  obj.innerHTML = obj.innerHTML.indexOf('[more]') > -1 ? make_drug_links(drug_names,div)+' [less]' : drug_names.substr(0,8)+'...[more]';

  var mycontent = '<p style="vertical-align:middle;">For gene '+gene+', the following inhibitors were found in DGIdb:<br/>&nbsp;<br/>'+make_drug_links(drug_names,div)+'</p>';

  $.fancybox.open({
    preload: 0, // Number of gallary images to preload
	width: 300,
	height: 300,
	minWidth: 250,
	maxHeight: 300,
	//width: '100%',
	//height: '100%',
	autoSize: false, // true, //false,  // true,  // false, // otherwise it resizes too tall.
    //padding: 2,  	// is space between image and fancybox, default 15
    //margin:  2, 	// is space between fancybox and viewport, default 20
    aspectRatio: true,
    //fitToView: true,
	autoCenter: true,
    arrows: false,
	closeEffect : 'none',
    helpers: {
        title: {
            type: 'inside'
        },
        overlay: {
            showEarly: true  // false  // Show as otherwise incorrectly sized box displays before images have arrived.
        }
    },

	type: 'inline', // 'html', // 'iframe', // 'html',
	content: mycontent,
    // href: href,
    // title: box_title  //,
   });
  }



function make_drug_links(drug_names,div) {
  // DBIdb paper: http://nar.oxfordjournals.org/content/44/D1/D1036.full
  var drugs = drug_names.split(div); // 'div' is a comma or semi-colon
  var links ='';
  for (var i=0; i<drugs.length; i++) {
	if (i>0) {links += ', ';}
    links += '<a href="http://dgidb.genome.wustl.edu/drugs/'+drugs[i]+'" target="_blank">'+drugs[i]+'</a>';
  }
  return links;
}



function stringdb_image(protein_list,protein_count) {
  // An alternative to string-db url is to use the stringdb links to build own cyctoscape display: http://thebiogrid.org/113894/summary/homo-sapiens/arid1a.html
  // var protein_list = get_id_list_for_depenedencies(); // returns (protein_list, protein_count)
  if (protein_count == 0) {alert("No rows that have ensembl protein ids"); return false;}
  var string_url = (protein_count == 1) ? global_url_for_stringdb_one_network : global_url_for_stringdb_networkList;
  string_url += protein_list;

  // Displaying in a fancybox, (alternatively open in a new browser tab, but can be blocked by popup blockers):
  //	window.open(string_url);  // should open a new tab in browser.
  //	return false; // or maybe return true?
  //	can run this command in the browser console to experiment)

  var mycontent = '<center><img src="' + string_url +'" alt="Loading StringDB image...."/></center>';
  //var mycontent = string_url
  var href = string_url;

  var box_title = '<p align="center" style="margin-top: 0;">Showing high confidence (score&ge;700) string-db interactions between the dependencies associated with driver gene <b>'+global_selected_gene+'</b><br/><a href="javascript:void(0);" title="String-db interactive view" onclick="$(\'#string_interactive_submit_button\').click();">Click here to go to interactive String-db view</a></p>';  //  or: onclick="document.getElementById(\'string_interactive_submit_button\').click();"
  $.fancybox.open({
    preload: 0, // Number of gallary images to preload
    minWidth: 900,
    //minHeight: 750,
	width: '100%',
	height: '100%',
	autoSize: false, // true, // otherwise it resizes too tall.
    padding: 2,  	// is space between image and fancybox, default 15
    margin:  2, 	// is space between fancybox and viewport, default 20
    aspectRatio: true,
    fitToView: true,
	autoCenter: true,
    arrows: false,
	closeEffect : 'none',
    helpers: {
        title: {
            type: 'inside'
        },
        overlay: {
            showEarly: false   // false  // or true, as otherwise incorrectly sized box displays before images have arrived.
        }
    },

	type: 'image', // type image should centre the small stringdb network images // 'inline', // 'html', // 'iframe', // 'html', //'inline',
    href: href,
	// content: mycontent,
    title: box_title  //,
   });

   return false; // Return false to the caller so won't move on the page
}





function populate_table(data,t0) {
	var html = '';
	// The position of the P-value column needs to correspond with the index.htm javascript for "filter-select:"

	//str.split(',') // or use '\t' as using comma assumes that no fields contain a comma - checked before data was added to the database.
	// if need to parse CSV that has quoted strings containing commas, then use: https://github.com/evanplaice/jquery-csv/
	var qi = data['query_info'];
	var search_by = qi['search_by'];

	var driver,target, search_by_driver;
	switch(search_by) {
		case 'driver':
	       $("#dependency_col_name").html('Dependency');
		   search_by_driver = true;
		   driver = qi['gene_name'];
		   break;
		case 'target':
	       $("#dependency_col_name").html('Driver');
		   search_by_driver = false;
		   target = qi['gene_name'];
		   break;
		default: alert("Invalid search_by: "+search_by);
	}

	var histotype = qi['histotype_name'];
	
	// Variables for links to string.org:
	var search_gene_string_protein = '9606.'+global_selected_gene_info['ensembl_protein_id'];


	// Alternative (?default) is 'evidence'.

	// StringDb API options:
	//   identifiers - required parameter for multiple items, e.g.DRD1_HUMAN%0DDRD2_HUMAN
	//   network - The network image for the query item
    //   networkList - The network image for the query items
    //   limit - Maximum number of nodes to return, e.g 10.
    //   required_score - Threshold of significance to include a interaction, a number between 0 and 1000
    //   additional_network_nodes - Number of additional nodes in network (ordered by score), e.g./ 10
    //   network_flavor - The style of edges in the network. evidence for colored multilines. confidence for singled lines where hue correspond to confidence score. (actions for stitch only)

	// var string_url_all_interactions = global_url_for_stringdb_networkList;  // For a call for all interactions in this table. Doesn't need the above search_gene_string_protein.

	var interaction_count = 0;

	results = data['results']

	// result array indexes:
	// igene can be either driver or target depending on 'search_by'.
	var igene=0, iwilcox_p=1, ieffect_size=2, izdelta=3, istudy_pmid=4, imultihit=5, iinteraction=6, iinhibitors=7; // itarget_variant=8; (removed target_variant - was only for Achilles variant boxplot image)
	// In javascript array indexes are represented internally as strings, so maybe using string indexes is a bit faster??


// In Chrome the total width of all the <th> elements is 985px, so make these widths add up to 985px -->
var width100=""; // "width:100px; ";
var width125=""; // "width:125px; ";
var width150=""; // "width:150px; ";


var stopat=20;	// To stop table early for testing.

	for (var i=0; i<results.length; i++) {   // for dependency in dependency_list	  
//if (i>stopat) {break;}
      d = results[i]; // d is just a reference to the array, not a copy of it, so should be more efficient and tidier than repeatidly using results[i]

	  var id="dtd"+(i+1).toString(); // id for the dependency table first cell in each row

	  var study = study_info(d[istudy_pmid]); // name,type,summary,details for 'study_pmid'
	  // perhaps 'map ......join' might be more efficient?
	  var comma = "', '";  // ie. is:  ', '
	  // An alternative to building the html as a string, is to directly modify the table using javascript.
	  // Pass the unformatted effect size, as the html tags could mess up as embedded inside tags.
	  // alternatively could pass 'this', then use next() to find subsequent columns in the row, or keep the data array globally then just specify the row number as the parameter here, eg: plot(1) for row one in the array.
      if (search_by_driver) {target = d[igene];}
      else {driver = d[igene];}

	  // The "this"	parameter correctly doesn't have quotes:
	  var plot_function = "plot('"+ id +comma+ driver + comma + target +comma+ histotype +comma+ d[istudy_pmid] +comma+ d[iwilcox_p] +comma+ d[ieffect_size] +comma+ d[izdelta] +"');"; // +comma+ d[itarget_variant]

      // Another way to pouplatte table is using DocumentFragment in Javascript:
      //      https://www.w3.org/TR/DOM-Level-2-Core/core.html#ID-B63ED1A3

	  // *** GOOD: http://desalasworks.com/article/javascript-performance-techniques/

	  val = parseFloat(d[iwilcox_p]); // This will be in scientific format, eg: 5E-4
      if      (val <= 0.0001) {bgcolor=darkgreen_UCD_logo}
	  else if (val <= 0.001)  {bgcolor=midgreen_SBI_logo}
	  else if (val <= 0.01)   {bgcolor=lightgreen_SBI_logo}
	  else {bgcolor = '';}
	  style = width100+"text-align:center;";
	  if (bgcolor != '') {style += ' background-color: '+bgcolor+';';}
	  var wilcox_p_cell = '<td style="'+style+'">' + d[iwilcox_p].replace('e', ' x 10<sup>') + '</sup></td>';

	  var val = parseFloat(d[ieffect_size]); // convert to float value
      if      (val >= 90) {bgcolor=darkgreen_UCD_logo}
	  else if (val >= 80) {bgcolor=midgreen_SBI_logo}
	  else if (val >= 70) {bgcolor=lightgreen_SBI_logo}
	  else {bgcolor = '';}
	  var style = width100+"text-align:center;";
	  if (bgcolor != '') {style += ' background-color: '+bgcolor+';';}
	  var effectsize_cell = '<td style="'+style+'">' + d[ieffect_size] + '</td>';

	  var val = parseFloat(d[izdelta]); // convert to float value
      if      (val <= -2.0) {bgcolor=darkgreen_UCD_logo}
	  else if (val <= -1.5) {bgcolor=midgreen_SBI_logo}
	  else if (val <= -1.0) {bgcolor=lightgreen_SBI_logo}
	  else {bgcolor = '';}
	  var style = width100+"text-align:center;";
	  if (bgcolor != '') {style += ' background-color: '+bgcolor+';';}
	  var zdelta_cell = '<td style="'+style+'">' + d[izdelta] + '</td>';

	  var style = width100+"text-align:center;";
	  var multihit_cell;
	  if (d[imultihit] == '') { multihit_cell = '<td style="'+style+'"></td>'; }
	  else {
	      var bgcolor = '';
		  var num = d[imultihit].split(";").length;
	      if      (num > 2)  {bgcolor=darkgreen_UCD_logo;}
	      else if (num == 2) {bgcolor=midgreen_SBI_logo;}
	      else               {bgcolor=lightgreen_SBI_logo;}
		  if (bgcolor != '') {style += ' background-color: '+bgcolor+';';}
   	      // WAS: multihit_cell = '<td style="'+style+'" data-multihit="'+d[imultihit]+'">' + d[imultihit].substr(0,15) + '...</td>';
		  multihit_cell = '<td style="'+style+'" data-multihit="'+d[imultihit]+'"> Yes </td>';
		  }  	  
	  
	  var interaction_cell;
	  var style = width100+"text-align: center;";
	  if (d[iinteraction] == '') {interaction_cell = '<td style="'+style+'"></td>';}
	  else {
	    var interaction = d[iinteraction].split('#'); // as contains, eg: High#ENSP00000269571 (ie protein id)
	    switch (interaction[0]) { // This will be in scientific format, eg: 5E-4
          case 'Highest': bgcolor=darkgreen_UCD_logo;  break;
	      case 'High':    bgcolor=midgreen_SBI_logo;   break;
	      case 'Medium':  bgcolor=lightgreen_SBI_logo; break;
	      default: bgcolor = '';
        }
	    if (bgcolor != '') {style += ' background-color: '+bgcolor+';';}

		var string_protein = '';
		if (interaction[1] == '') {
		  interaction_cell = '<td style="'+style+'">'+interaction[0]+'</td>';
		} else {
		  string_protein = '9606.'+interaction[1];
		  interaction_count ++;

		  // BUT this is just the target identifier now:
		  var string_url = global_url_for_stringdb_interactive_networkList_score400 + search_gene_string_protein + "%0D" + string_protein;
		  // Colm wants driver + target as they interact as (Med/High/Highest) link means these interact with score >=400. 

		  interaction_cell = '<td style="'+style+'"><a href="'+ string_url +'" target="_blank">'+interaction[0]+'</a></td>';
		}
	  }

	  var style = width150+"text-align: center;";
	  var inhibitor_cell;
	  if (d[iinhibitors] == '') {inhibitor_cell='<td style="'+style+'"></td>';}
	  else {
		  var onclick_or_alink = '';
		  if (d[iinhibitors].length <= 12) {
			  // create individual <a...> links for each drug
			  onclick_or_alink = make_drug_links(d[iinhibitors],', ');
			  }
		  else {
		    cell_text = d[iinhibitors].substr(0,7)+'..<span style="font-size:80%">[more]</span>';
			// create a onclick to open fancybox:
            var onclick_function = "toggle_show_drugs(this,'"+d[iinhibitors]+"', ', ', '"+d[igene]+"');";
			onclick_or_alink = '<a href="javascript:void(0);" onclick="'+onclick_function+'">'+cell_text+'</a>';
		  }
		  inhibitor_cell = '<td style="'+style+' background-color: beige;">'+onclick_or_alink+'</td>';
	  }
	  
	  // In future could use the td class instead of style=... - but need to add on hoover colours, etc....
	  // Removed tissue column as is in the box above the table, and is same for all row of the table:
	  html += '<tr>'
	    + '<td id="'+id+'" style="'+width125+'text-align:left; cursor:pointer;" data-gene="'+d[igene]+'" data-epid="'+string_protein+'" onclick="'+plot_function+'">' + d[igene] + '</td>' // was class="tipright" 		
        + wilcox_p_cell
		+ effectsize_cell
		+ zdelta_cell
        // + '<td style="'+width100+'text-align:center;">' + histotype_display(d[ihistotype]) + '</td>'
		+ '<td style="'+width100+'text-align:center;" data-study="'+d[istudy_pmid]+'">' + study_weblink(d[istudy_pmid],study) + '</td>' // but extra text in the table, and extra on hover events so might slow things down.
		+ '<td style="'+width100+'text-align:center;" data-exptype="'+d[istudy_pmid]+'">' + study[iexptype] + '</td>' // experiment type. The 'data-exptype=""' is use by tooltips
	    + multihit_cell
        + interaction_cell
	    + inhibitor_cell
		+ '</tr>';  // The newline character was removed from end of each row, as the direct trigger update method complains about undefined value.
	}

	console.log("Data formatted as html: ",performance.now()-t0); t0 = performance.now();

	$("#result_table_tbody").html(html);
	console.log("Data added to table tbody: ",performance.now()-t0); t0 = performance.now();

    triggercallback = function( table ){
     //   alert( 'update applied' );
	 console.log("Table updated: ",performance.now()-t0); t0 = performance.now();
    };

	// resort = false;

	return t0;
}



function format_gene_info_for_tooltip(data) {
  var synonyms = data['synonyms'];
  if (synonyms != '') {synonyms = ' | '+synonyms}
  return '<b>'+data['gene_name'] + '</b>' + synonyms +'<br/><i>' + data['full_name']+'</i>';
  }


function is_form_complete() {
  // Check that search query is valid, as the autocomplete form permits text that doesn't match any driver:
  var search_by = document.getElementById("search_by").value;
  var g = document.getElementById("gene").value;
  if (g == null || g == "") {
    alert("Search '"+search_by+" gene name' field needs a value entered");
    return false;
    }

  var found = false;
  if (search_by === 'driver') {
    for (var i=0; i<driver_array.length; i++) {
      if (g == driver_array[i]['value']) {
        found = true;
        break;
      }
    }
  }
  else if (search_by === 'target') {
      for (var i=0; i<target_array.length; i++) {
      if (g == target_array[i]['value']) {
        found = true;
        break;
      }
    }
  }
  else {alert('Invalid search_by '+search_by)}

  if (found == false) {alert("The "+search_by+" gene value: '"+g+"' doesn't match any "+search_by+" in the list. Please select a "+search_by+" gene.");}
  return found;
  }




function next_dependency(this_td) {
  if (this_td.tagName != "TD") {alert("next_dependency this_td, expected TD, but got "+this_td.tagName)}
  var row=this_td.parentNode;
  if (row.tagName != "TR") {alert("next_dependency this row, expected TR, but got "+row.tagName)}
  for (row = row.nextSibling; row!=null; row = row.nextSibling) {   // go to the next row
    if ($(row).hasClass("remove-me") || $(row).hasClass("filtered") || (row.nodeType!=1)) {continue;} // to skip hidden or special rows (such as the hidden row at top of scroller table)
	// Node.ELEMENT_NODE	1	An Element node such as <p> or <div>.
	if (row.tagName != "TR") {alert("next_dependency row, expected TR, but got "+row.tagName)}
	return row.firstChild; // should be the first td in this tr
    }
  return null;
  }


function previous_dependency(this_td) {
  if (this_td.tagName != "TD") {
	  alert("previous_dependency this_td, expected TD, but got "+this_td.tagName);
	  }
  var row=this_td.parentNode; // or use: $( "li.third-item" ).prev()
  if (row.tagName != "TR") {
	  alert("previous_dependency this row, expected TR, but got "+row.tagName);
      }
  for (row=row.previousSibling; row!=null; row=row.previousSibling) {
    if ($(row).hasClass("remove-me") || $(row).hasClass("filtered") || (row.nodeType!=1)) {continue;}
	if (row.tagName != "TR") {
		alert("previous_dependency, expected TR, but got "+row.tagName);
	    }
	return row.firstChild; // the td
    }
  return null;
  }


function plot(dependency_td_id, driver, target, histotype, study_pmid, wilcox_p, effect_size, zdelta_score, target_variant) { // The index number of the dependency in the array
  show_svg_boxplot_in_fancybox(dependency_td_id, driver, target, histotype, study_pmid, wilcox_p, effect_size, zdelta_score, target_variant); // the 'target_info' (including 'ncbi_summary') is now retrieved with the boxplot_data.
  return false; // Return false to the caller so won't move on the page as is called from a href="...
}

