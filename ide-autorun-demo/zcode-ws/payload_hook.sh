#!/bin/sh
# BENIGN DEMO PAYLOAD (defensive research)
# ZCode workspace SessionStart hook — runs at agent session start.
echo "[ZCODE-HOOK] $(date '+%F %T') user=$(whoami) pid=$$" >> TRIGGER_LOG.txt
