from django.conf.urls import url
from django.views.decorators.cache import cache_page

from django.contrib import admin # To add the admin wrapper to awstats_view

from . import views

app_name = 'gendep'

# Some info about url patterns: http://www.webforefront.com/django/accessurlparamsviewmethods.html
# Optional parameters: http://stackoverflow.com/questions/14351048/django-optional-url-parameters

urlpatterns = [
   # url(r'^$', cache_page(60 * 15)(views.index), name='home'),
    url(r'^$', views.index, name='home'),
    url(r'^about/$', views.about, name='about'),
    url(r'^tutorial/$', views.tutorial, name='tutorial'),
    url(r'^drivers/$', views.drivers, name='drivers'),
    url(r'^targets/$', views.targets, name='targets'),
    url(r'^tissues/$', views.tissues, name='tissues'),
    url(r'^studies/$', views.studies, name='studies'),
    url(r'^contact/$', views.contact, name='contact'),
    url(r'^faq/$', views.faq, name='faq'),
    
    #url(r'^awstats/$', admin.site.admin_view(awstats_view), name='awstats'),     # The 'self.admin_site.admin_view()' wrapper checks that have admin permissions and marks the page as non-cacheable.

#    url(r'^awstats/$', views.awstats, name='awstats'),
#    url(r'^awstats/awstats$', views.awstats, name='awstats_with_param'), # For the links within the awstats.pl (as set by the 'WrapperScript="awstats"' in the awstats config file.
    
    # url(r'^(?P<driver>[0-9A-Z]+)/graph/$', views.graph, name='graph'),

    url(r'^study/(?P<study_pmid>[0-9A-Za-z]+)/$', views.show_study, name='show_study'), # pmid could be 'Pending0001'

    url(r'^get_drivers/', views.get_drivers, name='get_drivers'),    
    
    url(r'^log_comment/', views.log_comment, name='log_comment'),
    
    # url(r'^get_dependencies/(?P<search_by>(?:mysearchby|driver|target))/(?P<gene_name>[0-9A-Za-z\-_\.]+)/(?P<histotype_name>[0-9A-Za-z\_]+)/(?P<study_pmid>[0-9A-Za-z\_]+)/$', views.get_dependencies, name='get_dependencies'), 
    url(r'^get_dependencies/(?P<search_by>(?:mysearchby|driver|target))/(?P<entrez_id>[0-9a-z]+)/(?P<histotype_name>[0-9A-Za-z\_]+)/(?P<study_pmid>[0-9A-Za-z\_]+)/$', views.get_dependencies, name='get_dependencies'),
    # '\_' is needed to match ALL_STUDIES and ALL_HISTOTYPES

    # url(r'^ajax_results/', views.ajax_results_slow_full_detail_version, name='ajax_results_post'),
    
    # url(r'^download_csv/(?P<delim_type>(?:csv|tsv|xlsx))/(?P<search_by>(?:mysearchby|driver|target))/(?P<gene_name>[0-9A-Za-z\-_\.]+)/(?P<histotype_name>[0-9A-Za-z\_]+)/(?P<study_pmid>[0-9A-Za-z\_]+)/$', views.download_dependencies_as_csv_file, name='download_csv'), # \_ needed to match ALL_STUDIES and ALL_HISTOTYPES
    url(r'^download_csv/(?P<delim_type>(?:csv|tsv|xlsx))/(?P<search_by>(?:mysearchby|driver|target))/(?P<entrez_id>[0-9a-z]+)/(?P<histotype_name>[0-9A-Za-z\_]+)/(?P<study_pmid>[0-9A-Za-z\_]+)/$', views.download_dependencies_as_csv_file, name='download_csv'), # \_ needed to match ALL_STUDIES and ALL_HISTOTYPES

    url(r'get_boxplot/(?P<dataformat>(?:myformat|csvplot|jsonplot|jsonplotandgene|csv|download))/(?P<driver_name>[0-9A-Za-z\-_\.]+)/(?P<target_name>[0-9A-Za-z\-_\.]+)/(?P<histotype_name>[0-9A-Za-z\_]+)/(?P<study_pmid>[0-9A-Za-z\_]+)/$', views.get_boxplot, name='get_boxplot'),
    # NOTE: Still using target gene_name (as we don't pass the target entrez_id to the html dependency table as means entrez_id would need top be sent for each dependency table row)
    # Still using driver_name, as could have searched by target, so wouldn't have entrez_id for drivers in the html dependency table.
    # url(r'get_boxplot/(?P<dataformat>(?:myformat|csvplot|jsonplot|jsonplotandgene|csv|download))/(?P<driver_entrez>[0-9a-z]+)/(?P<target_name>[0-9A-Za-z\-_\.]+)/(?P<histotype_name>[0-9A-Za-z\_]+)/(?P<study_pmid>[0-9A-Za-z\_]+)/$', views.get_boxplot, name='get_boxplot'),
    
    url(r'^get_gene_info/(?P<gene_name>[0-9A-Za-z\-_\.]+)/$', views.gene_info, name='get_gene_info'), # tip=element.data('url'),
    # url(r'^get_gene_info/(?P<gene_name>[0-9A-Za-z\-_\.]+)/$', views.gene_info, name='get_gene_info'), # tip=element.data('url'),

    #url(r'get_stringdb_interactions/(?P<protein_list>.+)/$', views.get_stringdb_interactions, name='get_stringdb_interactions'),
    
    # Allow carriage return character (as is %0D) - using a semicolon as the divider instead of return:
    url(r'get_stringdb_interactions/(?P<required_score>[0-9]+)/(?P<protein_list>[0-9A-Za-z\.;\%\r]+)/$', views.get_stringdb_interactions, name='get_stringdb_interactions'),
    
    # For sending protein_list request as HTML GET or POST:
    url(r'get_stringdb_interactions/(?P<required_score>[0-9]+)/$', views.get_stringdb_interactions, name='get_stringdb_interactions_post'),
        
    url(r'cytoscape/(?P<required_score>[0-9]+)/(?P<protein_list>[0-9A-Za-z\.;\%\r]+)/(?P<gene_list>[0-9A-Za-z\-_\.;\%\r]+)/$', views.cytoscape, name='cytoscape_get'),
    
    # For sending protein_list and gene_list as HTML GET or POST:
    url(r'cytoscape/(?P<required_score>[0-9]+)/$', views.cytoscape, name='cytoscape_post'),
    
    url(r'^(?P<search_by>(?:mysearchby|driver|target))/(?P<gene_name>[0-9A-Za-z\-_\.]*)/(?P<histotype_name>[0-9A-Za-z\_]*)/(?P<study_pmid>[0-9A-Za-z\_]*)/$', views.index, name='home_search_by_gene_tissue_pmid'),
    # url(r'^(?P<search_by>(?:mysearchby|driver|target))/(?P<entrez_id>[0-9a-z]*)/(?P<histotype_name>[0-9A-Za-z\_]*)/(?P<study_pmid>[0-9A-Za-z\_]*)/$', views.index, name='home_search_by_gene_tissue_pmid'),    

    url(r'^(?P<search_by>(?:mysearchby|driver|target))/(?P<gene_name>[0-9A-Za-z\-_\.]+)/$', views.index, name='home_search_by_gene'),
    # url(r'^(?P<search_by>(?:mysearchby|driver|target))/(?P<entrez_id>[0-9a-z]+)/$', views.index, name='home_search_by_gene'),

    url(r'^(?P<search_by>(?:mysearchby|driver|target))/$', views.index, name='home_search_by'), # Needs to be at end as could otherwise interpret 'about' as driver name.
        
    # eg:  http://localhost:8000/gendep/driver/ERBB2/PANCAN/26947069/

    # url(r'^driver/(?P<driver>[0-9A-Za-z\-_\.]+)/$', views.index, name='driver'), # ie: /driver/gene_name/
    # The parameters could be optional, so use '*'. If "//" not permitted in url, then could use "ALL/ALL/" (or "ALL_GENES", "ALL_HISTOTYPES", "ALL_STUDIES")
    # http://stackoverflow.com/questions/2325433/making-a-regex-django-url-token-optional
    # Better: https://gist.github.com/c4urself/1028897
    #url(r'^(?P<search_by>(?:mysearchby|driver|target))/(?P<gene_name>[0-9A-Za-z\-_\.]+)/(?P<histotype_name>[0-9A-Za-z\_]+)/(?P<study_pmid>[0-9A-Za-z\_]+)$', views.index, name='home_search_by'), # Needs to be at end as could otherwise interpret 'about' as driver name.    
    
    
]
