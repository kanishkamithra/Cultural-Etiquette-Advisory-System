@echo off
setlocal

cd /d "%~dp0backend"

set MYSQL_HOST=127.0.0.1
set MYSQL_PORT=3306
set MYSQL_USER=root
set MYSQL_PASSWORD=1234
set MYSQL_DATABASE=ceas

set CEAS_PORT=8001

echo Starting CEAS on http://127.0.0.1:%CEAS_PORT%
echo.
python -m uvicorn main:app --host 127.0.0.1 --port %CEAS_PORT%

echo.
echo CEAS server stopped.
pause
