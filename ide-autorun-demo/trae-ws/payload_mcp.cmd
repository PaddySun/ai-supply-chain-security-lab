@echo off
rem BENIGN DEMO PAYLOAD (defensive research)
echo [TRAE-MCP] %date% %time% user=%USERNAME% >> "%~dp0TRIGGER_LOG.txt"
start calc.exe
