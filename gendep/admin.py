from django.contrib import admin
from .models import Study, Gene, Dependency, Comment

""" Classes for formatting of the Dejango Admin pages """ 

class StudyAdmin(admin.ModelAdmin):
    list_display  = ('pmid', 'title', 'authors', 'journal', 'pub_date')
    search_fields = ['pmid', 'title', 'authors', 'journal', 'pub_date']


class GeneAdmin(admin.ModelAdmin):
    list_display  = ('gene_name', 'entrez_id', 'ensembl_id', 'full_name')
    search_fields = ['gene_name', 'entrez_id', 'ensembl_id']


class DependencyAdmin(admin.ModelAdmin):
    # For the foreign keys, to return a string need to append: '__gene_name' or use '_id' suffix
    list_display  = ('driver', 'target', 'histotype', 'wilcox_p', 'study')
    search_fields = ['driver_id', 'target_id', 'histotype']
    # search_fields = ['driver__gene_name', 'target__gene_name', 'histotype__full_name']


class CommentAdmin(admin.ModelAdmin):
    list_display  = ('name', 'email', 'comment', 'ip', 'date') # optionally add: 'interest'
    search_fields = ['name', 'email', 'comment', 'ip', 'date'] # optionally add: 'interest'




# OR Subclass the ModelAdmin to add this custom AwStats view.
#   based on: http://patrick.arminio.info/additional-admin-views/
#   and: https://docs.djangoproject.com/en/1.9/ref/contrib/admin/#django.contrib.admin.ModelAdmin.get_urls 
#class AwStats(admin.ModelAdmin):  
  # eg: http://www.cancergd.org/awstats/awstats?config=/home/cgenetics/awstats/awstats.cancergd.org.conf&output=allhosts  
    
# From: https://www.stavros.io/posts/how-to-extend-the-django-admin-site-with-custom/
"""
def get_admin_urls(urls):
    def get_urls():
        my_urls = [ url(r'^awstats/$', admin.site.admin_view(awstats_view), name='awstats'), ]     # The 'self.admin_site.admin_view()' wrapper checks that have admin permissions and marks the page as non-cacheable.
        print("Getting awstats url: ",my_urls + urls)
        return my_urls + urls
    print("Added awstats url: ",get_urls())
    return get_urls # returns a reference to the above get_urls() function.

#admin.site.get_urls = get_admin_urls(admin.site.get_urls())
    
print(admin.site.get_urls())    
"""
admin.site.register(Study, StudyAdmin)
admin.site.register(Gene, GeneAdmin)
admin.site.register(Dependency, DependencyAdmin)
admin.site.register(Comment, CommentAdmin)

# admin.site.register(MyEntry, AwStats)
