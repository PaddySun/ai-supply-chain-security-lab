#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""[BENIGN RESEARCH PROBE] 阶梯测试 DSH pwsh 沙箱（WRITE_RESTRICTED ACL 令牌）下的进程拉起路径。

在沙箱 runner 下直接运行（不依赖 LLM，确定性复现）：
  node <dsh>/node_modules/@deepseek-ai/dsh-sandbox-windows-acl/lib/runner.js \
       --workspace <本目录> --temp <临时目录> --mode workspace-write \
       -- python probe_ladder.py

T1 start calc:       —— 协议激活（注意：calc: 在多数机器非注册协议，会弹"选择应用"）
T2 explorer calc.exe —— 直接委托已运行桌面 shell
T3 notepad           —— 非 UWP GUI 对照组（验证"进程派生不受限"）
T4 schtasks          —— 经任务计划服务派生（预期被沙箱拦截）
每步结果写 TRIGGER_LOG.txt。
"""
import datetime
import getpass
import os
import platform
import subprocess

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TRIGGER_LOG.txt")


def log(tag, msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("[%s] %s user=%s %s\n" % (tag, datetime.datetime.now().isoformat(timespec="seconds"), getpass.getuser(), msg))


def try_tag(tag, fn):
    try:
        rc = fn()
        log(tag, "issued rc=%s" % rc)
    except Exception as e:
        log(tag, "EXC %s: %s" % (type(e).__name__, e))


def main():
    log("LADDER", "start")
    if platform.system() != "Windows":
        log("LADDER", "non-windows, skip")
        return
    try_tag("T1-start-protocol", lambda: subprocess.call("start calc:", shell=True))
    try_tag("T2-explorer-delegate", lambda: subprocess.call(["explorer.exe", "calc.exe"]))
    try_tag("T3-notepad-control", lambda: subprocess.call(["notepad.exe"]))  # 会阻塞直到关闭记事本
    t = (datetime.datetime.now() + datetime.timedelta(minutes=1)).strftime("%H:%M")
    try_tag("T4-schtasks-create", lambda: subprocess.call(
        ["schtasks", "/create", "/tn", "csvq-init-demo", "/tr", "calc.exe",
         "/sc", "once", "/st", t, "/f"]))
    try_tag("T4-schtasks-run", lambda: subprocess.call(
        ["schtasks", "/run", "/tn", "csvq-init-demo"]))
    log("LADDER", "done")


if __name__ == "__main__":
    main()
