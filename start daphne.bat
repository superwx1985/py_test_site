@echo off
::daphne -p 8001 py_test_site.asgi:application
python other\vic_daphne_server.py -p 8001 py_test_site.asgi:application
pause