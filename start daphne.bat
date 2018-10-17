@echo off
daphne -p 8001 py_test_site.asgi:application
pause