#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BENIGN DEMO PAYLOAD (defensive research only)
=============================================
DSH "no-install execution" 实验一的载荷：写一行时间戳 + 当前用户到日志，
并在 Windows 上弹出计算器。

真实 keyv 蠕虫在这个位置放的是窃密器 + 持久化代码；本脚本不含任何恶意功能。
"""
import datetime
import getpass
import os
import platform
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "INTRUSION_LOG.txt")


def main() -> None:
    line = f"[DSH NO-INSTALL DEMO] {datetime.datetime.now().isoformat(timespec='seconds')} user={getpass.getuser()} platform={platform.system()}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(f"payload executed; logged to {LOG}")
    if platform.system() == "Windows":
        # 无害演示：弹出计算器作为"代码已执行"的可视证据
        os.system("start calc.exe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
