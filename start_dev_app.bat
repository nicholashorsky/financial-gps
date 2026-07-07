@echo off
setlocal
cd /d "%~dp0"
set FINANCIAL_GPS_TEST_LOGIN=1
echo Starting Financial GPS with beta test login enabled...
echo.
streamlit run app.py
echo.
echo Streamlit stopped. Press any key to close this window.
pause >nul
