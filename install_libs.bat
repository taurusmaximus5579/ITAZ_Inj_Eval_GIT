@echo off
echo Installiere Python-Bibliotheken...

REM Absoluter Pfad zu Python verwenden
"C:\Users\larsk\anaconda3\envs\Python_Lars\python.exe" -m pip install --upgrade pip
"C:\Users\larsk\anaconda3\envs\Python_Lars\python.exe" -m pip install pandas numpy matplotlib scipy plotly

echo Installation abgeschlossen!
pause
