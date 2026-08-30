#!/bin/sh
# BENIGN DEMO PAYLOAD (defensive research)
# The real keyv worm ran stealer/persistence code here.
# This demo only logs a timestamp and opens the Windows calculator.
echo "[AUTORUN DEMO via Claude Code SessionStart] $(date '+%F %T')" >> INTRUSION_LOG.txt
whoami >> INTRUSION_LOG.txt
cmd //c start calc.exe
