@echo off
rem === 在 DSH 沙箱 runner 下直接运行探针（确定性，不依赖 LLM）===
rem 用法: run-under-sandbox.cmd <probe_ladder|probe_delegation> <DSH安装目录>
rem 示例: run-under-sandbox.cmd probe_delegation D:\dsh-install
setlocal
set PROBE=%1
set DSHDIR=%2
if "%PROBE%"=="" set PROBE=probe_ladder
if "%DSHDIR%"=="" set DSHDIR=%~dp0..\dsh-install
set RUNNER=%DSHDIR%\node_modules\@deepseek-ai\dsh-sandbox-windows-acl\lib\runner.js
cd /d "%~dp0probes"
del TRIGGER_LOG.txt 2>nul
echo [sandbox-probe] running %PROBE%.py under workspace-write sandbox...
node "%RUNNER%" --workspace "%~dp0probes" --temp "%TEMP%\dsh-probe-tmp" --mode workspace-write -- python %PROBE%.py
echo.
echo === TRIGGER_LOG ===
type TRIGGER_LOG.txt 2>nul
endlocal
