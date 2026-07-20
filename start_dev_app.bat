@echo off
setlocal
cd /d "%~dp0"
set FINANCIAL_GPS_TEST_LOGIN=1
echo Starting Financial GPS with beta test login enabled...
echo.
if exist ".venv\Scripts\streamlit.exe" (
    ".venv\Scripts\streamlit.exe" run app.py --server.headless=false --server.showEmailPrompt=false --browser.gatherUsageStats=false
) else (
    streamlit run app.py --server.headless=false --server.showEmailPrompt=false --browser.gatherUsageStats=false
)
echo.
echo Streamlit stopped. Press any key to close this window.
pause >nul
