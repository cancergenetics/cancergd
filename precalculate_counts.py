"""
Script to precalculate various features used in the DB interface.
These are stored in the study or gene tables. Details stored include :

# CGDs for each driver gene
# Tissues for each driver gene
# Studies for each driver gene
# Drivers for each study

In the future we should calculate these dynamically in the interface
and cache the results.
"""

import sys
import django
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
import warnings
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cgdd.settings")
django.setup()
from gendep.models import Study, Gene, Dependency


def error(message):
    sys.stderr.write('*** ERROR:  %s\n' % message)


def add_counts_of_study_tissue_and_target_to_drivers():
    print("Adding study, tissue and target counts to drivers")
    # select driver, count(distinct study), count(distinct histotype),
    # count(distinct target) from gendep_dependency group by driver;
    counts = Dependency.objects.values('driver').annotate(num_studies=Count('study', distinct=True),
                                                          num_histotypes=Count('histotype', distinct=True), num_targets=Count('target', distinct=True))
    # There is probably a faster SQL type quesry, or bulk_update
    for row in counts:
        try:
            print("gene_name: %s %d %d %d" % (row['driver'], row[
                  'num_studies'], row['num_histotypes'], row['num_targets']))
            g = Gene.objects.get(gene_name=row['driver'])  # .gene_name
            if not g.is_driver:
                error("count gene isn't marked as a driver '%s'" %
                      (g.gene_name))
            else:
                g.driver_num_studies = row['num_studies']
                g.driver_num_histotypes = row['num_histotypes']
                g.driver_num_targets = row['num_targets']
                g.save()
        except ObjectDoesNotExist:  # Not found by the objects.get()
            error("driver gene_name NOT found in the Gene table: '%s'" %
                  (row['driver']))
    print("Finished adding study, tissue and target counts to the drivers in the dependency table")


def add_tissue_and_study_lists_for_each_driver():
    print("Adding tissue list to each driver")
    q = Dependency.objects.order_by('driver_id').values(
        'driver_id', 'histotype').distinct()
    driver_tissues = {}
    for d in q:
        driver = d['driver_id']
        if driver in driver_tissues:
            driver_tissues[driver] += ';' + d['histotype']
        else:
            driver_tissues[driver] = d['histotype']

    with transaction.atomic():  # Using atomic makes this script run in half the time, as avoids autocommit after each save()
        for driver in driver_tissues:
            g = Gene.objects.get(gene_name=driver)
            g.driver_histotype_list = driver_tissues[driver]
            num_in_list = g.driver_histotype_list.count(';') + 1
            # BUT 'g.num_histotypes' could drefer to targets not drivers.
            if g.driver_num_histotypes != num_in_list:
                print("Count mismatch: g.num_histotypes(%d) != num_in_list(%d)" % (
                    g.driver_num_histotypes, num_in_list))
            g.save()
            print(g.gene_name, g.driver_histotype_list)
            # except ObjectDoesNotExist: # Not found by the objects.get()

    # putting order_by() after distinct() might not work correctly.
    q = Dependency.objects.order_by('driver_id').values(
        'driver_id', 'study_id').distinct()
    # print(q.query)
    driver_studies = dict()
    for d in q:
            # print(d)
        driver = d['driver_id']
        if driver in driver_studies:
            driver_studies[driver] += ';' + d['study_id']
        else:
            driver_studies[driver] = d['study_id']

    with transaction.atomic():  # Using atomic makes this script run in half the time, as avoids autocommit after each save()
        for driver in driver_studies:
            g = Gene.objects.get(gene_name=driver)
            g.driver_study_list = driver_studies[driver]
            num_in_list = g.driver_study_list.count(';') + 1
            # BUT 'g.num_studies' could drefer to targets not drivers.
            if g.driver_num_studies != num_in_list:
                print("Count mismatch: g.num_studies(%d) != num_in_list(%d)" %
                      (g.driver_num_studies, num_in_list))
            g.save()
            print(g.gene_name, g.driver_study_list)
            # except ObjectDoesNotExist: # Not found by the objects.get()

    print("Finished adding tissue and study lists to drivers")


def add_counts_of_driver_tissue_and_target_to_studies():
    print("Adding driver, tissue and target counts to studies")
    # select study, count(distinct driver), count(distinct histotype),
    # count(distinct target) from gendep_dependency group by study;
    counts = Dependency.objects.values('study').annotate(num_drivers=Count('driver', distinct=True), num_histotypes=Count(
        'histotype', distinct=True), num_targets=Count('target', distinct=True))
    # There is probably a faster SQL type quesry, or bulk_update
    for row in counts:
        try:
            print("study: %s %d %d %d" % (row['study'], row[
                  'num_drivers'], row['num_histotypes'], row['num_targets']))

            s = Study.objects.get(pmid=row['study'])  # .study_pmid
            s.num_drivers = row['num_drivers']
            s.num_histotypes = row['num_histotypes']
            s.save()
        except ObjectDoesNotExist:  # Not found by the objects.get()
            error("study pmid % NOT found in the Study table: '%s'" %
                  (row['study']))
    print("Finished adding driver, tissue and target counts to the study table")

if __name__ == "__main__":
    add_counts_of_study_tissue_and_target_to_drivers()
    add_counts_of_driver_tissue_and_target_to_studies()
    add_tissue_and_study_lists_for_each_driver()
