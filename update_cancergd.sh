#!/bin/bash

ALL=1

function ask() {
  local ANSWER
  if [ "$ALL" -eq "0" ]; then return 0; fi
  while true; do
    read -p "$1 ( y/n/all )? " ANSWER
    case "$ANSWER" in
       y|Y ) return 0 ;;
       n|N ) return 1 ;;
       all|ALL ) ALL=0; return 0 ;;
       * ) echo "Invalid answer";;
    esac
  done
}


echo -e "\nUpdating webpages and database (Press Ctrl+C to abort)"
echo -e   "======================================================\n"

#DATE=`date +%Y-%m-%d`
DATE=`date +%d%b%Y`
ask "Using date '$DATE' is this date correct?"

ask "Pull latest from github" && ( git pull || exit 1 )

ask "Collect static files into static/gendep" && ( python manage.py collectstatic || exit 2 )

if ask "Migrate MySQL database structure - only needed if you have changed the 'models.py' data structure"; then
  python manage.py makemigrations gendep || exit 3
  python manage.py migrate || exit 4
fi;

# ask "Unzip 'db_sqlite.zip'" && ( unzip db_sqlite.zip || exit 5 )
ask "xz uncompress 'db_sqlite.xz' (keeping the .xz file)" && ( xz -k db_sqlite.xz || exit 5 )

ask "Upload db.sqlite3 to mysql" && ( python sqlite_to_mysql.py || exit 6 )

ask "Clear database cache" && ( python clearcache.py || exit 7 )

ask "Export db to csv files" && ( bash ./convert_db_to_csv_xz.sh || exit 8 )

if ask "Export the multi-hit summary csv file"; then
#  python extract_multihits_from_dependencies_csv.py multihit_dependencies_$DATE.csv || exit 9
#  cp -ip multihit_dependencies.csv  static/gendep/ || exit 10

#  mv -i multihit_dependencies.csv multihit_dependencies_$DATE.csv || exit 10
#  zip static/gendep/multihit_dependencies_$DATE.csv.zip multihit_dependencies_$DATE.csv || exit 11

# Now using the more compact .xz compression (and also don't need to write intermediate uncompressed file that zip needs)
  python extract_multihits_from_dependencies_csv.py static/gendep/all_dependencies_$DATE.csv.xz static/gendep/multihit_dependencies_$DATE.csv || exit 9
  xz static/gendep/multihit_dependencies_$DATE.csv || exit 10
fi

echo -e "Finished.\n"

echo -e "\nNow restart the Web app - by going to the PythonAnywhere 'Web' tab, selecting 'cangerGD.org' in left margin, then click the 'Reload www.cancergd.org' button.\n"
