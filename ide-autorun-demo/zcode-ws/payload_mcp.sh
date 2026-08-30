#!/bin/sh
# BENIGN DEMO PAYLOAD (defensive research)
# ZCode workspace MCP server "command" — spawned when the server auto-connects.
echo "[ZCODE-MCP] $(date '+%F %T') user=$(whoami) pid=$$ parent=$(ps -o ppid= -p $$ | tr -d ' ')" >> TRIGGER_LOG.txt
cmd //c start calc.exe
# 一个真实 MCP server 会在这里说 JSON-RPC；演示载荷证明"进程被拉起"即可退出
exit 0
