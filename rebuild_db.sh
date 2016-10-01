#!/bin/bash

# if db exists try to delete it. In winndows can't just use '|| exit' as 'del' returns errorlevel of 0 even if can't delete the file, so just test again if still exists
if [ -e "db.sqlite3" ]; then
  rm db.sqlite3;
  if [ -e "db.sqlite3" ]; then exit; fi
fi

rm -r gendep/migrations/*
python manage.py migrate || exit
python manage.py makemigrations gendep || exit
python manage.py sqlmigrate gendep 0001 || exit
python manage.py migrate || exit
#python ./load_data.py
python ./populate_db.py

python manage.py createcachetable
# To just see the SQL use:  python createcachetable --dry-run
