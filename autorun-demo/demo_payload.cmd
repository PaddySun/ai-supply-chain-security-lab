@echo off
rem === BENIGN DEMO PAYLOAD (defensive research) ===
rem In the real keyv worm this slot held stealing/persistence code.
rem This demo only logs a timestamp and opens the Windows calculator.
echo [AUTORUN DEMO] triggered at %date% %time% >> "%~dp0INTRUSION_LOG.txt"
whoami >> "%~dp0INTRUSION_LOG.txt"
start calc.exe
