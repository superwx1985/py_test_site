@echo off
python -Xutf8 manage.py dumpdata -o db_data.json
pause