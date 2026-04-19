@echo off
echo Installing required Python packages...
pip install flask flask-cors fpdf

echo.
echo Starting Nexus Backend API Server...
python app.py
pause
