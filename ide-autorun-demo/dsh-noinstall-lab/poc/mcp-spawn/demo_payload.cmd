@echo off
rem === BENIGN DEMO PAYLOAD (defensive research only) ===
rem DSH "no-install execution" 实验二的载荷：写日志 + 弹计算器。
rem 真实攻击中这里放的是窃密器/持久化；本脚本不含任何恶意功能。
echo [DSH NO-INSTALL MCP DEMO] %date% %time% >> "%~dp0INTRUSION_LOG.txt"
whoami >> "%~dp0INTRUSION_LOG.txt"
start calc.exe
